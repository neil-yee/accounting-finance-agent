# Evaluation fixtures and evidence

[Project overview](../README.md) · [Operating guide](../docs/operating-guide.md)

This directory holds synthetic task inputs and independent evaluator assets.
Published results live in `docs/evaluations/`; earlier reports are retained in
`docs/history/`.

## Current benchmark

The current Excel fixture is **`excel-v4`**. The latest evaluated runtime profile
is **`excel-benchmark-v5`**: fixture versions describe the assignment and evaluation
assets, while profile versions describe runtime settings and limits. The v5 series
used the v4 fixture in three fresh threads. All three passed numerical checks and
independent spreadsheet recalculation, and the owner approved the exact output
versions on November 5, 2026.

- [Excel v5 results](../docs/evaluations/excel-v5-results.md)
- [Foundation checks and limits](../docs/evaluations/foundation-v5-2026-11-05.md)
- [Live request and tool ceiling probes](../docs/evaluations/v5-live-ceiling-probes-2026-11-05.md)
- [Calculation contract and review rubric](../docs/evaluations/excel-benchmark.md)
- [Earlier failures, corrections and approvals](../docs/history/test-gate-followup-2026-10-25.md)

These results cover one fictional assignment and the recorded configuration.
They do not establish general accounting reliability or approval for business use.

## Fixture catalog

| Fixture | Status | Purpose and evidence |
| --- | --- | --- |
| [Excel v4](excel-v4/) | Current benchmark fixture | Two-month Excel working paper; used in the approved v5 series above. |
| [Excel v1](excel-v1/), [v2](excel-v2/), [v3](excel-v3/) | Historical fixtures | Preserve earlier requirements and failed or superseded trials. v1 also supports grader defaults and engineering checks. |
| [Management review](management-review-v1/README.md) | Assisted demonstration | Department, project and budget analysis; [recorded results](../docs/evaluations/management-review.md) include reviewer intervention and limitations. |
| [Rolling monthly report](rolling-report-v1/README.md) | Exploratory draft | Five stages covering added periods, corrections and missing context; no established benchmark result. |
| [Starter CSV cases](csv-cases.jsonl) | Draft smoke cases | Two arithmetic and source-preservation cases; no published result for this dataset. |

## Inputs and evaluator boundaries

Supply only the selected fixture's `agent-inputs/` files to the agent. Keep
`evaluator/` assets, expected answers and evaluation reports outside its workspace
and context. For the rolling report, supply inputs one stage at a time.
Management-review metric names are agent inputs; expected numerical values remain
in its independent oracle.

Keep versioned fixtures intact, including repeated source files. The Excel series
runner records hashes of every fixture file so earlier results can be traced to
their exact inputs and requirements. Save new task revisions as a new fixture
version. Numerical grades and independent recalculation are supplemented by
narrative, presentation and owner review.

## Running evaluations

The [operating guide](../docs/operating-guide.md#versioned-excel-trial-profile)
documents the current Excel series command, profile requirements and review
process. Model and sandbox trials use paid services. Raw traces, trial workbooks
and local result records remain in the gitignored `traces/`, `workspace/` and
`.state/` directories.

For the two starter CSV smoke cases, run from the repository root:

```sh
uv run --locked python scripts/evaluate_agent.py --run
```

The runner creates a fresh thread and workspace for each case, exposes only the
prompt and `source.csv`, and compares the result with expected answers on the
host. Passing requires normal completion, exact parsed JSON totals and row counts,
and byte-identical source data. Reports are saved under `.state/evaluations/`.
These cases assess basic arithmetic and file handling; they do not assess
financial statements, spreadsheet recalculation or presentation.

For the separate offline engineering inventory and optional experiment uploads,
see [Engineering checks in LangSmith](langsmith-engineering.md).
