"""Run the offline TEST-06 recovery gates and save structured evidence."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / ".state" / "evaluations" / "test-recovery-cases.json"
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_recovery_integration")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "suite": "tests.test_recovery_integration",
        "case_count": result.testsRun,
        "passed_count": result.testsRun - len(result.failures) - len(result.errors),
        "failures": [{"test": test.id(), "detail": detail} for test, detail in result.failures],
        "errors": [{"test": test.id(), "detail": detail} for test, detail in result.errors],
        "scope": {
            "network": "offline; no live provider or sandbox calls",
            "model_outputs": "scripted FakeMessagesListChatModel responses",
            "summary_transport": "BudgetClient with httpx.MockTransport returning synthetic HTTP 503",
            "filesystem": "temporary local thread workspaces and SQLite checkpoints",
            "cases": [
                "compiled agent and run_prompt fail after a write takes effect but its response is lost; restart and reconcile without repeating the effect",
                "nonempty partial text with incomplete/max_output_tokens, failed, or cancelled Responses status is rejected; earlier file output and recovery manifest are preserved",
                "pinned summarization middleware plus HTTP retry layer stays within six total provider attempts",
            ],
        },
        "test_output": stream.getvalue(),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"Recovery gate: {report['status']} ({report['passed_count']}/{report['case_count']})")
    print(f"Evidence: {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    if not result.wasSuccessful():
        print(stream.getvalue())
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
