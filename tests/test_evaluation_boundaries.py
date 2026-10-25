"""Adversarial offline checks for task, transfer, and recovery boundaries.

These tests use real temporary local files and deterministic in-memory remote
filesystems/provider transports. They do not establish live service boundaries.
"""

from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx

from accounting_finance_agent import knowledge, workspace
from accounting_finance_agent.budget import BudgetClient
from accounting_finance_agent.config import EXCEL_PROFILE, Settings
from accounting_finance_agent.runtime import RunContext, RunControls


class MemorySandbox:
    """Small remote filesystem implementing only workspace transfer calls."""

    def __init__(self):
        self.files = {}
        self.reads = []

    def run(self, command, *, timeout):
        if "print(json.dumps(files))" in command:
            listing = {
                name.removeprefix("/workspace/"): sha256(data).hexdigest()
                for name, data in self.files.items()
            }
            return SimpleNamespace(exit_code=0, stdout=json.dumps(listing))
        return SimpleNamespace(exit_code=0, stdout="{}")

    def write(self, path, content):
        self.files[path] = content

    def read(self, path):
        self.reads.append(path)
        return self.files[path]


class WorkspaceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(workspace, "LOCAL_WORKSPACE", self.root / "workspace"))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.root.joinpath("workspace").mkdir()
        self.remote = MemorySandbox()

    def test_changed_protected_source_fails_without_overwriting_local_source(self):
        source = self.root / "workspace" / "input.csv"
        source.write_bytes(b"owner source")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files["/workspace/input.csv"] = b"sandbox altered source"
        self.remote.files["/workspace/result.csv"] = b"deliverable"

        with self.assertRaisesRegex(RuntimeError, "Protected source files changed"):
            workspace.download_workspace(self.remote, "run-1", baseline, protected=("input.csv",))

        self.assertEqual(source.read_bytes(), b"owner source")
        self.assertFalse((self.root / "workspace" / ".conflicts/run-1/input.csv").exists())
        # Other output remains available for review even though source validation failed.
        self.assertEqual((self.root / "workspace" / "result.csv").read_bytes(), b"deliverable")

    def test_missing_protected_source_is_detected_and_not_deleted_locally(self):
        source = self.root / "workspace" / "input.csv"
        source.write_bytes(b"owner source")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files.clear()

        with self.assertRaisesRegex(RuntimeError, "Protected source files changed or disappeared"):
            workspace.download_workspace(self.remote, "run-1", baseline, protected=("input.csv",))
        self.assertEqual(source.read_bytes(), b"owner source")

    def test_changed_name_colliding_with_unchanged_remote_name_is_rejected(self):
        original = self.root / "workspace" / "Report.csv"
        original.write_bytes(b"baseline")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files["/workspace/report.csv"] = b"new spelling"

        with self.assertRaisesRegex(ValueError, "Case-colliding workspace filename"):
            workspace.download_workspace(self.remote, "run-1", baseline)

        self.assertFalse((self.root / "workspace" / "report.csv").exists())

    def test_local_symlink_in_remote_target_path_is_rejected_before_read(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "workspace" / "linked").symlink_to(outside, target_is_directory=True)
        self.remote.files["/workspace/linked/escape.txt"] = b"do not copy"
        with self.assertRaisesRegex(ValueError, "Workspace links are not supported"):
            workspace.download_workspace(self.remote, "run-1", {})
        self.assertEqual(self.remote.reads, [])
        self.assertFalse((outside / "escape.txt").exists())

    def test_distinct_thread_workspaces_do_not_share_real_files(self):
        first, second = workspace.thread_workspace(str(uuid4())), workspace.thread_workspace(str(uuid4()))
        with workspace.use_workspace(first):
            (workspace.workspace_root() / "source.csv").write_text("task one")
        with workspace.use_workspace(second):
            self.assertEqual(workspace.workspace_manifest(), {})
            (workspace.workspace_root() / "source.csv").write_text("task two")
        self.assertEqual((first / "source.csv").read_text(), "task one")
        self.assertEqual((second / "source.csv").read_text(), "task two")


class ReferenceAndProviderBoundaryTests(unittest.TestCase):
    def test_benchmark_reference_namespace_rejects_unapproved_routes_and_writes(self):
        with TemporaryDirectory() as root:
            base = Path(root)
            with patch.object(knowledge, "PROJECT_ROOT", base), \
                 patch.object(knowledge, "MEMORY_ROOT", base / "legacy-memory"), \
                 patch.object(knowledge, "SKILLS_ROOT", base / "skills"):
                allowed_memory = base / "references/excel-benchmark/memory"
                allowed_memory.mkdir(parents=True)
                (allowed_memory / "AGENTS.md").write_text("approved")
                (base / "legacy-memory").mkdir()
                (base / "legacy-memory/company-profile.md").write_text("private legacy data")
                settings = Settings("gpt-6-luna", "high", False, "offline", profile=EXCEL_PROFILE)
                backend = knowledge.knowledge_backend(settings=settings)
                self.assertIn("approved", backend.read("/memories/AGENTS.md").file_data["content"])
                self.assertTrue(backend.read("/memories/company-profile.md").error)
                self.assertTrue(backend.read("/skills/bank-reconciliation/SKILL.md").error)
                self.assertTrue(backend.write("/memories/AGENTS.md", "mutated").error)
                self.assertEqual((allowed_memory / "AGENTS.md").read_text(), "approved")

    def test_incomplete_success_response_keeps_provider_reservation(self):
        settings = Settings("gpt-6-luna", "high", False, "offline", profile=EXCEL_PROFILE)
        controls = RunControls(settings, RunContext("run", "thread", "UTC", "virtual"), Mock())
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"output": []}))
        with BudgetClient(controls, transport=transport) as client:
            response = client.post("https://api.openai.com/v1/responses", json={
                "model": "gpt-6-luna", "input": "hello", "max_output_tokens": 100,
            })
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("usage", response.json())
            self.assertGreater(client.spent, 0)
            self.assertEqual(controls.counts["model"], 1)

    def test_provider_retry_ceiling_caps_one_call_at_six_attempts(self):
        attempts = []
        settings = Settings("gpt-6-luna", "high", False, "offline", profile=EXCEL_PROFILE)
        controls = RunControls(settings, RunContext("run", "thread", "UTC", "virtual"), Mock())
        def unavailable(request):
            attempts.append(request)
            return httpx.Response(503, json={"error": "temporary"})
        with BudgetClient(controls, transport=httpx.MockTransport(unavailable)) as client, \
             patch("accounting_finance_agent.budget.time.sleep"), redirect_stdout(io.StringIO()):
            response = client.post("https://api.openai.com/v1/responses", json={
                "model": "gpt-6-luna", "input": "hello", "max_output_tokens": 100,
            })
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(attempts), 6)
        self.assertEqual(controls.counts["model"], 6)


if __name__ == "__main__":
    unittest.main()
