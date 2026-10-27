"""Bounded live TEST-03/04/06 probe; no model calls or non-synthetic inputs.

Run from the project root with:
    uv run --locked python scripts/probe_evaluation_boundaries.py

Creates one isolated sandbox from the frozen Excel profile snapshot. A child
process intentionally exits after a known synthetic remote write to exercise
recovery after loss of local process state. All probe evidence stays in .state.
"""

import argparse
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
from unittest.mock import patch
from uuid import uuid4

from langsmith.sandbox import ResourceNotFoundError

from accounting_finance_agent.config import EXCEL_PROFILE, PROJECT_ROOT, load_settings
from accounting_finance_agent.provider import sandbox_client
from accounting_finance_agent.sandbox import (
    SANDBOX_DELETE_AFTER_STOP_SECONDS,
    SANDBOX_IDLE_TTL_SECONDS,
    SANDBOX_MEMORY_BYTES,
    SANDBOX_VCPUS,
    BoundedSandbox,
)
from accounting_finance_agent.worklog import thread_lease
from accounting_finance_agent.workspace import download_workspace, upload_workspace


PROBE_OUTPUT = b"synthetic boundary probe: known recoverable side effect\n"
PROBE_SCRIPT = r'''
import json, socket, subprocess

def attempt(fn):
    try:
        return {"result": fn()}
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)[:240]}

def dns():
    return socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)[0][4][0]

def direct_ip():
    sock = socket.socket(); sock.settimeout(2)
    try:
        sock.connect(("1.1.1.1", 443))
        return "connected"
    finally:
        sock.close()

def reentry():
    import ctypes, errno, os
    libc = ctypes.CDLL(None, use_errno=True)
    fd = os.open("/proc/1/ns/net", os.O_RDONLY)
    try:
        # From the isolated net namespace, try to join the sandbox's original
        # namespace (PID 1), which would restore its prior network view.
        if libc.setns(fd, 0x40000000) == 0:  # CLONE_NEWNET
            return {"joined_original_namespace": True}
        error = ctypes.get_errno()
        return {"joined_original_namespace": False, "errno": error,
                "error": os.strerror(error), "permission_denied": error in (errno.EPERM, errno.EACCES)}
    finally:
        os.close(fd)

import os
print(json.dumps({
    "sandbox_openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
    "sandbox_langsmith_key_present": bool(os.getenv("LANGSMITH_API_KEY")),
    "dns": attempt(dns),
    "direct_ip": attempt(direct_ip),
    "namespace_reentry": attempt(reentry),
}))
'''


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def child_create_and_exit(root: Path, metadata_path: Path, sandbox_name: str, thread_id: str) -> None:
    """Create, probe, perform known writes, persist recovery data, then os._exit."""
    from accounting_finance_agent import workspace

    settings = load_settings(profile=EXCEL_PROFILE)
    source_bytes = b"synthetic protected source v1\n"
    source = root / "source.csv"
    root.mkdir(parents=True, exist_ok=True)
    source.write_bytes(source_bytes)
    provisional = {
        "sandbox_name": sandbox_name,
        "thread_id": thread_id,
        "snapshot_id": settings.sandbox_snapshot_id,
        "profile": settings.profile,
        "model": settings.model,
        "reasoning_effort": settings.reasoning_effort,
        "service_tier": settings.service_tier,
        "tracing_enabled": settings.tracing_enabled,
        "host_openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "host_langsmith_key_present": bool(os.getenv("LANGSMITH_API_KEY")),
        "limits": {
            "model_calls": settings.max_model_calls,
            "tool_calls": settings.max_tool_calls,
            "run_seconds": settings.run_seconds,
            "model_timeout_seconds": settings.model_timeout_seconds,
            "tool_timeout_seconds": settings.tool_timeout_seconds,
            "sandbox_vcpus_requested": SANDBOX_VCPUS,
            "sandbox_memory_bytes_requested": SANDBOX_MEMORY_BYTES,
            "sandbox_idle_ttl_seconds": SANDBOX_IDLE_TTL_SECONDS,
            "sandbox_delete_after_stop_seconds": SANDBOX_DELETE_AFTER_STOP_SECONDS,
            "proxy_policy": "deny all destinations",
        },
    }
    provisional.update({"sandbox_state": "creating", "side_effect_state": "not_started"})
    write_json(metadata_path, provisional)
    with patch.object(workspace, "LOCAL_WORKSPACE", root):
        with sandbox_client(timeout=20, max_retries=0) as client:
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
            provisional["sandbox_state"] = "created"
            write_json(metadata_path, provisional)
            sandbox = client.wait_for_sandbox(sandbox_name, timeout=60)
            provisional["sandbox_state"] = "ready"
            provisional["actual_sandbox"] = {
                "name": sandbox_name,
                "id": getattr(sandbox, "id", None),
                "vcpus": getattr(sandbox, "vcpus", None),
                "mem_bytes": getattr(sandbox, "mem_bytes", None),
                "fs_capacity_bytes": getattr(sandbox, "fs_capacity_bytes", None),
            }
            write_json(metadata_path, provisional)
            remote = BoundedSandbox(sandbox=sandbox, command_timeout=settings.tool_timeout_seconds,
                                    network_isolated=True)
            uploaded = upload_workspace(sandbox)
            provisional.update({
                "uploaded_baseline": uploaded,
                "source_sha256": sha256(source_bytes).hexdigest(),
                "expected_output_sha256": sha256(PROBE_OUTPUT).hexdigest(),
                "side_effect_state": "not_started",
            })
            write_json(metadata_path, provisional)
            network = remote.execute("python3 -c " + shlex.quote(PROBE_SCRIPT), timeout=15)
            if network.exit_code != 0:
                raise RuntimeError(f"Network probe failed to run: {network.output[:400]}")
            # A deterministic, known effect is written before local process loss.
            command = "from pathlib import Path; Path('/workspace/probe-output.txt').write_bytes(" + repr(PROBE_OUTPUT) + "); Path('/workspace/source.csv').write_bytes(b'synthetic protected source changed\\n')"
            provisional["side_effect_state"] = "possibly_started"
            write_json(metadata_path, provisional)
            side_effect = remote.execute("python3 -c " + shlex.quote(command), timeout=15)
            if side_effect.exit_code != 0:
                raise RuntimeError(f"Synthetic side effect failed: {side_effect.output[:400]}")
            actual = {
                **provisional,
                "actual_sandbox": {
                    "name": sandbox_name,
                    "id": getattr(sandbox, "id", None),
                    "vcpus": getattr(sandbox, "vcpus", None),
                    "mem_bytes": getattr(sandbox, "mem_bytes", None),
                    "fs_capacity_bytes": getattr(sandbox, "fs_capacity_bytes", None),
                },
                "uploaded_baseline": uploaded,
                "source_sha256": sha256(source_bytes).hexdigest(),
                "expected_output_sha256": sha256(PROBE_OUTPUT).hexdigest(),
                "network_probe": json.loads(network.output.strip()),
                "remote_side_effect_exit_code": side_effect.exit_code,
                "side_effect_state": "completed",
                "sandbox_state": "ready",
                "abrupt_local_exit_after_remote_side_effect": True,
            }
            write_json(metadata_path, actual)
            # Intentionally skips Python finally/context cleanup after known output
            # and recovery metadata have both been durably written.
            os._exit(0)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(f"FAIL: {label}")
    print(f"PASS: {label}")


