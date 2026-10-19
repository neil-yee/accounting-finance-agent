"""Opt-in paid smoke evaluations; never runs merely by starting the application."""

import argparse
from contextlib import closing
import json
from uuid import uuid4

from accounting_finance_agent.__main__ import run_prompt
from accounting_finance_agent.config import PROJECT_ROOT, load_settings
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.worklog import WorkLog
from accounting_finance_agent.workspace import thread_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Authorize this invocation's two model/sandbox trials.")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to explicitly start paid model and sandbox trials.")
    settings = load_settings(require_sandbox=True)
    cases = [json.loads(line) for line in (PROJECT_ROOT / "evaluations" / "csv-cases.jsonl").read_text().splitlines() if line.strip()]
    results = []
    with open_history(mode="evaluation") as history, closing(WorkLog()) as log:
        for case in cases:
            thread = history.new()
            folder = thread_workspace(thread.id)
            source = folder / "source.csv"
            source.write_bytes(case["csv"].encode("utf-8"))
            error = None
            try:
                run_prompt(settings, history, log, thread.id, case["prompt"], sandbox=True)
                actual = json.loads((folder / "result.json").read_text())
            except Exception as exc:
                error, actual = type(exc).__name__, None
            passed = (error is None and actual == case["expected"] and source.is_file()
                      and source.read_bytes() == case["csv"].encode("utf-8"))
            results.append({"case": case["id"], "thread_id": thread.id, "passed": passed,
                            "error_type": error, "actual": actual})
    output = PROJECT_ROOT / ".state" / "evaluations" / f"{uuid4()}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Evaluation report: {output}")
    raise SystemExit(0 if all(item["passed"] for item in results) else 1)


if __name__ == "__main__":
    main()
