# Documentation

[Project overview](../README.md)

## Start here

| Goal | Read |
| --- | --- |
| Understand the demonstrated accounting task | [Excel benchmark and acceptance criteria](evaluations/excel-benchmark.md) |
| See the latest published results | [v5 workbook trials](evaluations/excel-v5-results.md), [foundation checks](evaluations/foundation-v5-2026-11-05.md), and [ceiling probes](evaluations/v5-live-ceiling-probes-2026-11-05.md) |
| Install and use the agent | [Setup and technical guide](technical-guide.md) |
| Choose a profile, review outputs, or recover work | [Operating guide](operating-guide.md) |
| Understand intended behavior and architecture | [Specification and design](agent-spec.md) |
| See completion criteria and remaining work | [Project task list](task-list.md) |
| Explore cases or run evaluations | [Evaluation catalog](../evaluations/README.md) and [script catalog](../scripts/README.md) |
| Understand the design vocabulary | [Mental models](mental-model/00-overview.md) |

The specification describes requirements and design. The task list records delivery status. Evaluation reports record what happened under an identified configuration. A historical result does not automatically apply to a later configuration.

## Repository map

| Location | Purpose |
| --- | --- |
| [src/accounting_finance_agent/](../src/accounting_finance_agent/) | Agent runtime, controls, persistence, and file handling. |
| [tests/](../tests/) | Engineering checks for the implementation and evaluation tools. |
| [evaluations/](../evaluations/) | Synthetic cases, prompts, independent expected answers, and rubrics. |
| [scripts/](../scripts/) | Operations and evaluation entry points, grouped in their README. |
| [skills/](../skills/) | Reusable agent procedures and supporting code. |
| [memory/](../memory/) | Owner-maintained local-profile guidance and fictional company context. |
| [references/](../references/) | Separate reference scope for the fixed Excel benchmark. |
| [config/](../config/) | Model pricing used by the conservative budget controls. |
| [environments/finance/](../environments/finance/) | Sandbox recipe, release record, and build instructions. |
| [docs/evaluations/](evaluations/) | Current benchmark contract, published results, and assisted demonstration assessment. |
| [docs/history/](history/) | Earlier assessments, implementation notes, and test reports. |

Private runtime data lives in Git-ignored `workspace/`, `.state/`, and `traces/`. Those folders contain working files, checkpoints, review records, and raw execution evidence; they are not disposable repository clutter.

## Evidence and history

- [Current evaluation catalog](../evaluations/README.md): distinguishes the evaluated Excel workflow from drafts and exploratory tasks.
- [Management-review demonstration](evaluations/management-review.md): a more complex case that required reviewer intervention, separate from the formal benchmark.
- [Historical reports](history/README.md): earlier failures, fixes, and build decisions retained for context.

Versioned fixtures stay at their existing paths because tests and provenance records reference them. Keep agent inputs separate from evaluator answers when preparing a run.