def confirm_deleted(client, sandbox_name: str, timeout: int = 60) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            status = client.get_sandbox_status(sandbox_name).status
        except ResourceNotFoundError:
            print(f"PASS: sandbox deletion confirmed by API: {sandbox_name}")
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Sandbox deletion not confirmed; last status={status}")
        time.sleep(2)


def recover_or_cleanup_failed_child(metadata_path: Path, workspace_root: Path, reason: str,
                                    *, client_factory=sandbox_client) -> dict:
    """Recover only the sandbox named in durable probe metadata, or retain it visibly."""
    try:
        evidence = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        evidence = {"metadata_read_error": type(exc).__name__}
    sandbox_name = evidence.get("sandbox_name")
    result = {"reason": reason, "sandbox_name": sandbox_name}
    if not sandbox_name:
        result.update(status="manual_recovery_required", reason_detail="no recorded sandbox identity")
    else:
        try:
            with patch("accounting_finance_agent.workspace.LOCAL_WORKSPACE", workspace_root):
                with client_factory(timeout=20, max_retries=0) as client:
                    try:
                        sandbox = client.get_sandbox(sandbox_name)
                    except ResourceNotFoundError:
                        result["status"] = "sandbox_already_absent"
                    else:
                        baseline = evidence.get("uploaded_baseline")
                        if not isinstance(baseline, dict):
                            result.update(status="retained_for_recovery",
                                          reason_detail="upload baseline was not durably recorded")
                        else:
                            try:
                                summary = download_workspace(
                                    sandbox, sandbox_name + "-failure-recovery", baseline,
                                    protected=tuple(name for name in baseline
                                                    if name in {"source.csv", "notes.json", "task.txt"}),
                                )
                                result["recovered_remote_files"] = summary.get("remote_files", {})
                            except Exception as exc:
                                result.update(status="retained_for_recovery",
                                              reason_detail="workspace export failed",
                                              export_error_type=type(exc).__name__)
                            else:
                                client.delete_sandbox(sandbox_name)
                                confirm_deleted(client, sandbox_name)
                                result["status"] = "recovered_and_deleted"
                    if result.get("status") == "sandbox_already_absent":
                        pass
        except Exception as exc:
            result.update(status="retained_for_recovery",
                          cleanup_error_type=type(exc).__name__)
    if result.get("status") == "retained_for_recovery":
        result["manual_action"] = (
            "Inspect the recorded sandbox in LangSmith and recover its /workspace "
            "before deleting it. This record names only this probe's sandbox."
        )
    evidence["child_failure_handling"] = result
    write_json(metadata_path, evidence)
    if result["status"] in {"recovered_and_deleted", "sandbox_already_absent"}:
        print(f"Child failure handled: {result['status']} ({sandbox_name})")
    else:
        print(f"Child failure retained for recovery: {metadata_path}")
    return result


