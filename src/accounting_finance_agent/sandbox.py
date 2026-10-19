"""Create a temporary LangSmith execution backend and explicitly delete it."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import ResourceNotFoundError, SandboxClient

from accounting_finance_agent.workspace import download_workspace, upload_workspace

# Explicit small allocation, not a claim about the provider's minimum size.
SANDBOX_VCPUS = 1
SANDBOX_MEMORY_BYTES = 2 * 1024**3
SANDBOX_IDLE_TTL_SECONDS = 300
SANDBOX_DELETE_AFTER_STOP_SECONDS = 600
SANDBOX_WORKSPACE = "/workspace"


class BoundedSandbox(LangSmithSandbox):
    def __init__(self, *, sandbox, command_timeout: int):
        super().__init__(sandbox=sandbox)
        self.command_timeout = command_timeout

    def execute(self, command: str, *, timeout: int | None = None):
        effective = self.command_timeout if not timeout or timeout < 0 else min(timeout, self.command_timeout)
        return super().execute(command, timeout=effective)

    async def aexecute(self, command: str, *, timeout: int | None = None):
        effective = self.command_timeout if not timeout or timeout < 0 else min(timeout, self.command_timeout)
        return await super().aexecute(command, timeout=effective)


@contextmanager
def sandbox_backend(*, snapshot_id: str | None = None, allowed_hosts: tuple[str, ...] | None = None,
                    command_timeout: int = 120, event=None) -> Iterator[LangSmithSandbox]:
    """Own one sandbox for a run, including cleanup after errors or Ctrl+C."""
    name = f"finance-{uuid4().hex[:12]}"
    def record(kind, **details):
        if event:
            event(kind, sandbox=name, **details)
    with SandboxClient() as client:
        print(f"Creating LangSmith sandbox: {name}")
        if snapshot_id:
            print(f"Sandbox snapshot: {snapshot_id}")
        retain_for_recovery = False
        try:
            # Keep the requested name for cleanup even if create/wait fails.
            client.create_sandbox(
                snapshot_id=snapshot_id, name=name, wait_for_ready=False,
                vcpus=SANDBOX_VCPUS, mem_bytes=SANDBOX_MEMORY_BYTES,
                idle_ttl_seconds=SANDBOX_IDLE_TTL_SECONDS,
                delete_after_stop_seconds=SANDBOX_DELETE_AFTER_STOP_SECONDS,
                proxy_config={"access_control": {"allow_list": list(allowed_hosts)}} if allowed_hosts else None,
            )
            record("sandbox_created", snapshot_id=snapshot_id, allowed_hosts=allowed_hosts)
            sandbox = client.wait_for_sandbox(name, timeout=60)
            ram = (
                f"{sandbox.mem_bytes / 1024**3:.2f} GiB RAM"
                if sandbox.mem_bytes is not None
                else "RAM allocation not returned"
            )
            storage = (
                f"{sandbox.fs_capacity_bytes / 1024**3:.2f} GiB storage"
                if sandbox.fs_capacity_bytes is not None
                else "storage allocation not returned"
            )
            print(f"Sandbox ready: {name} | {sandbox.vcpus} vCPU | {ram} | {storage}")
            backend = BoundedSandbox(sandbox=sandbox, command_timeout=command_timeout)
            preparation = backend.execute(
                f"mkdir -p {SANDBOX_WORKSPACE}",
                timeout=30,
            )
            if preparation.exit_code != 0:
                raise RuntimeError("Could not prepare the sandbox's /workspace directory.")
            baseline = upload_workspace(sandbox)
            record("workspace_uploaded", files=baseline)
            try:
                yield backend
            finally:
                try:
                    summary = download_workspace(sandbox, name, baseline)
                    record("workspace_downloaded", transfers=summary)
                except BaseException as exc:
                    # Do not knowingly delete the only copy after a failed export.
                    retain_for_recovery = True
                    record("sandbox_retained", reason=type(exc).__name__)
                    raise RuntimeError(
                        f"Could not preserve all outputs from sandbox {name}. "
                        "It was left available for recovery in LangSmith; the idle-stop "
                        "and automatic deletion timers still apply. Local downloads "
                        "may be incomplete."
                    ) from exc
        finally:
            if retain_for_recovery:
                print(f"Sandbox retained after download failure: {name}")
            else:
                try:
                    client.delete_sandbox(name)
                    record("sandbox_deletion_requested")
                except ResourceNotFoundError:
                    print(f"Sandbox already deleted: {name}")
                except Exception as exc:
                    raise RuntimeError(
                        f"Could not delete sandbox {name}. Check it in LangSmith "
                        "and delete it manually."
                    ) from exc
                else:
                    print(f"Sandbox deletion requested: {name}")
