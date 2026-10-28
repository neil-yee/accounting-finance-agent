"""Local agent workbench: bounded runs, thread workspaces, logs, and human review."""

import argparse
from contextlib import closing, nullcontext
import getpass
import json
from uuid import uuid4

from accounting_finance_agent.agent import build_agent
from accounting_finance_agent.config import (
    EXCEL_PROFILE, ConfigurationError, Settings, load_settings, require_runnable_profile,
)
from accounting_finance_agent.lifecycle import deadline, archive_run, mark_active
from accounting_finance_agent.provenance import effective_configuration
from accounting_finance_agent.persistence import CHECKPOINT_DATABASE, ThreadHistory, open_history
from accounting_finance_agent.runtime import RunContext, RunControls, RunLimitExceeded
from accounting_finance_agent.sandbox import sandbox_backend
from accounting_finance_agent.worklog import WorkLog, thread_lease
from accounting_finance_agent.workspace import thread_workspace, use_workspace, workspace_manifest
from accounting_finance_agent.validation import validate_artifact


COMMANDS = (
    ":new | :threads | :thread [ID] | :workspace | :state | :runs | :review | "
    ":approve RUN_ID | :reject RUN_ID [reason] | :help | exit"
)


def show_state(settings, history, thread_id):
    graph = build_agent(settings, checkpointer=history.checkpointer)
    snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
    values = snapshot.values or {}
    print(f"Thread: {thread_id}\nState keys: {', '.join(sorted(values)) or '(empty)'}")
    print(f"Messages: {len(values.get('messages', []))}; pending nodes: {snapshot.next}")
    for todo in values.get("todos", []):
        print(f"  [{todo.get('status', '?')}] {todo.get('content', '')}")


def run_prompt(settings, history, log, thread_id, prompt, *, sandbox):
    require_runnable_profile(settings)
    if not sandbox:
        raise ConfigurationError("Agent runs require a sandbox.")
    run_id = str(uuid4())
    path = thread_workspace(thread_id)
    from accounting_finance_agent.staging import stage_approved_helpers
    stage_approved_helpers(settings, path)
    context = RunContext(run_id, thread_id, settings.timezone, str(path))
    controls = RunControls(settings, context, log)
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 300,
              "run_id": run_id, "metadata": {"app_run_id": run_id, "work_thread_id": thread_id}}
    inputs = {"messages": [{"role": "user", "content": prompt}]}
    print(f"Run: {run_id}")
    with thread_lease(thread_id), use_workspace(path):
        mark_active(thread_id)
        before = workspace_manifest()
        log.start(run_id, thread_id, {"workspace": str(path), "snapshot": settings.sandbox_snapshot_id,
                  "timezone": settings.timezone, "model": settings.model,
                  "configuration": effective_configuration(settings)}, before)
        status, error_type = "failed", None
        try:
            scope = sandbox_backend(
                snapshot_id=settings.sandbox_snapshot_id,
                allowed_hosts=settings.sandbox_allowed_hosts,
                command_timeout=settings.tool_timeout_seconds,
                event=lambda kind, **details: log.event(run_id, kind, **details),
                **({"controls": controls} if settings.profile == EXCEL_PROFILE else {}),
            )
            with (deadline(controls.remaining()) if settings.profile == EXCEL_PROFILE else nullcontext()), scope as backend:
                agent = build_agent(settings, backend=backend, checkpointer=history.checkpointer, controls=controls)
                latest = None
                for event_type, payload in agent.stream(
                    inputs, config=config, context=context, stream_mode=["updates", "values"]
                ):
                    if event_type == "values":
                        latest = payload
                    else:
                        for update in payload.values():
                            if isinstance(update, dict) and "todos" in update:
                                print("[Plan] " + " | ".join(
                                    f"{item.get('status')}: {item.get('content')}" for item in update["todos"]
                                ), flush=True)
                if not latest or not latest.get("messages"):
                    raise RuntimeError("Run finished without messages; inspect :state before continuing.")
                final = latest["messages"][-1]
                if final.type != "ai" or getattr(final, "tool_calls", None):
                    raise RuntimeError("Run has unfinished tool work; inspect :state before continuing.")
                response_metadata = getattr(final, "response_metadata", {}) or {}
                response_status = response_metadata.get("status")
                if response_status and response_status != "completed":
                    details = response_metadata.get("incomplete_details") or {}
                    reason = details.get("reason") if isinstance(details, dict) else None
                    log.event(run_id, "incomplete_model_response", status=response_status, reason=reason)
                    suffix = f" ({reason})" if reason else ""
                    raise RuntimeError(
                        f"Model response status was {response_status}{suffix}; assignment is incomplete."
                    )
                answer = final.text
                if not answer.strip():
                    raise RuntimeError("Model returned no visible answer; assignment is incomplete.")
            after_transfer = workspace_manifest()
            reports = [validate_artifact(path / relative) for relative, digest in after_transfer.items()
                       if digest != before.get(relative) and (path / relative).suffix.lower() in
                       {".xlsx", ".docx", ".pptx", ".csv", ".json"}]
            log.event(run_id, "artifact_structure_checks", reports=reports)
            print(f"[Structure checks] {len(reports)} files; {sum(len(r['warnings']) for r in reports)} warnings. Not financial or visual sign-off.")
            if any(report["errors"] for report in reports):
                raise ValueError("Generated files failed structural checks. Inspect the work log and revise before approval.")
            if settings.profile == EXCEL_PROFILE:
                from accounting_finance_agent.spreadsheets import validate_delivery
                with deadline(controls.remaining()):
                    result = validate_delivery(path)
                log.event(run_id, "benchmark_delivery_checks", report=result)
                if result['errors']:
                    raise ValueError("Workbook acceptance blocked: " + '; '.join(result['errors']))
            status = "needs_review"
            print(f"\nAgent: {answer}\nRun saved for review: {run_id}")
        except BaseException as exc:
            error_type = type(exc).__name__
            cause = exc
            while cause.__cause__ is not None:
                cause = cause.__cause__
            status = "limited" if isinstance(cause, RunLimitExceeded) else "failed"
            log.event(run_id, "recovery_boundary", status=status,
                      note="Only confirmed workspace exports are durable; in-flight changes/effects may be unknown.")
            raise
        finally:
            try:
                after = workspace_manifest()
            except Exception as exc:
                after = {}
                status = "failed"
                error_type = type(exc).__name__
            log.event(run_id, "run_counts", **controls.counts)
            log.finish(run_id, status, after, error_type)
            if hasattr(controls, 'api_client'):
                controls.api_client.close()
            if settings.profile == EXCEL_PROFILE:
                try:
                    from time import monotonic
                    with deadline(max(.001, getattr(controls, "cleanup_until", monotonic() + 60) - monotonic())):
                        archive = archive_run(run_id, path)
                    log.event(run_id, 'backup_saved', path=str(archive))
                except Exception as exc:
                    log.event(run_id, 'backup_failed', error=type(exc).__name__)
                    log.finish(run_id, 'failed', after, type(exc).__name__)
                    raise


