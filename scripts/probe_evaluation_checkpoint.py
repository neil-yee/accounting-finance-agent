"""Live checkpoint deletion/recreation regression; never invokes a model.

Do not run until ``workspace.advance_baseline`` is available and the live
benchmark series is cleared for this isolated sandbox probe.

Run from the project root with:
    uv run --locked python scripts/probe_evaluation_checkpoint.py
"""

from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import time
from unittest.mock import patch
from uuid import uuid4

from langsmith.sandbox import ResourceNotFoundError

from accounting_finance_agent import workspace
from accounting_finance_agent.config import EXCEL_PROFILE, PROJECT_ROOT, load_settings
from accounting_finance_agent.provider import sandbox_client
from accounting_finance_agent.sandbox import (
    SANDBOX_DELETE_AFTER_STOP_SECONDS,
    SANDBOX_IDLE_TTL_SECONDS,
    SANDBOX_MEMORY_BYTES,
    SANDBOX_VCPUS,
    BoundedSandbox,
)
from accounting_finance_agent.workspace import download_workspace, upload_workspace


V1 = b"synthetic checkpoint output version one\n"
V2 = b"synthetic checkpoint output version two\n"
V3 = b"synthetic checkpoint output version three\n"
HOST_EDIT = b"synthetic reviewer host edit while remote file absent\n"


