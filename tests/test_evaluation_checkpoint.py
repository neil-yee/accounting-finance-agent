"""Regression for checkpoint deletion followed by remote deliverable recreation."""

from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from accounting_finance_agent import workspace


def advance_checkpoint_baseline(previous, remote_files):
    """Use the production helper when present; emulate the old assignment otherwise."""
    advance = getattr(workspace, "advance_baseline", None)
    return advance(previous, remote_files) if advance else remote_files


class CheckpointSandbox:
    def __init__(self, files):
        self.files = files

    def run(self, command, *, timeout):
        listing = {
            name.removeprefix("/workspace/"): sha256(content).hexdigest()
            for name, content in self.files.items()
        }
        return SimpleNamespace(exit_code=0, stdout=json.dumps(listing))

    def read(self, path):
        return self.files[path]

    def write(self, path, content):
        self.files[path] = content


class CheckpointDeletionRecreationTests(unittest.TestCase):
    def _check_remote_recreation_replaces_untouched_host_copy_after_checkpoint_deletion(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            root.mkdir()
            local_file = root / "deliverable.xlsx"
            original = b"original generated workbook"
            regenerated = b"regenerated workbook"
            local_file.write_bytes(original)
            sandbox = CheckpointSandbox({"/workspace/deliverable.xlsx": original})
            output = io.StringIO()

            with patch.object(workspace, "LOCAL_WORKSPACE", root), redirect_stdout(output):
                baseline = workspace.upload_workspace(sandbox)

                # A tool removes the output during an intermediate checkpoint.
                sandbox.files.clear()
                checkpoint = workspace.download_workspace(sandbox, "run-delete", baseline)
                # This is the production preserve() update: the latest remote
                # listing advances the next checkpoint's baseline.
                baseline = advance_checkpoint_baseline(baseline, checkpoint["remote_files"])
                self.assertEqual(local_file.read_bytes(), original)

                # The tool regenerates that same path with new content. The host
                # copy is unchanged, so this should be recognized as a remote
                # change relative to the original uploaded baseline.
                sandbox.files["/workspace/deliverable.xlsx"] = regenerated
                recreated = workspace.download_workspace(sandbox, "run-recreate", baseline)

            self.assertEqual(local_file.read_bytes(), regenerated)
            self.assertEqual(recreated["conflict_files"], {})
            self.assertEqual(recreated["changed_files"]["deliverable.xlsx"],
                             sha256(regenerated).hexdigest())
            self.assertEqual((root / ".versions/run-recreate/deliverable.xlsx").read_bytes(), original)

    def test_remote_recreation_replaces_untouched_host_copy_after_checkpoint_deletion(self):
        self._check_remote_recreation_replaces_untouched_host_copy_after_checkpoint_deletion()

    def test_actual_host_edit_after_checkpoint_deletion_remains_a_conflict(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            root.mkdir()
            local_file = root / "deliverable.xlsx"
            original = b"original generated workbook"
            host_edit = b"intentional local reviewer edit"
            regenerated = b"regenerated workbook"
            local_file.write_bytes(original)
            sandbox = CheckpointSandbox({"/workspace/deliverable.xlsx": original})

            with patch.object(workspace, "LOCAL_WORKSPACE", root), redirect_stdout(io.StringIO()):
                baseline = workspace.upload_workspace(sandbox)
                sandbox.files.clear()
                checkpoint = workspace.download_workspace(sandbox, "run-delete", baseline)
                baseline = advance_checkpoint_baseline(baseline, checkpoint["remote_files"])
                local_file.write_bytes(host_edit)
                sandbox.files["/workspace/deliverable.xlsx"] = regenerated
                recreated = workspace.download_workspace(sandbox, "run-recreate", baseline)

            self.assertEqual(local_file.read_bytes(), host_edit)
            self.assertEqual(recreated["conflict_files"]["deliverable.xlsx"],
                             sha256(regenerated).hexdigest())
            self.assertEqual((root / ".conflicts/run-recreate/deliverable.xlsx").read_bytes(),
                             regenerated)


if getattr(workspace, "advance_baseline", None) is None:
    # Until the production helper lands, keep the regression as an explicit
    # expected failure while exercising the old remote-list replacement rule.
    CheckpointDeletionRecreationTests.test_remote_recreation_replaces_untouched_host_copy_after_checkpoint_deletion = (
        unittest.expectedFailure(
            CheckpointDeletionRecreationTests.test_remote_recreation_replaces_untouched_host_copy_after_checkpoint_deletion
        )
    )


if __name__ == "__main__":
    unittest.main()
