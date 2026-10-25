"""Offline failure-path checks for the live boundary probe's child runner."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from langsmith.sandbox import ResourceNotFoundError

from scripts import probe_evaluation_boundaries as probe


class ProbeChildFailureTests(unittest.TestCase):
    def test_timeout_and_nonzero_exit_both_invoke_recorded_sandbox_recovery(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "recovery.json"
            metadata.write_text(json.dumps({"sandbox_name": "finance-probe-owned"}))
            for failure in (
                __import__("subprocess").TimeoutExpired(["child"], 1),
                SimpleNamespace(returncode=3, stderr="synthetic failure"),
            ):
                with self.subTest(failure=type(failure).__name__):
                    handler = Mock(return_value={"status": "recovered_and_deleted"})
                    runner = Mock(side_effect=failure) if isinstance(failure, Exception) else Mock(return_value=failure)
                    with self.assertRaisesRegex(RuntimeError, "Probe child"):
                        probe.run_child_process(["child"], metadata, root / "workspace",
                                                timeout=1, failure_handler=handler, runner=runner)
                    handler.assert_called_once_with(
                        metadata, root / "workspace",
                        "child process timed out" if isinstance(failure, Exception)
                        else "child exited 3",
                    )

    def test_failure_recovery_exports_then_deletes_only_recorded_sandbox(self):
        class Client:
            def __init__(self):
                self.deleted = []
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def get_sandbox(self, name):
                self.requested = name
                return object()
            def delete_sandbox(self, name):
                self.deleted.append(name)
            def get_sandbox_status(self, name):
                raise ResourceNotFoundError("deleted", resource_type="sandbox")

        with TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "recovery.json"
            metadata.write_text(json.dumps({
                "sandbox_name": "finance-probe-owned",
                "uploaded_baseline": {"source.csv": "baseline-hash"},
            }))
            client = Client()
            exported = Mock(return_value={"remote_files": {"result.txt": "digest"}})
            with unittest.mock.patch.object(probe, "download_workspace", exported), redirect_stdout(io.StringIO()):
                result = probe.recover_or_cleanup_failed_child(
                    metadata, root / "workspace", "child exited 2",
                    client_factory=lambda **kwargs: client,
                )
            self.assertEqual(result["status"], "recovered_and_deleted")
            exported.assert_called_once()
            self.assertEqual(client.requested, "finance-probe-owned")
            self.assertEqual(client.deleted, ["finance-probe-owned"])
            self.assertEqual(json.loads(metadata.read_text())["child_failure_handling"]["status"],
                             "recovered_and_deleted")

    def test_export_failure_records_retention_and_does_not_delete_sandbox(self):
        class Client:
            def __init__(self):
                self.deleted = []
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def get_sandbox(self, name):
                return object()
            def delete_sandbox(self, name):
                self.deleted.append(name)

        with TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "recovery.json"
            metadata.write_text(json.dumps({
                "sandbox_name": "finance-probe-owned",
                "uploaded_baseline": {"source.csv": "baseline-hash"},
            }))
            client = Client()
            with unittest.mock.patch.object(probe, "download_workspace", side_effect=OSError("offline")), \
                 redirect_stdout(io.StringIO()):
                result = probe.recover_or_cleanup_failed_child(
                    metadata, root / "workspace", "child timed out",
                    client_factory=lambda **kwargs: client,
                )
            self.assertEqual(result["status"], "retained_for_recovery")
            self.assertIn("Inspect the recorded sandbox", result["manual_action"])
            self.assertEqual(client.deleted, [])
            stored = json.loads(metadata.read_text())["child_failure_handling"]
            self.assertEqual(stored["sandbox_name"], "finance-probe-owned")
            self.assertEqual(stored["status"], "retained_for_recovery")


if __name__ == "__main__":
    unittest.main()
