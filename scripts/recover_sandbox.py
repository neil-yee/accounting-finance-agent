"""Explicitly export files from a retained sandbox without replaying an agent task."""

import argparse
from contextlib import closing

from dotenv import load_dotenv
from langsmith.sandbox import SandboxClient

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.worklog import WorkLog, thread_lease
from accounting_finance_agent.workspace import download_workspace, thread_workspace, use_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", help="Run ID printed by the terminal; uses its recorded upload hashes.")
    parser.add_argument("--delete-after-copy", action="store_true", help="Request deletion only after a successful export.")
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    with closing(WorkLog()) as log, SandboxClient() as client:
        thread_id, name, baseline = log.recovery_record(args.run_id)
        with thread_lease(thread_id), use_workspace(thread_workspace(thread_id)):
            sandbox = client.get_sandbox(name)
            print(f"Recovering {name}; a stopped sandbox may wake and incur compute usage.")
            result = download_workspace(sandbox, name, baseline)
            log.event(args.run_id, "manual_recovery", transfers=result)
            if args.delete_after_copy:
                client.delete_sandbox(name)
                log.event(args.run_id, "sandbox_deletion_requested", sandbox=name)
                print("Sandbox deletion requested. Use the deletion-check command to confirm absence.")
            else:
                print("Files exported; sandbox was not deleted. Its lifecycle timers still apply.")


if __name__ == "__main__":
    main()
