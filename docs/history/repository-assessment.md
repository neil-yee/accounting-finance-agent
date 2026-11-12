# Repository assessment and build history

These notes record the October 25–26, 2026 assessment and implementation sequence. Counts, open gaps, and completion statements describe that point in the project. Later evidence and the current delivery checklist are linked from the [task list](../task-list.md) and [v5 results](../evaluations/excel-v5-results.md).

## 10. Repository assessment — October 25, 2026

This is the initial source-review snapshot. The [build chronology](#11-build-progress) records subsequent changes; the [current task list](../task-list.md) holds the stage assessments.

**Basis:** reviewed source at local commit `e1729a8`, locked dependency declarations, installed harness source, skills, environment recipes and existing reports against spec v0.24. No new tests, model calls, sandbox allocations or provider-state checks were run. Private environment overrides were not inspected; coded defaults below are not assertions about an active process.

**Existing evidence:** the saved, ignored `.state/engineering-checks-latest.txt` is dated October 22, 2026 and records 58 passing tests with zero network attempts. The tracked [engineering report](engineering-checks.md) describes coverage and one earlier CSV/JSON smoke run. These are historical plumbing/limited task evidence, not a current Excel benchmark pass. No reports were found in `.state/evaluations/` during this review.

**How to interpret this review:** all six planning items meet their documentary criteria for the selected trial. The earlier v0.20 assessment incorrectly held PLAN-02/03/05 open for downstream implementation/verification; those gaps remain assigned to Build/Test/Release tasks. At that initial snapshot all ten composite Build items were Partial. The later increments complete BUILD-01–10; current evidence is recorded in §11. Deferred features are not marked missing merely because they are out of scope. A checked component below means source presence, not evaluated reliability.

### 10.1 Runtime and model

**Present:** [agent.py](../../src/accounting_finance_agent/agent.py) builds Deep Agents with the OpenAI Responses API; [config.py](../../src/accounting_finance_agent/config.py) defaults to `gpt-6-luna`/high; [pyproject.toml](../../pyproject.toml) and [uv.lock](../../uv.lock) pin dependencies. [The terminal](../../src/accounting_finance_agent/__main__.py) streams graph updates and connects the runtime, checkpointer, sandbox and controls. Installed harness source includes default summarization and a general-purpose subagent; the application does not disable it.

| Setting | Source default / current implementation | Selected benchmark target |
|---|---|---|
| Model/reasoning | gpt-6-luna / high | Same; verify account/effective profile and Standard tier. |
| Run time | 900 seconds, checked when admitting calls | 600-second work deadline plus bounded 60-second preservation/cleanup. |
| Model/tool ceilings | 40 / 120 logical calls | 20 model requests / 40 tool attempts, including retries/summarization as specified. |
| Output cap | 16,000 tokens | 32,000 maximum, reduced to available API spend. |
| Model/tool timeout | 120 / 120 seconds | 180 / 120 seconds, each capped by remaining run time. |
| Model retries | SDK `max_retries=2` | Up to five retries per eligible operation, counted across layers. |
| Delegation | Framework default remains enabled | Disabled, including removal of the delegation tool. |
| API budget | No monetary reservation/price calculation found | US$1 shared cap with conservative preflight accounting. |

**Remaining:** verify effective settings, immutable environment/profile and account access; implement the selected caps/delegation/accounting behavior. Existing code is the starting point.

### 10.2 Context, skills and planning

**Present:** [agent.py](../../src/accounting_finance_agent/agent.py), [knowledge.py](../../src/accounting_finance_agent/knowledge.py), [runtime.py](../../src/accounting_finance_agent/runtime.py) and [file_metadata.py](../../src/accounting_finance_agent/file_metadata.py) connect task messages, runtime context, todo state, read-only memory/skill routes and binary-file metadata. Default compaction is supplied by the installed framework; no custom summary prompt is required by the trial design.

**Remaining:** record effective compaction trigger/model/prompt/retained-history settings and verify repeated-compaction behavior. [Approved memory](../../memory/AGENTS.md) currently directs demo finance work toward an older [CAD company profile](../../memory/company-profile.md) and reconciliation skill. Isolate that business context from the new supplied-data-only USD benchmark; procedural guidance may remain. Document owner correction/deletion steps and evaluate cross-thread isolation. Historical fake-model tests establish wiring, not semantic retention.

### 10.3 Sandbox and file tools

**Present:** [sandbox.py](../../src/accounting_finance_agent/sandbox.py) creates a temporary execution backend with explicit resource/time/network configuration; [workspace.py](../../src/accounting_finance_agent/workspace.py) supplies working-copy transfer. A [snapshot recipe](../../environments/finance/snapshot.json), [builder](../../scripts/build_sandbox_snapshot.py) and [environment guide](../../environments/finance/README.md) exist.

**Remaining:** the current default allowlist permits package hosts and SEC endpoints; the selected task sandbox should have no external data/package access during execution. Empty hosts are rejected by config, and an absent allowlist is not deny-all; design the provider-supported restriction and verify it. A snapshot recipe is not proof of the active image or its access boundaries. Input copies are writable, and merge-back can replace their working version while archiving the old one; exact source immutability for the benchmark needs enforcement or detection, not only instructions.

### 10.4 Artifacts and spreadsheet tooling

**Present:** the owner confirms openpyxl is installed in the sandbox; this review did not allocate a sandbox or determine its version. [File-delivery guidance](../../skills/file-delivery-validation/SKILL.md) covers generation and checks. [validation.py](../../src/accounting_finance_agent/validation.py) inspects ZIP/XML/CSV/JSON structure and reports missing formula caches, numerical and visual limitations.

**Remaining:** no repository-defined LibreOffice recalculation/rendering pipeline or Excel numerical grader was found. The [snapshot requirements](../../environments/finance/requirements.txt) currently add no packages; LibreOffice availability in the remote base remains unverified, not proven absent. Missing formula caches currently produce warnings, not the benchmark-required acceptance failure. Reuse openpyxl; add verified recalculation/cached-value/rendering paths and independent graders. Permit PDF/page previews as validation evidence while retaining Excel as the business deliverable.

### 10.5 Persistence and transfer

**Present:** [persistence.py](../../src/accounting_finance_agent/persistence.py) supplies SQLite threads/checkpoints; [workspace.py](../../src/accounting_finance_agent/workspace.py) uses per-thread folders, hashes, conflict/version retention and atomic local replacement; [worklog.py](../../src/accounting_finance_agent/worklog.py) supplies a local overlapping-run lock. Remote deletions do not silently delete local files.

**Remaining:** [sandbox.py](../../src/accounting_finance_agent/sandbox.py) exports in its exit/finally path, not after each file-producing call. No selected 10 MiB/50 MiB transfer limits, automated local backup or 30-day retention process was found. Define/implement intermediate exports and exact loss reporting; a hard sandbox loss can occur before exit-time copying. Existing deletion timers also limit manual recovery time.

### 10.6 Permissions and budgets

**Present:** [RunControls](../../src/accounting_finance_agent/runtime.py) reserves logical calls and checks elapsed time before model/tool work; execute timeouts are capped in middleware/backend. [Read-only reference routes](../../src/accounting_finance_agent/knowledge.py) reject mutations. Historical tests cover local budget/route behavior.

**Remaining:** there is no USD reservation or full API-attempt accounting. Admission checks do not interrupt an already-running call, cap every operation to remaining run time, or establish accounting for SDK retries/compaction. Setup/export/cleanup require a total deadline design. The new source-only/network restrictions and actual provider boundaries remain unverified. Do not treat the proposed US$1/10-minute cap as currently enforced.

### 10.7 Outcomes and recovery

**Present:** [run_prompt](../../src/accounting_finance_agent/__main__.py) records `failed`, `limited` or `needs_review`; missing message state and unfinished tool calls fail. It blocks structural errors. [sandbox.py](../../src/accounting_finance_agent/sandbox.py) attempts export on ordinary failures and retains the sandbox after failed export; [recover_sandbox.py](../../scripts/recover_sandbox.py) can retry copying without rerunning the model. The CLI avoids automatic task replay.

**Remaining:** no unified five-retry policy, per-attempt progress/backoff or bounded 60-second cleanup was found. `run_prompt` does not reject empty final AI text or require the benchmark workbook to exist: an empty structural-check list can still lead to `needs_review`. Add task-specific completeness and required-check gates. SDK retries of model requests do not establish safe retries/reconciliation for tool side effects. Manual recovery is possible only while the remote sandbox survives.

### 10.8 Provenance and review

**Present:** [worklog.py](../../src/accounting_finance_agent/worklog.py) persists runs/events/manifests and hash-bound approvals; changed files display stale review and failed/other-thread runs cannot be approved. [export_traces.py](../../scripts/export_traces.py) supports read-only export/sync of trace trees and available usage/cost fields. [CLI review commands](../operating-guide.md) are available.

**Remaining:** run-start details contain selected model, timezone, workspace and snapshot, but not the complete effective settings, code/prompt/dependency/middleware versions or a price/accounting ledger. Trace metadata may contain additional fields; it does not replace an explicit effective-profile manifest. Verify tracing is on for the selected profile; its code default is false and environment overrides were not examined. Owner access/retention and benchmark review records still need evidence.

### 10.9 Cases and evaluation evidence

**Present:** [two CSV cases](../../evaluations/csv-cases.jsonl) and [evaluate_agent.py](../../scripts/evaluate_agent.py) separate expected answers from agent inputs, use fresh threads and compare source preservation/results. [Engineering tests](../../tests) cover framework wiring, transfer, limits, failure paths and review. The new [Excel fixture/rubric](../evaluations/excel-benchmark.md) defines exact inputs and reference answers.

**Remaining:** the paid evaluation runner handles the older two-case CSV dataset, not three Excel repetitions. The Excel fixture is still an evaluator document, not separated machine-readable inputs/oracle/grader execution. No current three-run results, formula-recalculation evidence or visual/analysis sign-off were found. Retain historical engineering evidence while adding the missing cases; do not rerun paid tasks merely to relabel an old result.

### 10.10 Monitoring and release

**Present:** CLI plan/tool progress, timestamps/statuses, structural-check records, review commands and manual trace exports provide useful local observation. [Engineering results](engineering-checks.md#fixes-made-during-this-pass) document previous diagnosis and regression fixes.

**Remaining:** no implemented API-cost guard/trend report, scheduled retention, benchmark-series review or approved release record for the selected scope was found. The spec defines owner cadence and incident responses; operating evidence remains open. Asana, production hosting and automatic learning are deferred and were not assessed for completion.

### 10.11 Practical implementation order

1. Align the effective trial profile, disable delegation and isolate benchmark context; verify the selected remote image/tool availability.
2. Implement shared cost/time/retry enforcement and honest completeness/failure outcomes before a paid benchmark run.
3. Add recalculation/rendering, independent Excel inputs/oracle/graders and required-check gates.
4. Add milestone preservation, transfer caps, backup/retention and complete configuration records.
5. Run the relevant engineering/foundation checks when requested, then the three paid benchmark runs under the agreed caps. Record results and owner review before checking off evaluation/release items.

## 11. Build progress

### Increment 1 — trial configuration, reference scope and provenance

Implemented in source on October 25, 2026; **not executed or tested**.

| Work | Code / documentation | Follow-up (Build / Test) |
|---|---|---|
| BUILD-01: fixed trial profile | [config.py](../../src/accounting_finance_agent/config.py) defines `excel-benchmark-v1`; [agent.py](../../src/accounting_finance_agent/agent.py) configures the API tier, SDK retry setting and default-subagent switch. | BUILD-01 is source-complete. Runtime/profile/delegation/provider checks: TEST-01/04/05. Image: BUILD-03; rates/accounting: BUILD-06. |
| BUILD-02: selected context | [knowledge.py](../../src/accounting_finance_agent/knowledge.py) routes benchmark memory and only two procedural skills; [guidance](../../references/excel-benchmark/memory/AGENTS.md) contains no company defaults; agent construction records computed framework compaction defaults. | BUILD-02 is source-complete. Exercise route isolation, retention and profile switching under TEST-01/03/04/06. |
| BUILD-08: configuration evidence | [provenance.py](../../src/accounting_finance_agent/provenance.py) records settings, source/reference hashes and dependency versions; [runner](../../src/accounting_finance_agent/__main__.py) stores the manifest and offers `--show-config`. | Build: implement usage/rate and sandbox package records. Test: verify saved manifests and identities under TEST-05. |
| BUILD-02: owner reference maintenance | [Operating guide](../operating-guide.md#versioned-excel-trial-profile) documents correction/removal and fresh-thread handling. | Stale-context evaluation: TEST-01/03. Thread/trace/archive deletion implementation: BUILD-05. |

**Historical state after increment 1:** the benchmark profile was staged. The CLI and `run_prompt` rejected execution
before remote work while cost/retry/deadline enforcement, sandbox network/image
setup, required artifact checks and preservation safeguards are unfinished. This
is a temporary implementation gate, not evidence that those safeguards exist.
The existing local profile remains available with its documented limitations.

**Assessment after increment 1:** BUILD-01/02 were source-complete; BUILD-03–10 still had implementation gaps. The increment below supersedes that status.
The historical 58-check report does not cover this increment. Next: BUILD-06/07
shared API-attempt accounting, dollar reservation, retry controller and deadlines.

### Increment 2 — remaining build components and execution checks

All ten Build tasks now meet their scoped implementation criteria. No Test or
Release task is newly completed. The original 58 checks were rerun; the expanded
suite passes **78 tests with zero network attempts**.

| Evidence | Result |
|---|---|
| Frozen sandbox | `3dce6ed0-f050-432a-bc9a-79a7b960972f`; LibreOffice 26.2.6.3, Poppler/fonts and captured Python inventory. Builder deletion confirmed. |
| Provider egress probe | Requested proxy deny-all still allowed PyPI because organization policy replaces caller controls. This mechanism was insufficient. |
| Effective execution boundary | Every benchmark execution is wrapped in a user/network namespace. Live DNS/direct-IP connections failed; re-entry to the original network namespace was denied. |
| Recalculation/rendering | The frozen image converted/rendered inside the namespace; =2+3 retained cached value 5 and one rendered page. Human visual review remains pending. Probe sandbox deletion was requested. |
| Budget/retry checks | Conservative reservation/refund, unknown usage, six-attempt ceiling, invalid-request handling, remaining-budget output reduction and Retry-After/deadline stopping pass offline. |
| State/evaluation checks | Reference isolation, consistent SQLite/file backup, closed-thread retention selection, namespace wrapper and four seeded grader defects pass offline. |
| Compiled graph | Model/reasoning/tier/client settings compile; filesystem/todo tools are exposed and `task` is absent. No model request was made during inspection. |
| Retention | Plan command runs; no eligible closed threads and no destructive deletion executed. Hosted delete requests are asynchronous and must be rechecked. |

**Operating limits:** the selected runner is synchronous and requires a POSIX
host. It rejects direct non-image provider attachments and hidden server-side history;
use sandbox libraries to inspect documents. Embedded image input is now enabled
with provider token preflight, as recorded below. Reservation prices deliberately exceed the
published Standard cache/long-context/regional rates, so logged estimates can be
higher than invoiced cost. Unknown usage stays reserved. The frozen image and
reference/prompt/configuration hashes must remain fixed during a three-run series.

The build does not establish reliability for every file format. The exact
numerical/label contract is in the agent-only task input. Human evaluation still
checks grounded explanations, formula meaning and rendered presentation. The
three fresh-thread model runs and release decisions remain outstanding.

### Demonstration follow-up — repeated edits and media handling

A separate fictional income-statement/analysis Excel + PDF task completed after
two runtime fixes. Repeated checkpoints now retain different versions without
filename collisions, and exports are serialized. Unsupported media is explained
in outgoing text-only requests; stored tool results remain available for review.
Both behaviors have regression coverage; the full offline suite passes **80 tests
with zero network attempts**. The earlier failed/limited runs remain recorded.
The successful continuation is `needs_review`, not human-approved. Its workbook
calculations/caches and PDF layout were checked independently. This is ad hoc
demonstration evidence, not the fixed three-run benchmark. No Test/Release status
is promoted on that basis. See the [engineering report](engineering-checks.md).

### Image input enabled

The owner requested image input after the demonstration. Embedded images now pass
through to the model; direct non-image document/audio/video inputs still receive
a supported-format explanation. `BudgetClient` preflights each immutable image
with the provider token-count endpoint and caches the result within a run. Image
tokens share the dollar reservation, request ceiling and deadline. Remote image
URLs/file IDs and invalid/unaffordable counts stop before generation.

The full suite passes **85 offline tests with zero network attempts**. A fresh
sandbox run read only the report-preview image and correctly returned its title,
January/February net income and layout observations. Its status is `needs_review`;
this is visual-input evidence, not owner approval or a formal benchmark pass.
The settings manifest records the supported input policy and the versioned rate
card records the counting contract. [Operating instructions](../operating-guide.md#versioned-excel-trial-profile).

### Multi-source management-review demonstration

The fictional three-department/six-project case now has frozen agent inputs, an
independent Decimal oracle, a cached-cell grader and eight offline checks. The
assisted run exposed sign/mapping errors and an ineffective self-check; reviewed
repairs were rebuilt by the accounting agent. The resulting package matches all
316 required metrics, retains source hashes and has a reviewed three-page PDF.
This required stopped attempts and reviewer intervention; it is not a clean
first-pass or formal benchmark result. Owner review and all existing Test/Release
gates remain outstanding. The full offline suite now passes **94 tests with zero
network attempts**, including the new 40-request boundary check. See the
[attempt history and assessment](../evaluations/management-review.md).

### Request ceiling revision

The owner requested a less restrictive request ceiling during the management-review
trial. Profile `excel-benchmark-v2` raises it from 20 to 40 provider requests.
Image-token preflights, inference retries and compaction share this counter. The
US$1 reservation policy, 600-second work deadline and 40-tool-attempt ceiling
remain unchanged. Existing v1 attempts retain their recorded configuration; the
revision applies to future runs and starts a new comparison baseline.

### Work deadline revision

The owner extended the work deadline from 10 to 30 minutes (1,800 seconds).
Profile `excel-benchmark-v3` records this new baseline. The US$1 API budget,
40 provider requests, 40 tool attempts and separate 60-second preservation/cleanup
phase are unchanged. Earlier attempts retain their recorded limits and outcomes.
The existing profile assertion now expects v3 and 1,800 seconds; tests were not
rerun for this configuration change.

### First Test pass

Collected all three formal Excel trials under profile v3 before applying fixes.
Two stopped at API reservation and one at the tool ceiling; 0/3 pass. Corrected
grader results, independent recalculation, live boundary/recovery probes and
128 passing offline tests are recorded in the [Test report](test-phase-2026-10-25.md).
Checkpoint, delivery selection and evaluation-harness defects were fixed after
collection. A new source-baseline series and remaining Test cases are still needed.
No release or monitoring gate is promoted.

### Test-gate follow-up — final fixture v4

The final series `df3feccd-26d4-44e0-8c7c-5ae0adfd1edb` passes numerical, grounding and assistant visual checks on three fresh trials within the unchanged runtime limits. The 142-test offline suite, 7/7 live context cases and 3/3 integrated offline recovery cases pass. The [follow-up report](test-gate-followup-2026-10-25.md) retains the v1 budget/tool stops, v2 causal-attribution failure, pre-hardening v3 results and post-hardening v3 uncertainty failure.

The runner now rejects explicit non-completed model status, even with partial text. The strict profile stages approved generic working-paper helpers and detects their mutation during export; no evaluator answers enter the agent workspace. BudgetClient alone controls HTTP retries, including summaries. Local-profile behavior is separate.

TEST-01/03/04/05/06 meet their selected scope. Owner approval completes TEST-02 and the selected Test gate. No release is approved.

```bash
uv run --locked python scripts/run_excel_series.py --run --assets evaluations/excel-v4
```

## Change log

| Version | Date | Change |
|---|---|---|
| v0.31 | 2026-10-26 | Recorded final v4 technical checks, context/recovery results, incomplete-response hardening and retained failures; recorded owner approval of the three exact outputs and completed the selected Test gate; Release remains pending. |
| v0.30 | 2026-10-25 | Recorded prior v3 numerical/grounding results as historical, corrected-run/visual-review gaps, selected-scope Test status and explicit fixture-series reproduction command; preserved earlier outcomes. |
| v0.29 | 2026-10-25 | Recorded the first Test pass, three limited trials, independent regrades, live probes, repaired regressions and remaining gates. |
| v0.28 | 2026-10-25 | Extended the owner-requested work deadline to 30 minutes in profile v3; retained other limits and historical evidence. |
| v0.27 | 2026-10-25 | Versioned the larger 40-request ceiling as profile v2; kept other limits and prior run evidence intact. |
| v0.26 | 2026-10-25 | Enabled image input with token preflight/shared budgets, recorded 85 offline checks and successful live image inspection; no formal evaluation/release promotion. |
| v0.25 | 2026-10-25 | Recorded the ad hoc Excel/PDF demonstration, checkpoint/media fixes and 80 passing offline checks; preserved formal evaluation/release gates. |
| v0.24 | 2026-10-25 | Completed BUILD-03–10 implementation, captured and probed a frozen image, recorded 78 passing offline checks and compiled tool inspection; kept benchmark/release evidence separate. |
| v0.23 | 2026-10-25 | Separated implementation from verification/evaluation; marked BUILD-01/02 source-complete, assigned image/pricing to their owning Build tasks, and retained all checks under linked Test/Monitor tasks. |
| v0.22 | 2026-10-25 | Recorded the first source build increment: staged benchmark profile, scoped guidance and configuration provenance; retained Partial statuses and explicit verification gaps. |
| v0.21 | 2026-10-25 | Corrected stage boundaries: planning judges decisions/design; all six selected-trial planning items meet that criterion. Preserved build, evaluation and release gaps and assigned memory procedures explicitly. |
| v0.20 | 2026-10-25 | Assessed the selected trial against source and historical evidence; recorded existing components, specific gaps and conditional gates without new tests or paid runs. |
| v0.19 | 2026-10-25 | Connected selected design defaults and benchmark fixture/rubric to implementation evidence; preserved unassessed statuses. |
| v0.18 | 2026-10-25 | Linked agreed benchmark/model/budget/retry/memory decisions to implementation and evaluation evidence; retained unassessed status. |
| v0.17 | 2026-10-25 | Aligned with pragmatic trial scope: conditional finance/integration gates and owner-led monitoring; preserved unassessed implementation records. |
| v0.16 | 2026-10-25 | Aligned planning and case records with anatomy-first requirements and layered, requirement-based evaluation grading. |
| v0.15 | 2026-10-24 | Linked runtime settings, compaction, middleware and subagent configuration to build evidence, evaluation comparisons and change review. |
| v0.14 | 2026-10-24 | Made this task list the single place for implementation status and evidence; linked the spec inventory without duplicating assessments. |
| v0.13 | 2026-10-24 | Retargeted design and lifecycle references to the combined specification and design document. |
| v0.12 | 2026-10-24 | Connected repository review to the spec implementation checklist and defined how detailed findings update its summary. |
| v0.11 | 2026-10-24 | Replaced granular behavior references with capability/case mapping; prioritized shared framework features and evaluation-driven specialization. |
| v0.10 | 2026-10-24 | Added behavior-ID mapping to planning, evaluation cases and repository assessment. |
| v0.9 | 2026-10-24 | Aligned criterion-based monitoring and corrected section/version references. |
| v0.8 | 2026-10-24 | Aligned work references with the reordered assignment lifecycle and evaluation plan. |
| v0.7 | 2026-10-24 | Pointed requirements to capability IDs and architecture details after removal of the spec shared-rules section; renumbered lifecycle references. |
| v0.6 | 2026-10-23 | Aligned work references with the combined capability/design table and shared rules; retained all assessment fields. |
| v0.5 | 2026-10-23 | Mapped work and evaluation items to the classified capability catalog; retained unassessed evidence fields. |
| v0.4 | 2026-10-23 | Replaced implementation-based statuses with an unassessed delivery plan; added capability/evaluation mappings, evidence fields and a later repository review procedure. |
| v0.3 and earlier | 2026-10-23 | Earlier task lists retained in Git history. |