def chat(settings: Settings, history: ThreadHistory, *, thread_id: str, log=None) -> None:
    print(f"Current thread: {thread_id}")
    print(f"Thread workspace: {thread_workspace(thread_id)}")
    print(COMMANDS)
    while True:
        prompt = input("\nYou: ").strip()
        if prompt.lower() in {"exit", "quit"}:
            return
        if not prompt:
            continue
        try:
            if prompt == ":help":
                print(COMMANDS)
            elif prompt == ":new":
                thread_id = history.new().id
                print(f"New thread: {thread_id}")
                print(f"New separate workspace: {thread_workspace(thread_id)}")
            elif prompt == ":threads":
                for thread in history.list():
                    print(f"{'*' if thread.id == thread_id else ' '} {thread.id} | {thread.title or '(empty conversation)'}")
            elif prompt == ":thread":
                print(f"Current thread: {thread_id}")
            elif prompt.startswith(":thread "):
                thread_id = history.select(prompt.split(maxsplit=1)[1].strip()).id
                print(f"Resumed thread: {thread_id}")
                print(f"Workspace: {thread_workspace(thread_id)}")
            elif prompt == ":workspace":
                print(thread_workspace(thread_id))
            elif prompt == ":state":
                show_state(settings, history, thread_id)
            elif prompt in {":runs", ":review"}:
                with use_workspace(thread_workspace(thread_id)):
                    manifest = workspace_manifest()
                for run in log.runs(thread_id):
                    print(f"{run['id']} | {run['status']} | {log.review_status(run['id'], manifest)} | {run['started']}")
            elif prompt.startswith((":approve ", ":reject ")):
                parts = prompt.split(maxsplit=2)
                decision = "approved" if parts[0] == ":approve" else "rejected"
                with use_workspace(thread_workspace(thread_id)):
                    manifest = workspace_manifest()
                log.review(parts[1], thread_id, decision, manifest, getpass.getuser(), parts[2] if len(parts) > 2 else "")
                print(f"Recorded {decision} for exact run {parts[1]}. No reusable assets were promoted.")
            elif prompt.startswith(":"):
                print(f"Unknown command. {COMMANDS}")
            else:
                history.record_prompt(history.select(thread_id), prompt)
                run_prompt(settings, history, log, thread_id, prompt, sandbox=True)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
            print("No task was automatically replayed. Inspect :state, :runs, and the workspace before continuing.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the accounting and finance agent.")
    # Keep existing launch commands working; all runs now use a sandbox.
    parser.add_argument("--sandbox", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--profile", choices=["local", EXCEL_PROFILE], default="local",
                        help="Select local settings or the fixed Excel benchmark baseline.")
    parser.add_argument("--show-config", action="store_true",
                        help="Print secret-free configuration without running a model or sandbox.")
    parser.add_argument("--thread", metavar="ID", help="Resume an existing conversation.")
    args = parser.parse_args()
    try:
        settings = load_settings(require_sandbox=True, profile=args.profile,
                                 validate_credentials=not args.show_config)
        if args.show_config:
            print(json.dumps(effective_configuration(settings), indent=2, sort_keys=True))
            return
        require_runnable_profile(settings)
    except ConfigurationError as exc:
        parser.error(str(exc))
    print(f"Deep Agent | Profile: {settings.profile} | Model: {settings.model} | Timezone: {settings.timezone}")
    print(f"Conversation state: {CHECKPOINT_DATABASE}")
    print(f"Limits per run: {settings.max_model_calls} model calls, {settings.max_tool_calls} tool calls, {settings.run_seconds}s admission deadline")
    print(f"Sandbox environment: {settings.sandbox_snapshot_id or 'LangSmith default'}")
    print("Each thread has its own workspace; use :workspace to see where to put files.")
    print("Existing files at workspace/ are untouched; copy needed files into the thread folder.")
    print("Sandbox HTTPS allowlist: " + ", ".join(settings.sandbox_allowed_hosts))
    try:
        with open_history(mode="sandbox") as history, closing(WorkLog()) as log:
            try:
                thread = history.initial(args.thread)
            except ValueError as exc:
                parser.error(str(exc))
            chat(settings, history, thread_id=thread.id, log=log)
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. Your thread can be resumed next time.")


if __name__ == "__main__":
    main()
