"""Run offline engineering checks with network access blocked and fake credentials."""

import argparse
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

from accounting_finance_agent.config import PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Print the full test report.")
    args = parser.parse_args()
    # Support tests that import local helper scripts, regardless of launch cwd.
    sys.path.insert(0, str(PROJECT_ROOT))
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Network access is disabled in offline engineering checks.")
    report = io.StringIO()
    with (
        patch.dict(os.environ, {"OPENAI_API_KEY": "offline-placeholder", "LANGSMITH_TRACING": "false"}, clear=True),
        patch.object(socket.socket, "connect", side_effect=blocked),
        patch("socket.create_connection", side_effect=blocked),
        patch("accounting_finance_agent.config.load_dotenv", return_value=False),
    ):
        suite = unittest.defaultTestLoader.discover(str(PROJECT_ROOT / "tests"))
        result = unittest.TextTestRunner(stream=report, verbosity=2, buffer=True).run(suite)
    text = (f"Offline engineering checks: {datetime.now(timezone.utc).isoformat()}\n"
            f"Network connection attempts: {len(attempts)}\n\n" + report.getvalue())
    path = PROJECT_ROOT / ".state" / "engineering-checks-latest.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    success = result.wasSuccessful() and not attempts
    print(f"{'PASS' if success else 'FAIL'}: {result.testsRun} tests; "
          f"{len(result.failures)} failures; {len(result.errors)} errors; "
          f"{len(result.expectedFailures)} expected failures; {len(attempts)} network attempts.")
    print(f"Report: {path}")
    if args.verbose or not success:
        print(report.getvalue())
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
