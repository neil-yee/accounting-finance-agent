"""Check deletion verification without creating or querying a real sandbox."""

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from langsmith.sandbox import ResourceNotFoundError

from scripts.check_workspace_transfer import confirm_sandbox_deleted


class DeletionConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.output = self.enterContext(redirect_stdout(io.StringIO()))
        self.sleep = self.enterContext(patch("scripts.check_workspace_transfer.sleep"))

    def test_deletion_can_take_multiple_reads(self):
        self.client.get_sandbox_status.side_effect = [
            SimpleNamespace(status="ready"),
            SimpleNamespace(status="stopped"),
            ResourceNotFoundError("gone", resource_type="sandbox"),
        ]
        confirm_sandbox_deleted(self.client, "example")
        self.assertEqual(self.client.get_sandbox_status.call_count, 3)
        self.assertEqual(self.sleep.call_count, 2)
        self.assertIn("PASS: sandbox deletion confirmed", self.output.getvalue())

    def test_already_absent_succeeds_without_waiting(self):
        self.client.get_sandbox_status.side_effect = ResourceNotFoundError(
            "gone", resource_type="sandbox"
        )
        confirm_sandbox_deleted(self.client, "example")
        self.sleep.assert_not_called()

    def test_stopped_record_is_not_confirmed_deleted(self):
        self.client.get_sandbox_status.return_value = SimpleNamespace(status="stopped")
        with self.assertRaisesRegex(TimeoutError, "last status: stopped"):
            confirm_sandbox_deleted(self.client, "example", timeout=0)
        self.assertNotIn("PASS:", self.output.getvalue())
        self.sleep.assert_not_called()

    def test_api_error_is_not_mistaken_for_deletion(self):
        self.client.get_sandbox_status.side_effect = RuntimeError("unauthorized")
        with self.assertRaisesRegex(RuntimeError, "unauthorized"):
            confirm_sandbox_deleted(self.client, "example")
        self.assertNotIn("PASS:", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
