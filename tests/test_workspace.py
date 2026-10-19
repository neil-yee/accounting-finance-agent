"""Exercise shared-folder transfers against an in-memory remote filesystem."""

from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from accounting_finance_agent import workspace


class FakeSandbox:
    def __init__(self):
        self.files = {}
        self.reads = []
        self.corrupt_reads = False

    def run(self, command, *, timeout):
        listing = {
            path.removeprefix("/workspace/"): sha256(data).hexdigest()
            for path, data in self.files.items()
        }
        return SimpleNamespace(exit_code=0, stdout=json.dumps(listing))

    def write(self, path, content):
        self.files[path] = content

    def read(self, path):
        self.reads.append(path)
        return b"corrupt" if self.corrupt_reads else self.files[path]


class SharedWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.enterContext(patch.object(workspace, "LOCAL_WORKSPACE", self.root))
        self.enterContext(redirect_stdout(io.StringIO()))
        self.remote = FakeSandbox()

    def local(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def test_new_and_changed_files_return_to_the_same_folder(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files["/workspace/report.txt"] = b"revised"
        self.remote.files["/workspace/nested/new.bin"] = bytes(range(256))
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(original.read_bytes(), b"revised")
        self.assertEqual((self.root / "nested/new.bin").read_bytes(), bytes(range(256)))
        self.assertEqual((self.root / ".versions/run-1/report.txt").read_bytes(), b"original")
        self.assertFalse((self.root / "inputs").exists())
        self.assertFalse((self.root / "outputs").exists())

    def test_unchanged_remote_file_does_not_download_over_a_local_edit(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        original.write_bytes(b"local edit")
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(original.read_bytes(), b"local edit")
        self.assertEqual(self.remote.reads, [])

    def test_concurrent_edits_keep_local_and_preserve_remote(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        original.write_bytes(b"local edit")
        self.remote.files["/workspace/report.txt"] = b"remote edit"
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(original.read_bytes(), b"local edit")
        self.assertEqual((self.root / ".conflicts/run-1/report.txt").read_bytes(), b"remote edit")

    def test_new_local_file_is_not_overwritten_by_a_new_remote_file(self):
        baseline = workspace.upload_workspace(self.remote)
        local = self.local("new.txt", b"local")
        self.remote.files["/workspace/new.txt"] = b"remote"
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(local.read_bytes(), b"local")
        self.assertEqual((self.root / ".conflicts/run-1/new.txt").read_bytes(), b"remote")

    def test_remote_deletion_does_not_delete_local_file(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files.clear()
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(original.read_bytes(), b"original")

    def test_local_deletion_and_remote_edit_are_saved_as_conflict(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        original.unlink()
        self.remote.files["/workspace/report.txt"] = b"remote edit"
        workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertFalse(original.exists())
        self.assertEqual((self.root / ".conflicts/run-1/report.txt").read_bytes(), b"remote edit")

    def test_hidden_files_and_old_test_artifacts_are_not_uploaded(self):
        self.local(".env", b"private")
        self.local(".versions/old/report.txt", b"old")
        self.local(".conflicts/old/report.txt", b"conflict")
        self.local("transfer-tests/old/report.txt", b"test fixture")
        self.local("__pycache__/cache.pyc", b"cache")
        self.local("nested/working.txt", b"working")
        baseline = workspace.upload_workspace(self.remote)
        self.assertEqual(set(baseline), {"nested/working.txt"})
        self.assertEqual(set(self.remote.files), {"/workspace/nested/working.txt"})

    def test_remote_internal_file_is_not_downloaded(self):
        self.remote.files["/workspace/.versions/forged.txt"] = b"ignore"
        workspace.download_workspace(self.remote, "run-1", {})
        self.assertEqual(self.remote.reads, [])
        self.assertFalse((self.root / ".versions").exists())

    def test_corrupted_download_does_not_replace_existing_file(self):
        original = self.local("report.txt", b"original")
        baseline = workspace.upload_workspace(self.remote)
        self.remote.files["/workspace/report.txt"] = b"remote edit"
        self.remote.corrupt_reads = True
        with self.assertRaisesRegex(RuntimeError, "changed during download"):
            workspace.download_workspace(self.remote, "run-1", baseline)
        self.assertEqual(original.read_bytes(), b"original")

    def test_remote_path_traversal_is_rejected(self):
        self.remote.files["/workspace/../escape.txt"] = b"unsafe"
        with self.assertRaisesRegex(ValueError, "Unsafe workspace path"):
            workspace.download_workspace(self.remote, "run-1", {})
        self.assertEqual(self.remote.reads, [])


if __name__ == "__main__":
    unittest.main()
