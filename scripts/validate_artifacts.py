"""Inspect file structure, without running generated code or recalculating Excel."""

import argparse
import json
from pathlib import Path

from accounting_finance_agent.validation import validate_artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    results = [validate_artifact(path) for path in args.files]
    print(json.dumps(results, indent=2))
    raise SystemExit(1 if any(item["errors"] for item in results) else 0)


if __name__ == "__main__":
    main()