def check(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(f"FAIL: {label}")
    print(f"PASS: {label}")


def confirm_deleted(client, name: str, timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            status = client.get_sandbox_status(name).status
        except ResourceNotFoundError:
            print(f"PASS: sandbox deletion confirmed by API: {name}")
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Sandbox deletion not confirmed; last status={status}")
        time.sleep(2)


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def main() -> None:
    advance_baseline = getattr(workspace, "advance_baseline", None)
    if not callable(advance_baseline):
        raise SystemExit("Not run: workspace.advance_baseline is not available yet.")

    settings = load_settings(profile=EXCEL_PROFILE, require_sandbox=True)
    if not settings.sandbox_snapshot_id:
        raise SystemExit("Not run: the Excel profile has no frozen snapshot selected.")

    probe_id = uuid4().hex[:12]
    base = PROJECT_ROOT / ".state" / "live-checkpoint" / probe_id
    root = base / "workspace"
    root.mkdir(parents=True, exist_ok=False)
    sandbox_name = f"finance-checkpoint-{probe_id}"
    evidence = {
        "probe_id": probe_id,
        "sandbox_name": sandbox_name,
        "profile": settings.profile,
        "snapshot_id": settings.sandbox_snapshot_id,
        "model_calls": 0,
        "synthetic_only": True,
        "limits": {
            "model_calls": settings.max_model_calls,
            "tool_calls": settings.max_tool_calls,
            "run_seconds": settings.run_seconds,
            "tool_timeout_seconds": settings.tool_timeout_seconds,
            "requested_vcpus": SANDBOX_VCPUS,
            "requested_memory_bytes": SANDBOX_MEMORY_BYTES,
            "idle_ttl_seconds": SANDBOX_IDLE_TTL_SECONDS,
            "delete_after_stop_seconds": SANDBOX_DELETE_AFTER_STOP_SECONDS,
            "proxy_policy": "deny all destinations",
        },
        "host_openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "host_langsmith_key_present": bool(os.getenv("LANGSMITH_API_KEY")),
        "workspace": str(root),
    }
    evidence_path = base / "assessment.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    deleted = False
    sandbox = None
    create_requested = False
    with patch.object(workspace, "LOCAL_WORKSPACE", root):
        try:
            with sandbox_client(timeout=20, max_retries=0) as client:
                create_requested = True
                client.create_sandbox(
                    snapshot_id=settings.sandbox_snapshot_id,
                    name=sandbox_name,
                    wait_for_ready=False,
                    vcpus=SANDBOX_VCPUS,
                    mem_bytes=SANDBOX_MEMORY_BYTES,
                    idle_ttl_seconds=SANDBOX_IDLE_TTL_SECONDS,
                    delete_after_stop_seconds=SANDBOX_DELETE_AFTER_STOP_SECONDS,
                    proxy_config={"access_control": {"deny_list": ["*"]}},
                )
                sandbox = client.wait_for_sandbox(sandbox_name, timeout=60)
                evidence["actual_sandbox"] = {
                    "name": sandbox_name,
                    "id": getattr(sandbox, "id", None),
                    "vcpus": getattr(sandbox, "vcpus", None),
                    "mem_bytes": getattr(sandbox, "mem_bytes", None),
                    "fs_capacity_bytes": getattr(sandbox, "fs_capacity_bytes", None),
                }
                backend = BoundedSandbox(sandbox=sandbox,
                                         command_timeout=settings.tool_timeout_seconds,
                                         network_isolated=True)
                prepared = backend.execute("mkdir -p /workspace", timeout=10)
                check(prepared.exit_code == 0,
                      f"sandbox workspace prepared: {getattr(prepared, 'output', '')[:300]}")
                baseline = upload_workspace(sandbox)

                def remote_write(content: bytes) -> None:
                    command = "from pathlib import Path; Path('/workspace/deliverable.txt').write_bytes(" + repr(content) + ")"
                    result = backend.execute("python3 -c " + shlex.quote(command), timeout=10)
                    check(result.exit_code == 0,
                          f"remote write {digest(content)[:12]} completed: {getattr(result, 'output', '')[:300]}")

                def remote_delete() -> None:
                    result = backend.execute("rm -f /workspace/deliverable.txt", timeout=10)
                    check(result.exit_code == 0, "remote deliverable deletion completed")

                # Create and export v1. Baseline advances only through the
                # production helper under evaluation.
                remote_write(V1)
                first = download_workspace(sandbox, sandbox_name + "-v1", baseline)
                check((root / "deliverable.txt").read_bytes() == V1,
                      "generated v1 exported to host")
                check(first["changed_files"].get("deliverable.txt") == digest(V1),
                      "v1 export digest recorded")
                baseline = advance_baseline(baseline, first["remote_files"])

                # Delete and checkpoint; the host v1 remains and the helper
                # must retain its last-known baseline digest.
                remote_delete()
                absent = download_workspace(sandbox, sandbox_name + "-deleted", baseline)
                check("deliverable.txt" not in absent["remote_files"],
                      "checkpoint listing observes remote deletion")
                check((root / "deliverable.txt").read_bytes() == V1,
                      "remote deletion preserves local v1")
                baseline = advance_baseline(baseline, absent["remote_files"])

                # Recreate the same remote path. An unchanged host v1 is not a
                # competing edit: v2 replaces it and v1 is preserved in history.
                remote_write(V2)
                second = download_workspace(sandbox, sandbox_name + "-v2", baseline)
                check((root / "deliverable.txt").read_bytes() == V2,
                      "regenerated v2 replaces untouched host v1")
                check(not second["conflict_files"], "v2 recreation creates no spurious conflict")
                check((root / ".versions" / (sandbox_name + "-v2") / "deliverable.txt").read_bytes() == V1,
                      "replaced v1 preserved in versions")
                baseline = advance_baseline(baseline, second["remote_files"])

                # Delete/checkpoint once more; then make a real host edit while
                # absent. Regenerated remote v3 belongs in conflicts.
                remote_delete()
                absent_again = download_workspace(sandbox, sandbox_name + "-host-edit-delete", baseline)
                baseline = advance_baseline(baseline, absent_again["remote_files"])
                (root / "deliverable.txt").write_bytes(HOST_EDIT)
                remote_write(V3)
                third = download_workspace(sandbox, sandbox_name + "-host-edit", baseline)
                check((root / "deliverable.txt").read_bytes() == HOST_EDIT,
                      "genuine host edit remains local")
                check(third["conflict_files"].get("deliverable.txt") == digest(V3),
                      "incoming v3 is recorded as a conflict")
                check((root / ".conflicts" / (sandbox_name + "-host-edit") / "deliverable.txt").read_bytes() == V3,
                      "incoming v3 bytes preserved in conflicts")
                baseline = advance_baseline(baseline, third["remote_files"])
                evidence["final_baseline"] = baseline
                evidence["results"] = {
                    "v1_sha256": digest(V1),
                    "v2_sha256": digest(V2),
                    "v3_sha256": digest(V3),
                    "host_edit_sha256": digest(HOST_EDIT),
                    "spurious_conflicts_for_v2": second["conflict_files"],
                    "v3_conflicts": third["conflict_files"],
                }
                evidence["status"] = "passed"
        except BaseException as exc:
            evidence["status"] = "failed"
            evidence["error_type"] = type(exc).__name__
            evidence["error"] = str(exc)[:1000]
            raise
        finally:
            if sandbox is not None or create_requested:
                try:
                    # All files are synthetic and known; perform one final export
                    # attempt before deleting if an earlier assertion failed.
                    if sandbox is not None:
                        try:
                            download_workspace(sandbox, sandbox_name + "-cleanup", baseline)
                        except Exception as export_exc:
                            evidence["cleanup_export_error_type"] = type(export_exc).__name__
                    with sandbox_client(timeout=20, max_retries=0) as cleanup_client:
                        cleanup_client.delete_sandbox(sandbox_name)
                        confirm_deleted(cleanup_client, sandbox_name)
                        deleted = True
                except ResourceNotFoundError:
                    deleted = True
                except Exception as cleanup_exc:
                    evidence["cleanup_error_type"] = type(cleanup_exc).__name__
                    evidence["status"] = "cleanup_unconfirmed"
            evidence["sandbox_deletion_confirmed"] = deleted
            evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(f"Evidence: {evidence_path}")


if __name__ == "__main__":
    main()