def run_child_process(command: list[str], metadata_path: Path, workspace_root: Path,
                      *, timeout: int = 180, failure_handler=recover_or_cleanup_failed_child,
                      runner=subprocess.run):
    """Launch the child and make timeout/nonzero exits enter recovery handling."""
    try:
        child = runner(command, cwd=PROJECT_ROOT, capture_output=True, text=True,
                       timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        failure_handler(metadata_path, workspace_root, "child process timed out")
        raise RuntimeError(f"Probe child timed out; recovery handling recorded at {metadata_path}") from exc
    if child.returncode != 0:
        safe_error = (child.stderr or "")[-1500:]
        failure_handler(metadata_path, workspace_root, f"child exited {child.returncode}")
        raise RuntimeError(f"Probe child failed ({child.returncode}): {safe_error}")
    return child


def parent_run() -> None:
    settings = load_settings(profile=EXCEL_PROFILE)
    if not settings.sandbox_snapshot_id:
        raise RuntimeError("The Excel profile did not select a frozen snapshot.")
    probe_id = uuid4().hex[:12]
    base = PROJECT_ROOT / ".state" / "live-boundaries" / probe_id
    workspace_root = base / "workspace"
    metadata_path = base / "recovery.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=False)
    sandbox_name = f"finance-probe-{uuid4().hex[:12]}"
    thread_id = str(uuid4())
    write_json(metadata_path, {
        "sandbox_name": sandbox_name,
        "thread_id": thread_id,
        "snapshot_id": settings.sandbox_snapshot_id,
        "profile": settings.profile,
        "sandbox_state": "not_created",
        "side_effect_state": "not_started",
    })
    command = [sys.executable, str(Path(__file__).resolve()), "--child",
               str(workspace_root), str(metadata_path), sandbox_name, thread_id]
    child = run_child_process(command, metadata_path, workspace_root)
    # The child intentionally exits via os._exit; captured stdout is not required.
    if child.returncode != 0 or not metadata_path.exists():
        safe_error = (child.stderr or "")[-1500:]
        raise RuntimeError(f"Probe child failed ({child.returncode}): {safe_error}")
    evidence = json.loads(metadata_path.read_text(encoding="utf-8"))
    sandbox_name = evidence["sandbox_name"]
    baseline = evidence["uploaded_baseline"]
    thread_id = evidence["thread_id"]
    failures = []
    deletion_confirmed = False
    try:
        with patch("accounting_finance_agent.workspace.LOCAL_WORKSPACE", workspace_root):
            with sandbox_client(timeout=20, max_retries=0) as client:
                sandbox = client.get_sandbox(sandbox_name)
                source_path = workspace_root / "source.csv"
                try:
                    download_workspace(sandbox, sandbox_name + "-changed-source", baseline,
                                       protected=("source.csv",))
                except RuntimeError as exc:
                    check("Protected source files changed" in str(exc),
                          "real sandbox source mutation detected")
                else:
                    failures.append("changed protected source was not detected")
                check(source_path.read_bytes() == b"synthetic protected source v1\n",
                      "host source preserved after changed-source check")
                output_path = workspace_root / "probe-output.txt"
                check(output_path.exists() and sha256(output_path.read_bytes()).hexdigest()
                      == evidence["expected_output_sha256"],
                      "known synthetic remote output transferred despite source error")

                missing = sandbox.run("rm -f /workspace/source.csv", timeout=10)
                check(missing.exit_code == 0, "remote source removal command completed")
                try:
                    download_workspace(sandbox, sandbox_name + "-missing-source", baseline,
                                       protected=("source.csv",))
                except RuntimeError as exc:
                    check("changed or disappeared" in str(exc), "real missing source detected")
                else:
                    failures.append("missing protected source was not detected")
                check(source_path.read_bytes() == b"synthetic protected source v1\n",
                      "host source preserved after missing-source check")

                restore = sandbox.write("/workspace/source.csv", b"synthetic protected source v1\n")
                del restore
                recovery = download_workspace(sandbox, sandbox_name + "-abrupt-recovery", baseline,
                                              protected=("source.csv",))
                output_bytes = output_path.read_bytes()
                check(sha256(output_bytes).hexdigest() == evidence["expected_output_sha256"],
                      "abrupt-exit output recovered with expected SHA-256")
                check(recovery["remote_files"].get("probe-output.txt") == evidence["expected_output_sha256"],
                      "existing download machinery confirms the recovered remote output digest")
                with thread_lease(thread_id):
                    try:
                        with thread_lease(thread_id):
                            failures.append("overlapping same-thread lease unexpectedly acquired")
                    except ValueError as exc:
                        check("run lock" in str(exc), "same-thread overlapping execution rejected")
                reentry = evidence["network_probe"]["namespace_reentry"]
                denied = reentry.get("error") is not None or reentry.get("result", {}).get("permission_denied") is True
                check(denied, "re-entry into the sandbox's original network namespace denied")
                if not denied:
                    failures.append("re-entry into original network namespace was not denied")
                client.delete_sandbox(sandbox_name)
                confirm_deleted(client, sandbox_name)
                deletion_confirmed = True
    finally:
        if not deletion_confirmed:
            try:
                with sandbox_client(timeout=20, max_retries=0) as cleanup_client:
                    cleanup_client.delete_sandbox(sandbox_name)
                    confirm_deleted(cleanup_client, sandbox_name)
                    deletion_confirmed = True
            except ResourceNotFoundError:
                deletion_confirmed = True
            except Exception as exc:
                evidence["cleanup_error_type"] = type(exc).__name__
        evidence["checks_failed"] = failures
        evidence["sandbox_deletion_confirmed"] = deletion_confirmed
        evidence["probe_workspace"] = str(workspace_root)
        evidence["child_exit_code"] = child.returncode
        evidence["live_checks"] = {
            "network_namespace_dns_direct_ip_reentry": evidence.get("network_probe"),
            "changed_source_detected": not any("changed protected source" in item for item in failures),
            "missing_source_detected": not any("missing protected source" in item for item in failures),
            "abrupt_process_exit_recovery": not any("abrupt" in item for item in failures),
            "same_thread_overlap_rejected": not any("overlapping" in item for item in failures),
        }
        write_json(metadata_path, evidence)
        summary_path = base / "assessment.json"
        write_json(summary_path, evidence)
        print(f"Evidence: {summary_path}")
    if failures:
        raise RuntimeError("Probe completed with failed checks: " + "; ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=4, metavar=("WORKSPACE", "METADATA", "SANDBOX", "THREAD"))
    args = parser.parse_args()
    if args.child:
        child_create_and_exit(Path(args.child[0]), Path(args.child[1]), args.child[2], args.child[3])
    parent_run()


if __name__ == "__main__":
    main()
