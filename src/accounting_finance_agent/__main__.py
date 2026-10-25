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
    run_id = str(uuid4())
    path = thread_workspace(thread_id) if sandbox else None
    context = RunContext(run_id, thread_id, settings.timezone, str(path) if path else "virtual thread files")
    controls = RunControls(settings, context, log)
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 300,
              "run_id": run_id, "metadata": {"app_run_id": run_id, "work_thread_id": thread_id}}
    inputs = {"messages": [{"role": "user", "content": prompt}]}
    print(f"Run: {run_id}")
    with thread_lease(thread_id), (use_workspace(path) if path else nullcontext()):
        before = workspace_manifest() if sandbox else {}
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
            ) if sandbox else nullcontext(None)
            with scope as backend:
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
                answer = final.text
            if sandbox:
                after_transfer = workspace_manifest()
                reports = [validate_artifact(path / relative) for relative, digest in after_transfer.items()
                           if digest != before.get(relative) and (path / relative).suffix.lower() in
                           {".xlsx", ".docx", ".pptx", ".csv", ".json"}]
                log.event(run_id, "artifact_structure_checks", reports=reports)
                print(f"[Structure checks] {len(reports)} files; {sum(len(r['warnings']) for r in reports)} warnings. Not financial or visual sign-off.")
                if any(report["errors"] for report in reports):
                    raise ValueError("Generated files failed structural checks. Inspect the work log and revise before approval.")
            status = "needs_review"
            print(f"\nAgent: {answer}\nRun saved for review: {run_id}")
        except BaseException as exc:
            error_type = type(exc).__name__
            status = "limited" if isinstance(exc, RunLimitExceeded) else "failed"
            raise
        finally:
            try:
                after = workspace_manifest() if sandbox else {}
            except Exception as exc:
                after = {}
                status = "failed"
                error_type = type(exc).__name__
            log.event(run_id, "run_counts", **controls.counts)
            log.finish(run_id, status, after, error_type)


def chat(settings: Settings, history: ThreadHistory, *, sandbox: bool, thread_id: str, log=None) -> None:
    print(f"Current thread: {thread_id}")
    if sandbox:
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
                if sandbox:
                    print(f"New separate workspace: {thread_workspace(thread_id)}")
            elif prompt == ":threads":
                for thread in history.list():
                    print(f"{'*' if thread.id == thread_id else ' '} {thread.id} | {thread.title or '(empty conversation)'}")
            elif prompt == ":thread":
                print(f"Current thread: {thread_id}")
            elif prompt.startswith(":thread "):
                thread_id = history.select(prompt.split(maxsplit=1)[1].strip()).id
                print(f"Resumed thread: {thread_id}")
                if sandbox:
                    print(f"Workspace: {thread_workspace(thread_id)}")
            elif prompt == ":workspace":
                print(thread_workspace(thread_id) if sandbox else "Files are virtual and checkpointed in this thread.")
            elif prompt == ":state":
                show_state(settings, history, thread_id)
            elif prompt in {":runs", ":review"}:
                with use_workspace(thread_workspace(thread_id)) if sandbox else nullcontext():
                    manifest = workspace_manifest() if sandbox else {}
                for run in log.runs(thread_id):
                    print(f"{run['id']} | {run['status']} | {log.review_status(run['id'], manifest)} | {run['started']}")
            elif prompt.startswith((":approve ", ":reject ")):
                if not sandbox:
                    raise ValueError("Artifact review commands require sandbox mode and its local workspace.")
                parts = prompt.split(maxsplit=2)
                decision = "approved" if parts[0] == ":approve" else "rejected"
                with use_workspace(thread_workspace(thread_id)) if sandbox else nullcontext():
                    manifest = workspace_manifest() if sandbox else {}
                log.review(parts[1], thread_id, decision, manifest, getpass.getuser(), parts[2] if len(parts) > 2 else "")
                print(f"Recorded {decision} for exact run {parts[1]}. No reusable assets were promoted.")
            elif prompt.startswith(":"):
                print(f"Unknown command. {COMMANDS}")
            else:
                history.record_prompt(history.select(thread_id), prompt)
                run_prompt(settings, history, log, thread_id, prompt, sandbox=sandbox)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
            print("No task was automatically replayed. Inspect :state, :runs, and the workspace before continuing.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the accounting and finance agent.")
    parser.add_argument("--sandbox", action="store_true", help="Use one temporary sandbox per prompt.")
    parser.add_argument("--profile", choices=["local", EXCEL_PROFILE], default="local",
                        help="Select local settings or the staged, fixed Excel benchmark baseline.")
    parser.add_argument("--show-config", action="store_true",
                        help="Print secret-free configuration without running a model or sandbox.")
    parser.add_argument("--thread", metavar="ID", help="Resume an existing conversation.")
    args = parser.parse_args()
    try:
        settings = load_settings(require_sandbox=args.sandbox, profile=args.profile,
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
    if args.sandbox:
        print(f"Sandbox environment: {settings.sandbox_snapshot_id or 'LangSmith default'}")
        print("Each thread has its own workspace; use :workspace to see where to put files.")
        print("Existing files at workspace/ are untouched; copy needed files into the thread folder.")
        print("Sandbox HTTPS allowlist: " + ", ".join(settings.sandbox_allowed_hosts))
    try:
        with open_history(mode="sandbox" if args.sandbox else "virtual") as history, closing(WorkLog()) as log:
            try:
                thread = history.initial(args.thread)
            except ValueError as exc:
                parser.error(str(exc))
            chat(settings, history, sandbox=args.sandbox, thread_id=thread.id, log=log)
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. Your thread can be resumed next time.")


if __name__ == "__main__":
    main()
