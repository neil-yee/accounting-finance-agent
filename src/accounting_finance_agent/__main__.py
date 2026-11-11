"""Local agent workbench: bounded runs, thread workspaces, logs, and human review."""

import argparse
from contextlib import closing, nullcontext
import getpass
import json
from uuid import uuid4
from langgraph.types import Command

from accounting_finance_agent.agent import build_agent
from accounting_finance_agent.config import (
    COLLAB_PROFILE, EXCEL_PROFILE, ConfigurationError, Settings, load_settings, require_runnable_profile,
)
from accounting_finance_agent.lifecycle import deadline, archive_run, mark_active
from accounting_finance_agent.provenance import effective_configuration
from accounting_finance_agent.persistence import CHECKPOINT_DATABASE, ThreadHistory, open_history
from accounting_finance_agent.runtime import RunContext, RunControls, RunLimitExceeded
from accounting_finance_agent.sandbox import sandbox_backend
from accounting_finance_agent.worklog import WorkLog, thread_lease
from accounting_finance_agent.workspace import thread_workspace, use_workspace, workspace_manifest
from accounting_finance_agent.validation import validate_artifact
from accounting_finance_agent.clarification import pending_requests


COMMANDS = (
    ":new | :threads | :thread [ID] | :workspace | :state | :pending | :answer ID RESPONSE | :runs | :recovery [RUN_ID] | :review | "
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


def inspect_pending(settings, history, log, thread_id):
    """Read clarification requests from the durable checkpoint without a run."""
    class InspectionLog:
        def event(self, *args, **kwargs):
            pass
    controls = RunControls(settings, RunContext('inspection', thread_id, settings.timezone,
                                               str(thread_workspace(thread_id))), InspectionLog())
    try:
        graph = build_agent(settings, checkpointer=history.checkpointer, controls=controls)
        snapshot = graph.get_state({"configurable": {"thread_id": thread_id}})
        return pending_requests(snapshot)
    finally:
        if hasattr(controls, 'api_client'):
            controls.api_client.close()


def show_pending(requests):
    if not requests:
        print('No clarification is waiting in this thread.')
        return
    for request in requests:
        print(f"Clarification ID: {request['id']}\nQuestion: {request['question']}")
    print('Respond with :answer ID your response. The response starts a new run.')


def show_recovery(log, thread_id, run_id=None):
    """Show factual recovery evidence and leave the next action to the owner."""
    record = log.recovery_summary(thread_id, run_id)
    events = record['events']
    kinds = {kind for kind, _ in events}
    print(f"Run: {record['id']} | status: {record['status']} | error: {record['error_type'] or 'none recorded'}")
    failures = [details for kind, details in events if kind == 'failure_summary']
    if failures and failures[-1].get('timeout'):
        print('A timeout was recorded; inspect the run/trace to identify the affected operation.')
    print(f"Workspace: {thread_workspace(thread_id)}")
    outputs = record['outputs']
    if outputs is None or 'workspace_manifest_failed' in kinds:
        print('Final workspace manifest: unavailable; inspect files directly.')
    else:
        before = record['inputs']
        new = sorted(name for name in outputs if name not in before)
        changed = sorted(name for name in outputs if name in before and outputs[name] != before[name])
        print(f"Recorded final workspace: {len(outputs)} files; {len(new)} new, {len(changed)} changed since start.")
        for name in new:
            print(f'  New: {name}')
        for name in changed:
            print(f'  Changed: {name}')
    names = [details.get('sandbox') for kind, details in events
             if kind.startswith('sandbox_') and details.get('sandbox')]
    if names:
        print(f'Sandbox: {names[-1]}')
    if 'sandbox_retained' in kinds:
        print('Sandbox was retained after a transfer failure; inspect its recovery record and expiry before acting.')
    elif 'workspace_downloaded' in kinds:
        print('Sandbox workspace transfer completed; inspect outputs and transfer records for exclusions or conflicts.')
    elif 'sandbox_created' in kinds:
        print('No completed sandbox workspace transfer was recorded; work may be missing.')
    else:
        print('No completed sandbox creation was recorded; provider state may still need checking.')
    if 'sandbox_deletion_requested' in kinds:
        print('Sandbox deletion was requested; this record does not confirm deletion.')
    elif 'sandbox_deletion_unconfirmed' in kinds:
        print('Sandbox deletion could not be confirmed; check provider status.')
    elif 'sandbox_absent_on_cleanup' in kinds:
        print('Provider reported the sandbox absent during cleanup.')
    print('Next: inspect :state, the workspace and run/trace records. Reconcile any uncertain external effects before retrying.')
    print('No work has been automatically resumed or replayed. A new prompt is a new run.')


def run_prompt(settings, history, log, thread_id, prompt, *, sandbox, clarification_id=None):
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
    inputs = (Command(resume={clarification_id: prompt}) if clarification_id
              else {"messages": [{"role": "user", "content": prompt}]})
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
                pending = pending_requests(agent.get_state(config))
                if clarification_id:
                    if clarification_id not in {item['id'] for item in pending}:
                        raise ValueError('Clarification ID is no longer pending; inspect :pending.')
                    log.event(run_id, 'clarification_response_submitted', clarification_id=clarification_id)
                elif pending:
                    raise ValueError('A clarification is pending; use :pending and :answer before sending a new task.')
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
                pending = pending_requests(agent.get_state(config))
                if pending:
                    # The sandbox context exits before the pause is reported, so
                    # eligible work is copied out and cleanup follows normally.
                    answer = None
                elif not latest or not latest.get("messages"):
                    raise RuntimeError("Run finished without messages; inspect :state before continuing.")
                else:
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
            if pending:
                log.event(run_id, 'clarification_requested', ids=[item['id'] for item in pending])
                status = 'awaiting_clarification'
                show_pending(pending)
                return
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
            error_chain = [error_type]
            while cause.__cause__ is not None:
                cause = cause.__cause__
                error_chain.append(type(cause).__name__)
            status = "limited" if isinstance(cause, RunLimitExceeded) else "failed"
            log.event(run_id, "failure_summary", error_types=error_chain,
                      timeout=any('timeout' in name.lower() for name in error_chain))
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
                log.event(run_id, "workspace_manifest_failed", error=error_type)
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
            elif prompt == ":pending":
                show_pending(inspect_pending(settings, history, log, thread_id))
            elif prompt.startswith(":answer "):
                parts = prompt.split(maxsplit=2)
                if len(parts) != 3 or not parts[2].strip():
                    raise ValueError('Use :answer ID followed by your response.')
                requests = inspect_pending(settings, history, log, thread_id)
                if parts[1] not in {request['id'] for request in requests}:
                    raise ValueError('Clarification ID is not pending in this thread; use :pending.')
                run_prompt(settings, history, log, thread_id, parts[2], sandbox=True,
                           clarification_id=parts[1])
            elif prompt == ":recovery" or prompt.startswith(":recovery "):
                parts = prompt.split(maxsplit=1)
                show_recovery(log, thread_id, parts[1].strip() if len(parts) > 1 else None)
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
                if inspect_pending(settings, history, log, thread_id):
                    raise ValueError('A clarification is pending; use :pending and :answer before continuing.')
                history.record_prompt(history.select(thread_id), prompt)
                run_prompt(settings, history, log, thread_id, prompt, sandbox=True)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
            print("No task was automatically replayed. Use :recovery for recorded recovery details.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the accounting and finance agent.")
    # Keep existing launch commands working; all runs now use a sandbox.
    parser.add_argument("--sandbox", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--profile", choices=["local", EXCEL_PROFILE, COLLAB_PROFILE], default="local",
                        help="Select local, fixed Excel benchmark, or experimental peer collaboration.")
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
