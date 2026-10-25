"""Create a temporary LangSmith execution backend and explicitly delete it."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4
from contextlib import nullcontext
from time import monotonic
from accounting_finance_agent.lifecycle import deadline
import shlex

from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import ResourceNotFoundError, SandboxClient

from accounting_finance_agent.provider import sandbox_client
from accounting_finance_agent.workspace import download_workspace, upload_workspace, workspace_root

# Explicit small allocation, not a claim about the provider's minimum size.
SANDBOX_VCPUS = 1
SANDBOX_MEMORY_BYTES = 2 * 1024**3
SANDBOX_IDLE_TTL_SECONDS = 300
SANDBOX_DELETE_AFTER_STOP_SECONDS = 600
SANDBOX_WORKSPACE = "/workspace"


class BoundedSandbox(LangSmithSandbox):
    def __init__(self, *, sandbox, command_timeout: int, network_isolated: bool = False):
        super().__init__(sandbox=sandbox)
        self.command_timeout = command_timeout
        self.network_isolated = network_isolated

    def execute(self, command: str, *, timeout: int | None = None):
        effective = self.command_timeout if not timeout or timeout < 0 else min(timeout, self.command_timeout)
        if self.network_isolated:
            command = "unshare --user --map-root-user --net -- sh -c " + shlex.quote(command)
        return super().execute(command, timeout=effective)

    async def aexecute(self, command: str, *, timeout: int | None = None):
        effective = self.command_timeout if not timeout or timeout < 0 else min(timeout, self.command_timeout)
        if self.network_isolated:
            command = "unshare --user --map-root-user --net -- sh -c " + shlex.quote(command)
        return await super().aexecute(command, timeout=effective)


@contextmanager
def sandbox_backend(*, snapshot_id: str | None = None, allowed_hosts: tuple[str, ...] | None = None,
                    command_timeout: int = 120, event=None, controls=None) -> Iterator[LangSmithSandbox]:
    """Own one sandbox for a run, including cleanup after errors or Ctrl+C."""
    name = f"finance-{uuid4().hex[:12]}"
    def record(kind, **details):
        if event:
            event(kind, sandbox=name, **details)
    with (sandbox_client() if controls else SandboxClient()) as client:
        print(f"Creating LangSmith sandbox: {name}")
        if snapshot_id:
            print(f"Sandbox snapshot: {snapshot_id}")
        retain_for_recovery = False
        cleanup_until = None
        try:
            # Keep the requested name for cleanup even if create/wait fails.
            client.create_sandbox(
                snapshot_id=snapshot_id, name=name, wait_for_ready=False,
                vcpus=SANDBOX_VCPUS, mem_bytes=SANDBOX_MEMORY_BYTES,
                idle_ttl_seconds=SANDBOX_IDLE_TTL_SECONDS,
                delete_after_stop_seconds=SANDBOX_DELETE_AFTER_STOP_SECONDS,
                proxy_config={"access_control": {"allow_list": list(allowed_hosts)}} if allowed_hosts else ({"access_control": {"deny_list": ["*"]}} if controls else None),
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
            backend = BoundedSandbox(sandbox=sandbox, command_timeout=command_timeout, network_isolated=bool(controls))
            preparation = backend.execute(
                f"mkdir -p {SANDBOX_WORKSPACE}",
                timeout=30,
            )
            if preparation.exit_code != 0:
                raise RuntimeError("Could not prepare the sandbox's /workspace directory.")
            baseline = upload_workspace(sandbox)
            protected = tuple(name for name in baseline if name in {'source.csv', 'notes.json', 'task.txt'}) if controls else ()
            transferred_bytes = 0
            def preserve():
                nonlocal baseline, transferred_bytes
                summary = download_workspace(sandbox, name + '-checkpoint', baseline, protected=protected)
                transferred_bytes += sum((workspace_root()/name).stat().st_size for name in summary['changed_files'])
                if transferred_bytes > 50 * 1024**2:
                    raise RuntimeError('Run export allowance exhausted; inspect preserved local files.')
                baseline = summary['remote_files']
                record('workspace_checkpoint', transfers=summary)
            if controls:
                controls.preserve = preserve
                inventory = backend.execute("python3 -c " + shlex.quote("import json,sys,openpyxl; print(json.dumps(dict(python=sys.version,openpyxl=openpyxl.__version__)))") + "; libreoffice --version", timeout=30)
                record('sandbox_inventory', output=inventory.output if hasattr(inventory, 'output') else str(inventory))
            record("workspace_uploaded", files=baseline)
            try:
                yield backend
            finally:
                try:
                    cleanup_until = monotonic() + 60
                    if controls:
                        controls.cleanup_until = cleanup_until
                    with (deadline(60) if controls else nullcontext()):
                        summary = download_workspace(sandbox, name, baseline, protected=protected)
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
            if controls and not getattr(controls, "cleanup_until", None):
                controls.cleanup_until = monotonic() + 60
            if retain_for_recovery:
                print(f"Sandbox retained after download failure: {name}")
            else:
                try:
                    with (deadline(max(.001, (cleanup_until or monotonic() + 60) - monotonic())) if controls else nullcontext()):
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
