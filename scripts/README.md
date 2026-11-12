# Script catalog

Run these tools from the repository root with the locked environment:

```bash
uv run --locked python scripts/SCRIPT.py [arguments]
```

All entries are command-line tools except `recalculate_evaluation.py`, which is
an imported helper. Most CLIs expose arguments with `--help`; consult the linked
source for tools without an argument parser. Real model and sandbox calls incur
service usage. Model evaluations also upload traces when tracing is enabled.

See the [technical guide](../docs/technical-guide.md) for setup and checks, the
[operating guide](../docs/operating-guide.md) for profiles, trials and recovery,
and the [evaluation catalog](../evaluations/README.md) for fixtures.

## Operations

| Script | Purpose | Execution side effects |
| --- | --- | --- |
| [build_sandbox_snapshot.py](build_sandbox_snapshot.py) | Build a reusable finance environment release. | Creates a real builder sandbox and persistent snapshot; writes a local manifest. `--activate` also selects the snapshot in `.env`. No model calls. |
| [export_traces.py](export_traces.py) | Download project traces or a selected trace. | Reads LangSmith and writes `traces/`. Defaults to syncing the last 30 days; `--trace` and `--latest` narrow selection. |
| [manage_retention.py](manage_retention.py) | Close threads and apply retention rules. | Defaults to a local plan. `--close` writes a closure marker; `--apply` archives files and prunes eligible local data; adding `--hosted` requests or verifies LangSmith trace deletion. |
| [monitor_runs.py](monitor_runs.py) | Summarize recent runs, costs and review needs. | Opens the local work log and prints JSON; no service calls. |
| [recover_sandbox.py](recover_sandbox.py) | Export files from a recorded retained sandbox. | Contacts a real sandbox, which may wake; writes local files and recovery events. `--delete-after-copy` requests deletion after export. No model calls. |
| [validate_artifacts.py](validate_artifacts.py) | Inspect the structure of supplied files. | Offline inspection; prints JSON. Does not execute generated code or recalculate workbooks. |

## Evaluation and review

| Script | Purpose | Execution side effects |
| --- | --- | --- |
| [evaluate_agent.py](evaluate_agent.py) | Run the two starter CSV cases in fresh threads. | Requires `--run`; makes real model and sandbox calls, writes workspaces and local reports. |
| [run_excel_series.py](run_excel_series.py) | Run three frozen Excel trials with independent recalculation. | Requires `--run`; makes real model and sandbox calls, writes trial files and evidence. Defaults to `evaluations/excel-v4`. |
| [grade_excel_benchmark.py](grade_excel_benchmark.py) | Grade Excel calculations, source preservation and structural requirements. | Offline inspection; prints JSON. Defaults to `evaluations/excel-v1`; pass `--assets evaluations/excel-v4` for current trials. Also imported by other evaluation tools. |
| [grade_management_review.py](grade_management_review.py) | Grade management-review metrics using an optional cell map. | Offline inspection of the supplied delivery; prints JSON. |
| [recalculate_evaluation.py](recalculate_evaluation.py) | Imported helper for independently recalculating a delivery copy. | Called by the series runner; creates a real sandbox and writes a fresh local output folder and report. No model calls or standalone CLI. |
| [seed_excel_defects.py](seed_excel_defects.py) | Create four deliberately defective delivery copies. | Offline; creates and modifies copies under the supplied destination. Also imported by checks. |
| [check_excel_defects.py](check_excel_defects.py) | Confirm seeded defects are rejected after a positive control passes. | Offline; creates defective copies, grades them and writes the required `--output` report. |
| [review_excel_workbooks.py](review_excel_workbooks.py) | Check source rows, formula dependencies, cached errors and small text. | Offline workbook inspection; writes the required `--output` report. Narrative and presentation still require human review. |
| [assess_excel_evidence.py](assess_excel_evidence.py) | Reconstruct trial provenance, file identity and review status. | Reads host records, workspaces and downloaded traces; writes the required `--output` report. Exercises approval rejection in a temporary synthetic database. |

## Engineering checks and probes

| Script | Purpose | Execution side effects |
| --- | --- | --- |
| [check_engineering.py](check_engineering.py) | Run the offline unittest suite with network access blocked. | Runs local tests and writes `.state/engineering-checks-latest.txt`. |
| [evaluate_recovery_cases.py](evaluate_recovery_cases.py) | Run the offline recovery suite and capture structured evidence. | Runs local tests and writes `.state/evaluations/test-recovery-cases.json`. |
| [evaluate_context_cases.py](evaluate_context_cases.py) | Probe instruction handling, clarification and context compaction. | Makes real model calls immediately, with a virtual backend and no sandbox; writes local evidence. `--case` selects one case. |
| [check_workspace_transfer.py](check_workspace_transfer.py) | Exercise file transfer and deletion confirmation. | Creates one real sandbox and leaves synthetic local files. `--check-deletion NAME` only reads sandbox status. No model calls. |
| [probe_evaluation_boundaries.py](probe_evaluation_boundaries.py) | Probe isolation, transfer limits and recovery after process loss. | Creates a real sandbox, intentionally exits a child process and saves local evidence. No model calls; `--child` is an internal subprocess mode. |
| [probe_evaluation_checkpoint.py](probe_evaluation_checkpoint.py) | Probe checkpoint export across remote deletion and recreation. | Creates a real sandbox and writes local synthetic files and evidence. No model calls. |
| [langsmith_engineering.py](langsmith_engineering.py) | Publish existing tests as datasets and report their results. | `inventory` discovers local tests; `sync` writes LangSmith datasets; `run GROUP` runs local offline tests and uploads results. `execute TEST_ID` is the local subprocess entry point. |

## Fixture maintenance

| Script | Purpose | Execution side effects |
| --- | --- | --- |
| [prepare_excel_benchmark.py](prepare_excel_benchmark.py) | Materialize the original Excel inputs, oracle and rubric from the benchmark specification. | Offline; writes or overwrites fixture files in the supplied destination. Use a new destination to preserve versioned fixtures. |

Scripts stay together because evaluation tools use sibling imports and record
evaluator hashes. Versioned fixtures and retained evidence are indexed in the
evaluation catalog rather than regenerated as part of routine cleanup.
