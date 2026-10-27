"""Integrated offline recovery gates for runner, compiled graph, and HTTP retries.

Tool and final model outcomes use scripted chat responses; the summary-retry
case sends synthetic 503 responses through BudgetClient and MockTransport.
No credentials or live provider calls are used. Files land in temp workspaces.
"""

from contextlib import contextmanager, redirect_stdout
from dataclasses import replace
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import unittest

import httpx
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import HumanMessage

from accounting_finance_agent import __main__ as cli, knowledge, worklog, workspace
from accounting_finance_agent.agent import build_agent as real_build_agent
from accounting_finance_agent.config import EXCEL_PROFILE, Settings
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.runtime import RunContext, RunControls
from accounting_finance_agent.worklog import WorkLog
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage


class OfflineCompiledModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class RecoveryIntegrationChecks(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.enterContext(patch.object(workspace, "LOCAL_WORKSPACE", self.root / "workspace"))
        self.enterContext(patch.object(worklog, "PROJECT_ROOT", self.root))
        self.enterContext(patch.dict(os.environ, {
            "OPENAI_API_KEY": "offline-fake-key",
            "OPENAI_BASE_URL": "http://127.0.0.1:9/v1",
        }))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.settings = replace(Settings("gpt-6-luna", "high", False, "recovery-offline"),
                                profile=EXCEL_PROFILE, max_model_calls=40, max_tool_calls=40,
                                run_seconds=1800, sdk_max_retries=0, delegation_enabled=False)
        self.log = WorkLog(self.root / "worklog.sqlite")
        self.addCleanup(self.log.close)
        self.db = self.root / "checkpoints.sqlite"

    def patch_agent_model(self, model):
        """Replace only provider generation; keep the real compiled graph/tools."""
        from accounting_finance_agent import agent
        return patch.object(agent, "init_chat_model", return_value=model)

    def runner_sandbox(self, thread_id, backend):
        @contextmanager
        def scope(**kwargs):
            yield backend
        return patch.object(cli, "sandbox_backend", side_effect=scope)

    def runner_builder(self):
        def build(settings, *, backend=None, checkpointer=None, controls=None):
            return real_build_agent(settings, backend=backend, checkpointer=checkpointer, controls=controls)
        return patch.object(cli, "build_agent", side_effect=build)

    def test_lost_tool_response_preserves_file_and_restart_does_not_repeat_write(self):
        """A write that took effect before its response was lost must be reconciled."""
        effects = []

        class WriteAppliedThenLost(FilesystemBackend):
            def write(self, file_path, content):
                result = super().write(file_path, content)
                effects.append((file_path, content))
                if len(effects) == 1:
                    raise TimeoutError("simulated lost write response after durable effect")
                return result

        model = OfflineCompiledModel(responses=[AIMessage(content="", tool_calls=[{
            "name": "write_file", "args": {"file_path": "recovered.txt", "content": "posted once"},
            "id": "write-call-1",
        }])])

        with open_history(mode="sandbox", database=self.db) as history:
            thread_id = history.new().id
            folder = workspace.thread_workspace(thread_id)
            backend = WriteAppliedThenLost(root_dir=folder)
            with self.patch_agent_model(model), self.runner_builder(), self.runner_sandbox(thread_id, backend):
                with self.assertRaises(TimeoutError):
                    cli.run_prompt(self.settings, history, self.log, thread_id,
                                   "Write recovered.txt with posted once.", sandbox=True)

            self.assertEqual((folder / "recovered.txt").read_text(), "posted once")
            self.assertEqual(len(effects), 1)
            self.assertEqual(self.log.runs(thread_id)[0]["status"], "failed")
            run_id = self.log.runs(thread_id)[0]["id"]
            with self.log.lock:
                outputs = self.log.conn.execute(
                    "SELECT outputs FROM runs WHERE id=?", (run_id,)
                ).fetchone()["outputs"]
            self.assertIn("recovered.txt", json.loads(outputs))


        # Reopen SQLite as a separate runner process would, then inspect and
        # reconcile the preserved effect with an explicit continuation.
        with open_history(mode="sandbox", database=self.db) as history:
            controls = RunControls(self.settings, RunContext("recovery-resume", thread_id,
                                    self.settings.timezone, str(folder)), self.log)
            with self.patch_agent_model(OfflineCompiledModel(responses=[AIMessage(content="Reconciled.")])):
                graph = real_build_agent(self.settings, backend=backend,
                                         checkpointer=history.checkpointer, controls=controls)
                self.addCleanup(controls.api_client.close)
                resumed = graph.invoke({"messages": [{"role": "user", "content":
                    "Inspect the existing file and reconcile; do not repeat completed writes."}]},
                    config={"configurable": {"thread_id": thread_id}})
            self.assertEqual(resumed["messages"][-1].text, "Reconciled.")

        self.assertEqual((folder / "recovered.txt").read_text(), "posted once")
        self.assertEqual(len(effects), 1, "uncertain write was replayed after restart")
        self.assertEqual(self.log.runs(thread_id)[0]["status"], "failed")

    def test_incomplete_provider_output_is_an_honest_runner_failure(self):
        with open_history(mode="sandbox", database=self.db) as history:
            for response_status, details in (
                ("incomplete", {"reason": "max_output_tokens"}),
                ("failed", {}),
                ("cancelled", {}),
                ("queued", {}),
                ("in_progress", {}),
            ):
                with self.subTest(response_status=response_status):
                    thread = history.new().id
                    folder = workspace.thread_workspace(thread)
                    backend = FilesystemBackend(root_dir=folder)
                    model = OfflineCompiledModel(responses=[
                        AIMessage(content="", tool_calls=[{
                            "name": "write_file",
                            "args": {"file_path": "partial.txt", "content": "preserved before incomplete response"},
                            "id": "partial-write-" + response_status,
                        }]),
                        AIMessage(content="Partial draft that must not be accepted.", response_metadata={
                            "status": response_status, "incomplete_details": details,
                        }),
                    ])
                    with self.patch_agent_model(model), self.runner_builder(), self.runner_sandbox(thread, backend):
                        with self.assertRaisesRegex(RuntimeError, f"status was {response_status}"):
                            cli.run_prompt(self.settings, history, self.log, thread,
                                           "Prepare the requested result.", sandbox=True)
                    self.assertEqual((folder / "partial.txt").read_text(),
                                     "preserved before incomplete response")
                    row = self.log.runs(thread)[0]
                    self.assertEqual(row["status"], "failed")
                    with self.log.lock:
                        outputs = self.log.conn.execute(
                            "SELECT outputs FROM runs WHERE id=?", (row["id"],)
                        ).fetchone()["outputs"]
                        events = self.log.conn.execute(
                            "SELECT kind, details FROM events WHERE run_id=?", (row["id"],)
                        ).fetchall()
                    self.assertIn("partial.txt", json.loads(outputs))
                    self.assertTrue(any(item["kind"] == "recovery_boundary" for item in events))
                    status_events = [json.loads(item["details"]) for item in events
                                     if item["kind"] == "incomplete_model_response"]
                    self.assertEqual(status_events[0]["status"], response_status)
                    if response_status == "incomplete":
                        self.assertEqual(status_events[0]["reason"], "max_output_tokens")

    def test_summary_framework_and_http_retries_share_five_retry_ceiling(self):
        """An integrated summary failure may have at most initial + five retries."""
        from accounting_finance_agent.budget import BudgetClient
        hits = []

        class HttpFailingSummaryModel(OfflineCompiledModel):
            client: object | None = None
            calls: int = 0

            def _generate(self, messages, *args, **kwargs):
                self.calls += 1
                result = self.client.post("https://api.openai.com/v1/responses", json={
                    "model": "gpt-6-luna", "input": "synthetic summary failure", "max_output_tokens": 30,
                })
                result.raise_for_status()
                raise AssertionError("unavailable response should fail")

        def unavailable(request):
            hits.append(request)
            return httpx.Response(503, json={"error": {"message": "temporary unavailable"}}, request=request)

        settings = replace(self.settings, max_model_calls=40)
        controls = RunControls(settings, RunContext("retry-run", "retry-thread", "UTC", "virtual"), self.log)
        controls.log = Mock()
        history = []
        for index in range(80):
            history.extend([HumanMessage(content=f"Earlier fact {index}: " + "x " * 800),
                            HumanMessage(content=f"Earlier response {index}: " + "y " * 800)])
        # The low synthetic context threshold forces the real pinned summary
        # middleware to call the same real OpenAI client before the user turn.
        model = HttpFailingSummaryModel(responses=[AIMessage(content="unused")])
        def initialize(*args, **kwargs):
            kwargs["http_client"].close()
            client = BudgetClient(controls, transport=httpx.MockTransport(unavailable))
            controls.api_client = client
            self.addCleanup(client.close)
            model.client = client
            model.profile = {"max_input_tokens": 8000}
            return model

        with patch("accounting_finance_agent.agent.init_chat_model", side_effect=initialize), \
             patch("accounting_finance_agent.budget.time.sleep"), \
             patch("accounting_finance_agent.budget.random.random", return_value=0):
            graph = real_build_agent(settings, controls=controls)
            with self.assertRaises(Exception) as failure:
                graph.invoke({"messages": history + [HumanMessage(content="Continue.")]})

        self.assertEqual(len(hits), 6, "expected exactly initial + five shared HTTP attempts")
        self.assertLessEqual(controls.counts["model"], 6)
        self.assertGreater(len(hits), 0, f"no synthetic HTTP call; model={model.calls}, error={failure.exception!r}")
        self.assertEqual(model.calls, 1, "pinned summary middleware retried outside the HTTP attempt budget")


if __name__ == "__main__":
    unittest.main()
