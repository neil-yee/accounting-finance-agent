"""Exercise resource cleanup and allocation timing without cloud API calls."""

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepagents.backends.langsmith import LangSmithSandbox

from accounting_finance_agent import __main__ as cli
from accounting_finance_agent.agent import build_agent
from accounting_finance_agent.config import ConfigurationError, Settings, load_settings
from accounting_finance_agent.sandbox import sandbox_backend


class SandboxLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.remote = MagicMock()
        self.remote.vcpus = 1
        self.remote.mem_bytes = 2 * 1024**3
        self.remote.fs_capacity_bytes = 16 * 1024**3
        self.remote.run.return_value = SimpleNamespace(stdout="", stderr="", exit_code=0)
        self.client.wait_for_sandbox.return_value = self.remote
        client_type = self.enterContext(
            patch("accounting_finance_agent.sandbox.SandboxClient")
        )
        client_type.return_value.__enter__.return_value = self.client
        # Lifecycle tests isolate transfers; the remote mock has no filesystem.
        self.enterContext(patch("accounting_finance_agent.sandbox.upload_workspace", return_value={}))
        self.enterContext(patch("accounting_finance_agent.sandbox.download_workspace"))
        self.output = self.enterContext(redirect_stdout(io.StringIO()))

    def test_success_deletes_sandbox_after_use(self):
        with sandbox_backend() as backend:
            self.assertEqual(backend.execute("python3 --version").exit_code, 0)
            self.client.delete_sandbox.assert_not_called()
        name = self.client.create_sandbox.call_args.kwargs["name"]
        self.client.delete_sandbox.assert_called_once_with(name)
        self.assertIn(f"Sandbox deletion requested: {name}", self.output.getvalue())

    def test_run_failure_still_deletes_sandbox(self):
        with self.assertRaisesRegex(ValueError, "agent failed"):
            with sandbox_backend():
                raise ValueError("agent failed")
        self.client.delete_sandbox.assert_called_once()

    def test_keyboard_interrupt_still_deletes_sandbox(self):
        with self.assertRaises(KeyboardInterrupt):
            with sandbox_backend():
                raise KeyboardInterrupt()
        self.client.delete_sandbox.assert_called_once()

    def test_readiness_failure_still_deletes_sandbox(self):
        self.client.wait_for_sandbox.side_effect = TimeoutError("not ready")
        with self.assertRaises(TimeoutError):
            with sandbox_backend():
                self.fail("A sandbox that is not ready must not be yielded.")
        self.client.delete_sandbox.assert_called_once()

    def test_workspace_failure_still_deletes_sandbox(self):
        self.remote.run.return_value.exit_code = 1
        with self.assertRaisesRegex(RuntimeError, "prepare"):
            with sandbox_backend():
                self.fail("An unprepared workspace must not be yielded.")
        self.client.delete_sandbox.assert_called_once()

    def test_cleanup_failure_is_reported_with_sandbox_name(self):
        self.client.delete_sandbox.side_effect = RuntimeError("network unavailable")
        with self.assertRaisesRegex(RuntimeError, "delete it manually") as raised:
            with sandbox_backend():
                pass
        name = self.client.create_sandbox.call_args.kwargs["name"]
        self.assertIn(name, str(raised.exception))
        self.assertNotIn("Sandbox deletion requested:", self.output.getvalue())

    def test_download_failure_retains_sandbox_for_recovery(self):
        with patch(
            "accounting_finance_agent.sandbox.download_workspace",
            side_effect=RuntimeError("download failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "left available for recovery"):
                with sandbox_backend():
                    pass
        self.client.delete_sandbox.assert_not_called()

    def test_upload_failure_deletes_sandbox_before_agent_runs(self):
        with patch(
            "accounting_finance_agent.sandbox.upload_workspace",
            side_effect=RuntimeError("upload failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "upload failed"):
                with sandbox_backend():
                    self.fail("Failed upload must not start agent work.")
        self.client.delete_sandbox.assert_called_once()

    def test_snapshot_network_settings_and_timeout_cap_reach_sdk(self):
        with sandbox_backend(snapshot_id="release-id", allowed_hosts=("pypi.org:443",), command_timeout=15) as backend:
            backend.execute("echo bounded", timeout=999)
            self.assertEqual(self.remote.run.call_args.kwargs["timeout"], 15)
            backend.execute("echo bounded", timeout=0)
            self.assertEqual(self.remote.run.call_args.kwargs["timeout"], 15)
        kwargs = self.client.create_sandbox.call_args.kwargs
        self.assertEqual(kwargs["snapshot_id"], "release-id")
        self.assertEqual(kwargs["proxy_config"], {"access_control": {"allow_list": ["pypi.org:443"]}})

    def test_create_failure_still_requests_cleanup_by_name(self):
        self.client.create_sandbox.side_effect = TimeoutError("create response lost")
        with self.assertRaisesRegex(TimeoutError, "create response lost"):
            with sandbox_backend():
                self.fail("Creation failed")
        name = self.client.create_sandbox.call_args.kwargs["name"]
        self.client.delete_sandbox.assert_called_once_with(name)


class SandboxEntryPointTests(unittest.TestCase):
    def test_sandbox_backend_enables_the_execute_tool(self):
        settings = Settings("gpt-6-luna", "high", False, "accounting-finance-agent")
        remote = MagicMock()
        remote.name = "offline-test"
        remote.run.return_value = SimpleNamespace(stdout="4\n", stderr="", exit_code=0)
        backend = LangSmithSandbox(sandbox=remote)
        # Exercise direct command routing without the separate output-offload wrapper.
        backend.enable_capture_offload = False
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "offline-placeholder", "LANGSMITH_TRACING": "false"},
        ):
            default_agent = build_agent(settings)
            execution_agent = build_agent(settings, backend=backend)
        default_tools = default_agent.get_graph().nodes["tools"].data.tools_by_name
        execution_tools = execution_agent.get_graph().nodes["tools"].data.tools_by_name
        runtime = SimpleNamespace(tool_call_id="offline-execution-check")
        command = "python3 -c 'print(2 + 2)'"
        unavailable = default_tools["execute"].func(command=command, runtime=runtime)
        result = execution_tools["execute"].func(command=command, runtime=runtime)
        self.assertEqual(unavailable.status, "error")
        self.assertIn("Execution not available", unavailable.content)
        self.assertEqual(result.status, "success")
        self.assertIn("4", result.content)
        remote.run.assert_called_once()

    def test_exiting_without_a_prompt_does_not_allocate_a_sandbox(self):
        settings = Settings("gpt-6-luna", "high", False, "accounting-finance-agent")
        with (
            patch("sys.argv", ["finance-agent", "--sandbox"]),
            patch.object(cli, "load_settings", return_value=settings),
            patch.object(cli, "open_history"),
            patch.object(cli, "WorkLog"),
            patch.object(cli, "thread_workspace", return_value=Path("offline-workspace")),
            patch.object(cli, "sandbox_backend") as backend,
            patch.object(cli, "build_agent") as builder,
            patch("builtins.input", return_value="exit"),
            redirect_stdout(io.StringIO()),
        ):
            cli.main()
        backend.assert_not_called()
        builder.assert_not_called()

    def test_sandbox_requires_credentials_when_tracing_is_disabled(self):
        with (
            patch("accounting_finance_agent.config.load_dotenv"),
            patch.dict(
                "os.environ",
                {"OPENAI_API_KEY": "offline-placeholder", "LANGSMITH_TRACING": "false"},
                clear=True,
            ),
        ):
            with self.assertRaisesRegex(ConfigurationError, "LANGSMITH_API_KEY"):
                load_settings(require_sandbox=True)


if __name__ == "__main__":
    unittest.main()
