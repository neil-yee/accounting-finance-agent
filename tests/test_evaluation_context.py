"""Deterministic offline checks for context, skills, todos, and harness settings.

These exercise the pinned framework wiring with fake responses. They do not
evaluate model quality or prove that a live model preserves meaning through
repeated compaction.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import os
from unittest.mock import Mock, patch
import unittest

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from accounting_finance_agent import knowledge
from accounting_finance_agent.agent import build_agent
from accounting_finance_agent.config import EXCEL_PROFILE, Settings, load_settings
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.runtime import RunContext, RunControls


class CapturingFakeModel(FakeMessagesListChatModel):
    calls: int = 0
    seen_messages: list = []
    bound_tool_names: list = []

    def bind_tools(self, tools, **kwargs):
        self.bound_tool_names.extend(
            tool.get("name") if isinstance(tool, dict) else getattr(tool, "name", None)
            for tool in tools
        )
        return self

    def _generate(self, messages, *args, **kwargs):
        self.calls += 1
        self.seen_messages.append(list(messages))
        return super()._generate(messages, *args, **kwargs)


class FailingSummarizerModel(CapturingFakeModel):
    def _generate(self, messages, *args, **kwargs):
        self.calls += 1
        self.seen_messages.append(list(messages))
        raise RuntimeError("fixture summarizer failure")


class OpenAIProfileFakeModel(CapturingFakeModel):
    model_name: str = "gpt-6-luna"

    def _get_ls_params(self, stop=None, **kwargs):
        return {"ls_provider": "openai", "ls_model_name": self.model_name}


class EvaluationContextChecks(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.memory = self.root / "memory"
        self.skills = self.root / "skills"
        self.enterContext(patch.object(knowledge, "MEMORY_ROOT", self.memory))
        self.enterContext(patch.object(knowledge, "SKILLS_ROOT", self.skills))
        self.settings = Settings("gpt-6-luna", "high", False, "offline-context-checks")

    def make_graph(self, model, controls=None, checkpointer=None):
        controls = controls or RunControls(
            self.settings,
            RunContext("context-run", "context-thread", "UTC", "virtual"),
            Mock(),
        )
        with patch("accounting_finance_agent.agent.init_chat_model", return_value=model):
            graph = build_agent(self.settings, controls=controls, checkpointer=checkpointer)
        return graph, controls

    def test_skill_index_and_file_route_are_supplied_to_model(self):
        skill = self.skills / "fixture-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: fixture-skill\ndescription: Fixture guidance.\n---\n"
            "# Fixture skill\nUse revised source evidence."
        )
        model = CapturingFakeModel(responses=[
            AIMessage(content="", tool_calls=[{
                "name": "read_file",
                "args": {"file_path": "/skills/fixture-skill/SKILL.md"},
                "id": "read-skill",
            }]),
            AIMessage(content="Used the fixture skill."),
        ])
        graph, _ = self.make_graph(model)

        result = graph.invoke({"messages": [HumanMessage(content="Use the fixture skill.")]})

        self.assertEqual(result["messages"][-1].text, "Used the fixture skill.")
        self.assertIn("fixture-skill", model.seen_messages[0][0].text)
        skill_result = next(m for m in model.seen_messages[1] if isinstance(m, ToolMessage))
        self.assertIn("Use revised source evidence.", skill_result.text)

    def test_todo_tool_updates_framework_state_and_is_visible_to_next_turn(self):
        model = CapturingFakeModel(responses=[
            AIMessage(content="", tool_calls=[{
                "name": "write_todos",
                "args": {"todos": [
                    {"content": "Inspect source", "status": "in_progress"},
                    {"content": "Check result", "status": "pending"},
                ]},
                "id": "todo-write",
            }]),
            AIMessage(content="The plan is recorded."),
        ])
        graph, _ = self.make_graph(model)

        result = graph.invoke({"messages": [HumanMessage(content="Inspect source and check result.")]})

        self.assertEqual(result["todos"], [
            {"content": "Inspect source", "status": "in_progress"},
            {"content": "Check result", "status": "pending"},
        ])
        self.assertIn("write_todos", model.seen_messages[0][0].text)
        self.assertTrue(any(isinstance(m, ToolMessage) for m in model.seen_messages[1]))

    def test_thread_checkpoint_keeps_exact_user_correction_and_isolates_other_thread(self):
        database = self.root / "history.sqlite"
        correction = "Correction: use revision B; revision A is obsolete."
        with open_history(mode="virtual", database=database) as history:
            thread = history.new()
            first = CapturingFakeModel(responses=[AIMessage(content="Acknowledged.")])
            graph, _ = self.make_graph(first, checkpointer=history.checkpointer)
            graph.invoke(
                {"messages": [HumanMessage(content=correction)]},
                config={"configurable": {"thread_id": thread.id}},
            )

        with open_history(mode="virtual", database=database) as history:
            followup_model = CapturingFakeModel(responses=[AIMessage(content="Revision B applies.")])
            graph, _ = self.make_graph(followup_model, checkpointer=history.checkpointer)
            result = graph.invoke(
                {"messages": [HumanMessage(content="Which revision applies?")]},
                config={"configurable": {"thread_id": thread.id}},
            )
            self.assertIn(correction, [m.text for m in followup_model.seen_messages[0]])

            other_thread = history.new()
            isolated_model = CapturingFakeModel(responses=[AIMessage(content="No prior correction.")])
            isolated_graph, _ = self.make_graph(isolated_model, checkpointer=history.checkpointer)
            isolated_graph.invoke(
                {"messages": [HumanMessage(content="Which revision applies?")]},
                config={"configurable": {"thread_id": other_thread.id}},
            )
            self.assertNotIn(correction, [m.text for m in isolated_model.seen_messages[0]])

        self.assertEqual(result["messages"][-1].text, "Revision B applies.")

    def test_harness_records_pinned_compaction_configuration(self):
        model = CapturingFakeModel(responses=[AIMessage(content="Done")])
        controls = RunControls(
            self.settings,
            RunContext("context-run", "context-thread", "UTC", "virtual"),
            Mock(),
        )
        self.make_graph(model, controls=controls)

        configuration_events = [
            call.kwargs for call in controls.log.event.call_args_list
            if len(call.args) >= 2 and call.args[1] == "harness_configuration"
        ]
        self.assertEqual(len(configuration_events), 1)
        compaction = configuration_events[0]["compaction"]
        self.assertEqual(
            compaction["implementation"],
            "deepagents.middleware.summarization.create_summarization_middleware",
        )
        self.assertEqual(compaction["defaults"]["trigger"], ("tokens", 170000))
        self.assertEqual(compaction["defaults"]["keep"], ("messages", 6))
        self.assertEqual(len(compaction["summary_prompt_sha256"]), 64)
        self.assertEqual(compaction["summarizer_model"], self.settings.model)
        self.assertFalse(compaction["custom_summary_prompt"])
        self.assertEqual(compaction["usage_accounting"], "logical calls only")

    def test_v3_profile_ignores_environment_overrides_without_credentials(self):
        attempted = {
            "OPENAI_MODEL": "gpt-6-other",
            "OPENAI_REASONING_EFFORT": "low",
            "LANGSMITH_TRACING": "false",
            "AGENT_MAX_MODEL_CALLS": "7",
            "AGENT_RUN_SECONDS": "12",
            "SANDBOX_ALLOWED_HOSTS": "unexpected.example:443",
        }
        with patch("accounting_finance_agent.config.load_dotenv") as dotenv, patch.dict(
            os.environ, attempted, clear=True
        ):
            self.assertNotIn("OPENAI_API_KEY", os.environ)
            settings = load_settings(profile=EXCEL_PROFILE, validate_credentials=False)

        dotenv.assert_called_once()
        self.assertEqual(settings.profile, "excel-benchmark-v3")
        self.assertEqual(settings.model, "gpt-6-luna")
        self.assertEqual(settings.reasoning_effort, "high")
        self.assertTrue(settings.tracing_enabled)
        self.assertEqual(settings.max_model_calls, 40)
        self.assertEqual(settings.max_tool_calls, 40)
        self.assertEqual(settings.run_seconds, 1800)
        self.assertFalse(settings.delegation_enabled)
        self.assertEqual(settings.sandbox_allowed_hosts, ())

    def test_v3_graph_does_not_expose_delegation_tool(self):
        model = OpenAIProfileFakeModel(responses=[AIMessage(content="No delegation used.")])
        with patch("accounting_finance_agent.config.load_dotenv"), patch.dict(
            os.environ, {}, clear=True
        ):
            settings = load_settings(profile=EXCEL_PROFILE, validate_credentials=False)
        controls = RunControls(
            settings,
            RunContext("benchmark-run", "benchmark-thread", settings.timezone, "virtual"),
            Mock(),
        )
        with patch("accounting_finance_agent.agent.init_chat_model", return_value=model):
            graph = build_agent(settings, controls=controls, checkpointer=InMemorySaver())

        try:
            result = graph.invoke(
                {"messages": [HumanMessage(content="Answer without delegation.")]},
                config={"configurable": {"thread_id": "benchmark-thread"}},
            )
        finally:
            controls.api_client.close()

        self.assertEqual(result["messages"][-1].text, "No delegation used.")
        self.assertTrue(model.bound_tool_names)
        self.assertNotIn("task", model.bound_tool_names)
        self.assertFalse(settings.delegation_enabled)

    def long_history(self):
        messages = []
        for index in range(80):
            messages.extend([
                HumanMessage(content=f"Old context item {index}: " + "x " * 40),
                AIMessage(content=f"Old assistant response {index}: " + "y " * 40),
            ])
        return messages

    @staticmethod
    def rendered(messages):
        return "\n".join(getattr(message, "text", "") for message in messages)

    def test_real_pinned_middleware_runs_two_fake_summary_cycles(self):
        model = CapturingFakeModel(responses=[
            AIMessage(content="FAKE_SUMMARY_1: Correction retained: REV-B replaces REV-A."),
            AIMessage(content="First turn complete."),
            AIMessage(content="FAKE_SUMMARY_2: Correction retained: REV-B replaces REV-A; CASE-92 remains active."),
            AIMessage(content="Second turn complete."),
        ])
        model.profile = {"max_input_tokens": 8000}
        graph, _ = self.make_graph(model, checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "repeated-compaction-thread"}}

        first = graph.invoke(
            {"messages": self.long_history() + [
                HumanMessage(content="Correction: source REV-B replaces REV-A.")
            ]},
            config=config,
        )
        second = graph.invoke(
            {"messages": self.long_history() + [
                HumanMessage(content="Carry forward identifier CASE-92.")
            ]},
            config=config,
        )

        self.assertEqual(first["messages"][-1].text, "First turn complete.")
        self.assertEqual(second["messages"][-1].text, "Second turn complete.")
        self.assertEqual(model.calls, 4)
        first_post_summary_view = self.rendered(model.seen_messages[1])
        second_post_summary_view = self.rendered(model.seen_messages[3])
        self.assertIn("FAKE_SUMMARY_1", first_post_summary_view)
        self.assertIn("REV-B replaces REV-A", first_post_summary_view)
        self.assertIn("FAKE_SUMMARY_2", second_post_summary_view)
        self.assertIn("REV-B replaces REV-A", second_post_summary_view)
        self.assertIn("CASE-92", second_post_summary_view)

    def test_summarizer_failure_propagates_and_does_not_call_user_turn(self):
        model = FailingSummarizerModel(responses=[AIMessage(content="unused")])
        model.profile = {"max_input_tokens": 8000}
        graph, _ = self.make_graph(model)

        with self.assertRaisesRegex(RuntimeError, "fixture summarizer failure"):
            graph.invoke({"messages": self.long_history() + [
                HumanMessage(content="Correction: source REV-B replaces REV-A.")
            ]})

        # The pinned framework retries a failed summary generation twice;
        # it then propagates the error without reaching the ordinary user turn.
        self.assertEqual(model.calls, 3)


if __name__ == "__main__":
    unittest.main()
