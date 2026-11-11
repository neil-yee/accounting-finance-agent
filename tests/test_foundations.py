"""Offline checks with disposable files/databases and no provider calls."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from dataclasses import replace
from datetime import datetime
from hashlib import sha256
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4
from zipfile import ZipFile
from zoneinfo import ZoneInfo

from langchain.agents.middleware import ModelRequest
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest

from accounting_finance_agent import config, knowledge, runtime, worklog, workspace
from accounting_finance_agent.file_metadata import add_file_names
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.runtime import RunContext, RunControls, RunLimitExceeded
from accounting_finance_agent.validation import validate_artifact
from accounting_finance_agent.worklog import WorkLog, thread_lease


def settings(**overrides):
    return replace(config.Settings("gpt-6-luna", "high", False, "offline-checks"), **overrides)


class RuntimeChecks(unittest.TestCase):
    def setUp(self):
        self.log = Mock()
        self.context = RunContext("run-test", "thread-test", "America/Toronto", "virtual")

    def test_model_budget_blocks_before_the_next_handler(self):
        controls = RunControls(settings(max_model_calls=2), self.context, self.log)
        controls.reserve("model")
        controls.reserve("model")
        with self.assertRaises(RunLimitExceeded):
            controls.reserve("model")
        self.assertEqual(controls.counts["model"], 2)

    def test_tool_budget_is_shared_across_parallel_attempts(self):
        controls = RunControls(settings(max_tool_calls=5), self.context, self.log)
        def attempt(_):
            try:
                controls.reserve("tool")
                return True
            except RunLimitExceeded:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(attempt, range(30)))
        self.assertEqual(sum(outcomes), 5)
        self.assertEqual(controls.counts["tool"], 5)

    def test_deadline_blocks_both_types_without_incrementing(self):
        with patch.object(runtime, "monotonic", return_value=0):
            controls = RunControls(settings(run_seconds=10), self.context, self.log)
        with patch.object(runtime, "monotonic", return_value=10):
            for kind in ("model", "tool"):
                with self.assertRaises(RunLimitExceeded):
                    controls.reserve(kind)
        self.assertEqual(controls.counts, {"model": 0, "tool": 0})

    def test_current_time_refreshes_without_mutating_saved_prompt(self):
        controls = RunControls(settings(), self.context, self.log)
        original = SystemMessage(content="Original instructions")
        request = ModelRequest(model=Mock(), messages=[], system_message=original)
        dates = [datetime(2026, 1, 15, 9, minute, tzinfo=ZoneInfo("America/Toronto")) for minute in (0, 1)]
        with patch.object(runtime, "datetime") as clock:
            clock.now.side_effect = dates
            first = controls.model_request(request)
            second = controls.model_request(request)
        self.assertIn("2026-01-15T09:00:00-05:00", first.system_message.text)
        self.assertIn("2026-01-15T09:01:00-05:00", second.system_message.text)
        self.assertIn("Thursday", first.system_message.text)
        self.assertIn("run-test", first.system_message.text)
        self.assertEqual(original.content, "Original instructions")
        self.assertEqual(second.system_message.text.count("Current local time:"), 1)

    def test_execute_timeout_preparation_preserves_other_arguments(self):
        controls = RunControls(settings(), self.context, self.log)
        for timeout, expected in ((0, 120), (-1, 120), (120000, 120), (30, 30), (None, None)):
            with self.subTest(timeout=timeout):
                call = {"name": "execute", "id": "execute-1", "args": {"command": "echo test", "timeout": timeout}}
                request = ToolCallRequest(tool_call=call, tool=None, state={}, runtime=None)
                prepared = controls.prepare_tool_request(request)
                self.assertEqual(prepared.tool_call["args"], {"command": "echo test", "timeout": expected})
                self.assertEqual(request.tool_call["args"]["timeout"], timeout)
        request = ToolCallRequest(tool_call={"name": "other", "id": "other-1", "args": {"timeout": 120000}},
                                  tool=None, state={}, runtime=None)
        self.assertIs(controls.prepare_tool_request(request), request)


class ConfigurationChecks(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(config, "load_dotenv"))
        self.enterContext(patch.dict(os.environ, {"OPENAI_API_KEY": "offline-placeholder", "LANGSMITH_TRACING": "false"}, clear=True))

    def test_defaults_and_snapshot_override(self):
        self.assertEqual(config.load_settings().max_model_calls, 100)
        with patch.dict(os.environ, {"SANDBOX_SNAPSHOT_ID": "chosen-id", "AGENT_MAX_MODEL_CALLS": "7"}):
            loaded = config.load_settings()
        self.assertEqual(loaded.sandbox_snapshot_id, "chosen-id")
        self.assertEqual(loaded.max_model_calls, 7)

    def test_invalid_limits_fail_at_startup(self):
        for name in ("AGENT_MAX_MODEL_CALLS", "AGENT_MAX_TOOL_CALLS", "AGENT_RUN_SECONDS", "AGENT_MODEL_TIMEOUT_SECONDS", "AGENT_TOOL_TIMEOUT_SECONDS", "AGENT_MAX_OUTPUT_TOKENS"):
            for value in ("0", "-1", "abc"):
                with self.subTest(name=name, value=value), patch.dict(os.environ, {name: value}):
                    with self.assertRaises(config.ConfigurationError):
                        config.load_settings()

    def test_invalid_timezone_and_empty_allowlist_fail(self):
        for env in ({"AGENT_TIMEZONE": "Unknown/Nowhere"}, {"SANDBOX_ALLOWED_HOSTS": " , "}):
            with self.subTest(env=env), patch.dict(os.environ, env):
                with self.assertRaises(config.ConfigurationError):
                    config.load_settings()


class StorageChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(workspace, "LOCAL_WORKSPACE", self.root / "workspace"))
        self.enterContext(patch.object(worklog, "PROJECT_ROOT", self.root))

    def test_thread_workspaces_are_separate_and_legacy_files_remain(self):
        workspace.LOCAL_WORKSPACE.mkdir()
        legacy = workspace.LOCAL_WORKSPACE / "legacy.txt"
        legacy.write_text("original")
        one, two = (workspace.thread_workspace(str(uuid4())) for _ in range(2))
        (one / "source.txt").write_text("thread one")
        with workspace.use_workspace(one):
            manifest = workspace.workspace_manifest()
        self.assertEqual(set(manifest), {"source.txt"})
        self.assertFalse((two / "source.txt").exists())
        self.assertEqual(legacy.read_text(), "original")
        self.assertEqual(workspace.workspace_root(), workspace.LOCAL_WORKSPACE)

    def test_workspace_scope_resets_after_exception_and_excludes_history(self):
        folder = workspace.thread_workspace(str(uuid4()))
        (folder / ".versions").mkdir()
        (folder / ".versions" / "old.txt").write_text("old")
        with self.assertRaises(RuntimeError):
            with workspace.use_workspace(folder):
                self.assertEqual(workspace.workspace_manifest(), {})
                raise RuntimeError("stop")
        self.assertEqual(workspace.workspace_root(), workspace.LOCAL_WORKSPACE)

    def test_invalid_thread_identifier_cannot_escape_workspace(self):
        with self.assertRaises(ValueError):
            workspace.thread_workspace("../outside")

    def test_thread_lock_prevents_overlap_and_releases_after_error(self):
        with self.assertRaisesRegex(RuntimeError, "task failure"):
            with thread_lease("same-thread"):
                with self.assertRaisesRegex(ValueError, "run lock"):
                    with thread_lease("same-thread"):
                        self.fail("Second runner acquired the same lock")
                raise RuntimeError("task failure")
        with thread_lease("same-thread"):
            pass

    def test_thread_selection_and_checkpoint_survive_reopen(self):
        db = self.root / "checkpoints.sqlite"
        with open_history(mode="sandbox", database=db) as history:
            first = history.initial()
            history.record_prompt(first, "First task")
            second = history.new()
            history.select(first.id)
        with open_history(mode="sandbox", database=db) as history:
            self.assertEqual(history.initial().id, first.id)
            self.assertEqual(len(history.list()), 2)
            self.assertEqual(history.select(second.id).id, second.id)
        with open_history(mode="virtual", database=db) as history:
            with self.assertRaises(ValueError):
                history.select(first.id)


class WorkLogChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.database = self.root / "worklog.sqlite"
        self.log = WorkLog(self.database)
        self.addCleanup(lambda: self.log.close())
        self.files = {"report.xlsx": "hash-v1"}
        self.log.start("run-1", "thread-1", {"snapshot": "s1"}, {"source.csv": "source-hash"})

    def test_run_events_and_outcome_persist_after_reopen(self):
        self.log.event("run-1", "tool_finished", name="execute", status="success")
        self.log.finish("run-1", "needs_review", self.files)
        self.log.close()
        self.log = WorkLog(self.database)
        row = self.log.runs("thread-1")[0]
        self.assertEqual(row["status"], "needs_review")
        self.assertEqual(self.log.conn.execute("SELECT count(*) FROM events").fetchone()[0], 1)
        self.assertEqual(self.log.runs("unrelated-thread"), [])

    def test_approval_requires_success_same_thread_and_exact_hashes(self):
        with self.assertRaises(ValueError):
            self.log.review("run-1", "thread-1", "approved", self.files, "reviewer")
        self.log.finish("run-1", "needs_review", self.files)
        for thread, manifest in (("thread-2", self.files), ("thread-1", {"report.xlsx": "new-hash"}), ("thread-1", {})):
            with self.subTest(thread=thread, manifest=manifest), self.assertRaises(ValueError):
                self.log.review("run-1", thread, "approved", manifest, "reviewer")
        self.log.review("run-1", "thread-1", "approved", self.files, "reviewer")
        self.assertEqual(self.log.review_status("run-1", self.files), "approved")
        self.assertIn("changed since review", self.log.review_status("run-1", {}))

    def test_review_decision_must_be_explicit(self):
        self.log.finish("run-1", "needs_review", self.files)
        with self.assertRaises(ValueError):
            self.log.review("run-1", "thread-1", "approevd", self.files, "reviewer")

    def test_failed_run_cannot_be_approved_and_rejection_is_separate(self):
        self.log.finish("run-1", "failed", self.files, "TimeoutError")
        with self.assertRaises(ValueError):
            self.log.review("run-1", "thread-1", "approved", self.files, "reviewer")
        self.log.review("run-1", "thread-1", "rejected", self.files, "reviewer", "Needs revision")
        self.assertEqual(self.log.runs("thread-1")[0]["status"], "failed")
        self.assertEqual(self.log.review_status("run-1", self.files), "rejected")

    def test_recovery_requires_original_upload_baseline(self):
        with self.assertRaises(ValueError):
            self.log.recovery_record("run-1")
        self.log.event("run-1", "sandbox_created", sandbox="finance-retained")
        self.log.event("run-1", "workspace_uploaded", sandbox="finance-retained", files={"input.csv": "h"})
        self.assertEqual(self.log.recovery_record("run-1"), ("thread-1", "finance-retained", {"input.csv": "h"}))


class ReferenceAndMetadataChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(knowledge, "MEMORY_ROOT", self.root / "memory"))
        self.enterContext(patch.object(knowledge, "SKILLS_ROOT", self.root / "skills"))

    def test_reference_routes_read_but_reject_all_mutation_methods(self):
        backend = knowledge.knowledge_backend()
        (knowledge.MEMORY_ROOT / "AGENTS.md").write_text("approved guidance")
        read = backend.read("/memories/AGENTS.md")
        self.assertIsNone(read.error)
        self.assertIn("approved guidance", read.file_data["content"])
        self.assertTrue(backend.write("/memories/AGENTS.md", "replacement").error)
        self.assertTrue(backend.edit("/memories/AGENTS.md", "approved", "changed").error)
        self.assertTrue(backend.delete("/memories/AGENTS.md").error)
        self.assertEqual(backend.upload_files([("/memories/AGENTS.md", b"replacement")])[0].error, "permission_denied")
        self.assertTrue(backend.write("/skills/new/SKILL.md", "replacement").error)
        self.assertEqual((knowledge.MEMORY_ROOT / "AGENTS.md").read_text(), "approved guidance")

    def test_filename_repair_preserves_original_history_and_existing_filename(self):
        source = ToolMessage(content=[{"type": "file", "mime_type": "application/pdf", "base64": "YQ=="}],
                             tool_call_id="read-1", additional_kwargs={"read_file_path": "/workspace/filing.pdf"})
        repaired = add_file_names([source])[0]
        self.assertEqual(repaired.content[0]["filename"], "filing.pdf")
        self.assertNotIn("filename", source.content[0])
        repaired.content[0]["filename"] = "chosen.pdf"
        self.assertEqual(add_file_names([repaired])[0].content[0]["filename"], "chosen.pdf")

    def test_filename_can_be_recovered_from_tool_call_history(self):
        call = AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"file_path": "/workspace/book.xlsx"}, "id": "read-2"}])
        result = ToolMessage(content=[{"type": "file", "mime_type": "application/octet-stream", "base64": "YQ=="}], tool_call_id="read-2")
        repaired = add_file_names([call, result])
        self.assertEqual(repaired[1].content[0]["filename"], "book.xlsx")


class StructuralValidationChecks(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))

    def test_csv_structure_and_json_syntax(self):
        good = self.root / "good.csv"
        good.write_text("Item,Amount\nCoffee,4.50\n")
        self.assertEqual(validate_artifact(good)["rows"], 1)
        good.write_text("Item,Amount\nCoffee\n")
        self.assertTrue(validate_artifact(good)["errors"])
        malformed = self.root / "broken.json"
        malformed.write_text("{invalid}")
        self.assertTrue(validate_artifact(malformed)["errors"])

    def test_office_package_checks_and_formula_limitations(self):
        path = self.root / "book.xlsx"
        with ZipFile(path, "w") as archive:
            archive.writestr("xl/workbook.xml", "<workbook/>")
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c><f>1+1</f><v/></c></row></sheetData></worksheet>')
        result = validate_artifact(path)
        self.assertEqual(result["errors"], [])
        self.assertIn("No recalculation", " ".join(result["warnings"]))
        with ZipFile(path, "w") as archive:
            archive.writestr("wrong.xml", "<root/>")
        self.assertTrue(validate_artifact(path)["errors"])


if __name__ == "__main__":
    unittest.main()
