"""Sync accounting-finance-agent traces locally through the LangSmith API."""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from dotenv import load_dotenv
from langsmith import AsyncClient

from accounting_finance_agent.config import PROJECT_ROOT

DEFAULT_PROJECT = "accounting-finance-agent"

# Explicit projection: the current query API otherwise returns only run IDs.
RUN_FIELDS = [
    "ID", "NAME", "RUN_TYPE", "STATUS", "START_TIME", "END_TIME", "ERROR",
    "EXTRA", "METADATA", "EVENTS", "INPUTS", "OUTPUTS", "PARENT_RUN_IDS",
    "PROJECT_ID", "TRACE_ID", "THREAD_ID", "DOTTED_ORDER", "IS_ROOT", "TAGS",
    "TOTAL_TOKENS", "PROMPT_TOKENS", "COMPLETION_TOKENS", "TOTAL_COST",
    "PROMPT_COST", "COMPLETION_COST", "FIRST_TOKEN_TIME", "FEEDBACK_STATS",
    "PROMPT_TOKEN_DETAILS", "COMPLETION_TOKEN_DETAILS",
]


async def query_runs(client: AsyncClient, project, since: datetime, **filters):
    """Follow every API page within the selected date window."""
    return [run async for run in client.runs.query(
        project_ids=[str(project.id)], min_start_time=since,
        selects=RUN_FIELDS, **filters,
    )]


def trace_id(value: str) -> UUID:
    """Accept the UUID printed by the app or a trace-UUID export name."""
    try:
        return UUID(value.removeprefix("trace-"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use a run/trace UUID, optionally prefixed with trace-.") from exc


async def export_trace(client: AsyncClient, run_id: UUID, project, destination: Path, since: datetime) -> tuple[Path, str]:
    matches = await query_runs(client, project, since, ids=[str(run_id)])
    if not matches:
        raise ValueError("Run not found; check its ID, --project and --days date window.")
    selected = matches[0]
    identifier = str(UUID(selected.trace_id))
    runs = {run.id: run for run in await query_runs(client, project, since, trace_id=identifier)}
    runs.setdefault(selected.id, selected)
    if identifier not in runs:
        raise ValueError("The trace root is not available; export was not saved.")
    ordered = sorted(runs.values(), key=lambda run: (run.dotted_order or "", str(run.id)))
    missing_parents = sorted({parent for run in ordered
                              for parent in (run.parent_run_ids or []) if parent not in runs})
    if missing_parents:
        raise ValueError("Some parent runs are missing from the API response; retry after ingestion completes.")
    unfinished = sum(run.end_time is None for run in ordered)
    payload = {
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": project.name,
        "project_id": str(project.id),
        "trace_id": str(identifier),
        "run_count": len(ordered),
        "unfinished_run_count": unfinished,
        "scope": "Run records including inputs/outputs; separate binary attachments are not downloaded.",
        "runs": [
            {**json.loads(run.model_dump_json(exclude={"attachments"}, exclude_unset=True)),
             "parent_run_id": (run.parent_run_ids or [None])[-1]}
            for run in ordered
        ],
    }
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"trace-{identifier}.json"
    change = "updated" if target.exists() else "new"
    if target.exists():
        try:
            previous = json.loads(target.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            previous = None
        # Compare the actual trace, excluding this export's timestamp. Always
        # query the API so delayed children, errors and costs can be refreshed.
        if isinstance(previous, dict):
            previous.pop("exported_at", None)
            current = {key: value for key, value in payload.items() if key != "exported_at"}
            if previous == current:
                print(f"Unchanged: {target.name}", flush=True)
                return target, "unchanged"
    # Publish the new copy only after its entire JSON has been written.
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination,
                                prefix=".export-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Saved {len(ordered)} runs: {target}", flush=True)
    if unfinished:
        print(f"Snapshot includes {unfinished} unfinished runs; export again after the trace finishes.", flush=True)
    return target, change


async def export_selected(args, project_name: str):
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    async with AsyncClient() as client:
        project = await client.read_project(project_name=project_name)
        if args.trace:
            ids = [args.trace]
        else:
            ids = []
            async for run in client.runs.query(
                project_ids=[str(project.id)], min_start_time=since,
                is_root=True, page_size=args.latest or 100, selects=["ID"],
            ):
                ids.append(UUID(run.id))
                if args.latest is not None and len(ids) >= args.latest:
                    break
        if not ids:
            print("No traces found in this project.", flush=True)
        else:
            print(f"Found {len(ids)} traces in the selected window.", flush=True)
        counts = {"new": 0, "updated": 0, "unchanged": 0, "failed": 0}
        for identifier in ids:
            try:
                _, change = await export_trace(client, identifier, project, PROJECT_ROOT / "traces", since)
                counts[change] += 1
            except Exception as exc:
                counts["failed"] += 1
                print(f"Could not export {identifier}: {type(exc).__name__}: {exc}", flush=True)
        print("Sync complete: " + ", ".join(f"{number} {label}" for label, number in counts.items()), flush=True)
        if counts["failed"]:
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--sync", action="store_true", help="Sync all project traces in the date window (default).")
    selection.add_argument("--trace", type=trace_id, help="One trace or child-run UUID.")
    selection.add_argument("--latest", type=int, metavar="N", help="Export the N most recent root traces.")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help=f"LangSmith project (default: {DEFAULT_PROJECT}).")
    parser.add_argument("--days", type=int, default=30, help="Look back 1–400 days (default: 30).")
    args = parser.parse_args()
    if args.latest is not None and not 1 <= args.latest <= 100:
        parser.error("--latest must be between 1 and 100.")
    if not 1 <= args.days <= 400:
        parser.error("--days must be between 1 and 400 (API time-window limit).")
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    if not os.getenv("LANGSMITH_API_KEY", "").strip():
        parser.error("Set LANGSMITH_API_KEY in .env before exporting.")
    project_name = args.project
    print(f"Reading LangSmith project: {project_name}", flush=True)
    asyncio.run(export_selected(args, project_name))


if __name__ == "__main__":
    main()
