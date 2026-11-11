# Engineering checks in LangSmith

The six `accounting-finance-engineering-v1-*` datasets index the existing offline
`unittest` checks in `tests/`. Each example contains a `test_id` and group; its
expected output is `{"status": "passed"}`. The setup, fixtures, and real
assertions remain in the repository. Uploading the datasets does not execute a
check, configure online monitoring, or upload the test implementation.

| Group | What it covers |
| --- | --- |
| `foundation-runtime` | General foundation and agent runtime checks. |
| `sandbox-workspace` | Sandbox lifecycle, workspace transfer, staging, isolation and boundaries. |
| `recovery` | Offline recovery behavior and recovery probe checks. |
| `benchmark-controls` | Benchmark profile, budgets and additional benchmark implementation checks. |
| `evaluation-infrastructure` | Context rubrics, evaluation infrastructure and workbook grader checks. |
| `financial-helpers` | Financial working-paper helpers and management review oracle/grader checks. |

The groups describe current test modules; some modules contain checks for more
than one concern. `benchmark-controls` does not imply that all checks in that
group apply to the local profile.

## Sync and run

From the repository root, with dependencies and LangSmith credentials configured:

```bash
# List the discovered checks by group. This does not execute them.
uv run --locked python scripts/langsmith_engineering.py inventory

# Create datasets or add missing cases. No checks execute.
uv run --locked python scripts/langsmith_engineering.py sync

# Run one group locally and upload an experiment and scores to LangSmith.
uv run --locked python scripts/langsmith_engineering.py run recovery
```

Replace `recovery` with any group name from the table. Sync assigns stable IDs,
checks existing examples, and does not delete extra remote examples. Review any
warning about extra examples before running an experiment. If tests are removed
or renamed, manually review the old remote examples: a stale ID will not be run
against an unrelated test.

For an experiment, LangSmith gives the local target each test ID. The target
launches a separate local Python process for that unittest. As in
`scripts/check_engineering.py`, the test process uses fake credentials and
blocks socket connections. Its status and report return to the local evaluator,
which records pass/fail feedback in LangSmith; skipped cases are not passes.
These are offline tests, not live sandbox or model evaluations. Each case runs in
isolation, so results may differ from running the full suite together. There are
no automatic online evaluations in this setup.
