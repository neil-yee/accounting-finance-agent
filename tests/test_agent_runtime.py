"""Exercise real agent middleware and CLI orchestration with fake model responses."""

from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest
from uuid import uuid4

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage

from accounting_finance_agent import __main__ as cli, knowledge, workspace, worklog
from accounting_finance_agent.agent import build_agent
from accounting_finance_agent.config import Settings
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.runtime import RunContext, RunControls, RunLimitExceeded
from accounting_finance_agent.sandbox import BoundedSandbox
from accounting_finance_agent.worklog import WorkLog


class OfflineToolModel(FakeMessagesListChatModel):
    calls: int = 0
    seen_messages: list = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, *args, **kwargs):
        self.calls += 1
        self.seen_messages.append(list(messages))
        return super()._generate(messages, *args, **kwargs)


class AgentGraphChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(knowledge, "MEMORY_ROOT", self.root / "memory"))
        self.enterContext(patch.object(knowledge, "SKILLS_ROOT", self.root / "skills"))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.settings = Settings("gpt-6-luna", "high", False, "offline-checks")

    def graph(self, responses, *, limit=40):
        from dataclasses import replace
        model = OfflineToolModel(responses=responses)
        controls = RunControls(replace(self.settings, max_model_calls=limit),
                               RunContext("offline-run", "offline-thread", "America/Toronto", "virtual"), Mock())
        with patch("accounting_finance_agent.agent.init_chat_model", return_value=model):
            graph = build_agent(self.settings, controls=controls)
        return graph, model, controls

    def test_parent_and_builtin_subagent_share_real_middleware_budget(self):
        delegate = AIMessage(content="", tool_calls=[{"name": "task", "args": {
            "description": "Return a short report; no file changes are needed.", "subagent_type": "general-purpose"}, "id": "delegate-1"}])
        graph, model, controls = self.graph([delegate, AIMessage(content="Subagent report"), AIMessage(content="Final answer")])
        output = graph.invoke({"messages": [{"role": "user", "content": "Delegate this check."}]})
        self.assertEqual(output["messages"][-1].text, "Final answer")
        self.assertEqual(model.calls, 3)
        self.assertEqual(controls.counts, {"model": 3, "tool": 1})

    def test_shared_budget_blocks_subagent_before_fake_provider_call(self):
        delegate = AIMessage(content="", tool_calls=[{"name": "task", "args": {
            "description": "Return a report.", "subagent_type": "general-purpose"}, "id": "delegate-2"}])
        graph, model, controls = self.graph([delegate, AIMessage(content="Should never be generated")], limit=1)
        with self.assertRaises(RunLimitExceeded):
            graph.invoke({"messages": [{"role": "user", "content": "Delegate."}]})
        self.assertEqual(model.calls, 1)

    def test_context_and_memory_are_loaded_without_real_files_or_network(self):
        knowledge.MEMORY_ROOT.mkdir()
        (knowledge.MEMORY_ROOT / "AGENTS.md").write_text("Fixture guidance: preserve source evidence.")
        skill = knowledge.SKILLS_ROOT / "fixture-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: fixture-skill\ndescription: Read fixture guidance for an offline check.\n---\n# Fixture\nUse source evidence.")
        graph, model, controls = self.graph([AIMessage(content="Done")])
        output = graph.invoke({"messages": [{"role": "user", "content": "Hello"}]})
        self.assertEqual(output["messages"][-1].text, "Done")
        self.assertEqual(controls.counts["model"], 1)
        # These fields are private/omitted from graph output in this version.
        # Verify what reaches the model instead of assuming public state fields.
        system = model.seen_messages[0][0].text
        self.assertIn("Fixture guidance", system)
        self.assertIn("fixture-skill", system)
        self.assertIn("America/Toronto", system)

    def test_execute_timeout_is_capped_before_real_tool_validation(self):
        remote = Mock(name="offline-sandbox")
        remote.run.return_value = SimpleNamespace(stdout="4\n", stderr="", exit_code=0)
        backend = BoundedSandbox(sandbox=remote, command_timeout=120)
        backend.enable_capture_offload = False
        call = AIMessage(content="", tool_calls=[{"name": "execute", "args": {
            "command": "python3 -c 'print(2 + 2)'", "timeout": 120000}, "id": "execute-large-timeout"}])
        model = OfflineToolModel(responses=[call, AIMessage(content="Done")])
        controls = RunControls(self.settings,
                               RunContext("offline-run", "offline-thread", "America/Toronto", "virtual"), Mock())
        with patch("accounting_finance_agent.agent.init_chat_model", return_value=model):
            graph = build_agent(self.settings, backend=backend, controls=controls)
        output = graph.invoke({"messages": [{"role": "user", "content": "Execute a small check."}]})
        remote.run.assert_called_once_with("python3 -c 'print(2 + 2)'", timeout=120)
        tool_result = next(message for message in output["messages"] if isinstance(message, ToolMessage))
        self.assertEqual(tool_result.status, "success")
        self.assertIn("4", tool_result.text)
        self.assertEqual(call.tool_calls[0]["args"]["timeout"], 120000)
        self.assertEqual(controls.counts, {"model": 2, "tool": 1})
        controls.log.event.assert_any_call("offline-run", "tool_timeout_capped",
                                          call_id="execute-large-timeout", requested_seconds=120000,
                                          effective_seconds=120)

    def test_checkpoint_restores_conversation_after_reopening_database(self):
        db = self.root / "checkpoints.sqlite"
        with open_history(mode="virtual", database=db) as history:
            thread = history.new()
            first = OfflineToolModel(responses=[AIMessage(content="First answer")])
            with patch("accounting_finance_agent.agent.init_chat_model", return_value=first):
                graph = build_agent(self.settings, checkpointer=history.checkpointer)
            graph.invoke({"messages": [{"role": "user", "content": "Remember MAPLE-42"}]},
                         config={"configurable": {"thread_id": thread.id}})
        with open_history(mode="virtual", database=db) as history:
            second = OfflineToolModel(responses=[AIMessage(content="Second answer")])
            with patch("accounting_finance_agent.agent.init_chat_model", return_value=second):
                graph = build_agent(self.settings, checkpointer=history.checkpointer)
            output = graph.invoke({"messages": [{"role": "user", "content": "Continue"}]},
                                  config={"configurable": {"thread_id": thread.id}})
            self.assertEqual(len(output["messages"]), 4)
            self.assertIn("Remember MAPLE-42", [message.text for message in second.seen_messages[0]])
            other = history.new()
            isolated = graph.invoke({"messages": [{"role": "user", "content": "Unrelated task"}]},
                                    config={"configurable": {"thread_id": other.id}})
            self.assertEqual(len(isolated["messages"]), 2)


class RunnerChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(workspace, "LOCAL_WORKSPACE", self.root / "workspace"))
        self.enterContext(patch.object(worklog, "PROJECT_ROOT", self.root))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.settings = Settings("gpt-6-luna", "high", False, "offline-checks")
        self.log = WorkLog(self.root / "worklog.sqlite")
        self.addCleanup(self.log.close)

    def test_runner_preserves_files_logs_outcome_and_passes_snapshot_policy(self):
        from dataclasses import replace
        thread = str(uuid4())
        @contextmanager
        def sandbox_scope(**kwargs):
            self.assertEqual(kwargs["snapshot_id"], "fixed-release")
            self.assertEqual(kwargs["command_timeout"], 120)
            self.assertIn("pypi.org:443", kwargs["allowed_hosts"])
            yield Mock()
        def events(*args, **kwargs):
            self.assertEqual(kwargs["context"].thread_id, thread)
            (workspace.workspace_root() / "result.json").write_text('{"total":"14.24"}')
            yield "values", {"messages": [AIMessage(content="Output created")]}
        fake_agent = Mock()
        fake_agent.stream.side_effect = events
        with patch.object(cli, "sandbox_backend", side_effect=sandbox_scope), patch.object(cli, "build_agent", return_value=fake_agent):
            cli.run_prompt(replace(self.settings, sandbox_snapshot_id="fixed-release"), Mock(), self.log,
                           thread, "Make a result", sandbox=True)
        row = self.log.runs(thread)[0]
        self.assertEqual(row["status"], "needs_review")
        with workspace.use_workspace(workspace.thread_workspace(thread)):
            manifest = workspace.workspace_manifest()
        self.assertIn("result.json", manifest)
        self.log.review(row["id"], thread, "approved", manifest, "offline-reviewer")

    def test_failure_records_outcome_and_does_not_replay_model_work(self):
        thread = str(uuid4())
        fake_agent = Mock()
        fake_agent.stream.side_effect = RuntimeError("simulated failure")
        with patch.object(cli, "build_agent", return_value=fake_agent):
            with self.assertRaisesRegex(RuntimeError, "simulated failure"):
                cli.run_prompt(self.settings, Mock(), self.log, thread, "Task", sandbox=False)
        self.assertEqual(fake_agent.stream.call_count, 1)
        self.assertEqual(self.log.runs(thread)[0]["status"], "failed")
        with worklog.thread_lease(thread):
            pass

    def test_structurally_bad_output_blocks_successful_review(self):
        thread = str(uuid4())
        def events(*args, **kwargs):
            (workspace.workspace_root() / "broken.json").write_text("{broken}")
            yield "values", {"messages": [AIMessage(content="Done")]}
        fake_agent = Mock()
        fake_agent.stream.side_effect = events
        @contextmanager
        def sandbox_scope(**kwargs):
            yield Mock()
        with patch.object(cli, "sandbox_backend", side_effect=sandbox_scope), patch.object(cli, "build_agent", return_value=fake_agent):
            with self.assertRaisesRegex(ValueError, "structural checks"):
                cli.run_prompt(self.settings, Mock(), self.log, thread, "Task", sandbox=True)
        self.assertEqual(self.log.runs(thread)[0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
