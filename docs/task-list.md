# Accounting & Finance Agent — Delivery and Assessment Plan

| Field | Value |
|---|---|
| Version | v0.20 repository assessment · October 25, 2026 |
| Owner | Neil Yee; assign additional owners during planning. |
| Specification and design | [Agent specification and design](agent-spec.md) v0.24 |
| Assessment baseline | Source/document review on October 25, 2026 against spec v0.24 and the selected Excel benchmark. Historical evidence is labeled; no new tests or paid runs. |

This plan follows the [ADLC](mental-model/02-adlc.md). Assessments below distinguish existing implementation, historical evidence and remaining gaps against the selected requirements. Detailed findings are in [§10](#10-repository-assessment--october-25-2026). Reuse the foundation before adding missing behavior.

**Assessment values:** Not assessed · Missing · Partial · Meets completion criterion. Keep evidence links beside each finding. **Meets completion criterion** is the equivalent of checking off that row, for its stated scope. **Partial** means useful work exists but the full criterion is unmet. **Missing** means required implementation or evidence was not found in the inspected repository. Code presence can satisfy a build item; evaluation items require results, and release items require the corresponding approval. A gate is met only when its required evidence is complete. “Not met” can mean evidence is missing; it does not necessarily mean a test failed.

**Scope first:** select the next trial or release under spec §1. Deferred features stay unassessed and do not block unrelated work. Include finance, Asana, delegation, memory and concurrency checks when the selected scope uses them.

The owner has selected the [two-month Excel benchmark](agent-spec.md#32-starter-evaluation-tasks) and [trial settings](agent-spec.md#27-runtime-configuration-and-customization). The [fixture and rubric](evaluations/excel-benchmark.md) and labeled defaults now settle the design choices. The review below finds substantial reusable implementation, but the new benchmark, configuration and enforcement requirements are not yet complete.

## 1. Plan

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| PLAN-01 | Agree objective, boundaries, capabilities and criteria — §§1–3 | Reviewed anatomy and C1–C12 behavior/work/operating requirements → design → SC-1–SC-7 mapping; assumptions and exclusions explicit. | Meets completion criterion | [Spec scope and requirements](agent-spec.md#1-purpose-and-scope), owner decisions and [benchmark](evaluations/excel-benchmark.md) define the selected trial. Planning completion only. |
| PLAN-02 | Define task outputs and evaluation plan — §§2.3, 3.1–3.3; D2, D3 | Materialize the selected fixture/rubric into separate agent inputs and independent evaluator answers; retain four dimensions, three-run design, thresholds and seeded-defect checks. | Partial | [Fixture/rubric](evaluations/excel-benchmark.md) exists; separate machine-readable agent inputs, oracle and seeded-defect graders are not materialized. [§10.9](#109-cases-and-evaluation-evidence). |
| PLAN-03 | Select configuration and release design — §§2, 4; [deployment design](agent-spec.md#42-deployment-architecture-and-trust-boundaries); D1, D5 | Runtime choices and rationale per §2.7; host/storage, identities, concurrency, data policy, transfer limits and stop/recovery/rollback plan. | Partial | [Settings/design](agent-spec.md#27-runtime-configuration-and-customization) selected; exact recalculation image and verified effective profile/rate card still need evidence. [§10.1](#101-runtime-and-model), [§10.4](#104-artifacts-and-spreadsheet-tooling). |
| PLAN-04 | Define monitoring and response — §5.2; D4 | SC-1–SC-7 signals, data sources, thresholds, owners, cadence, trace access/retention and incident responses. | Meets completion criterion | [Monitoring plan](agent-spec.md#5-monitor-and-improve-requirements-and-design) defines signals, owner, cadence, failure response and retention; operating it is BUILD-10/MON-01–03. |
| PLAN-05 | Define references and memory policy — C1, C4–C6; §§2.7, 5.3; D7 | Ownership, scope, versions, read/write rules, retention/deletion, compatibility and promotion rules. | Partial | [Policy](agent-spec.md#42-deployment-architecture-and-trust-boundaries) and owner-maintained files exist; legacy demo-company scope and owner correction/deletion steps need alignment. [§10.2](#102-context-skills-and-planning). |
| PLAN-06 | Cross-check architecture and task coverage — §§2–6 | Architecture views cover agent execution, evaluation/operation and deployment boundaries; each requirement has work and evidence links. | Meets completion criterion | Reviewed spec loop, host/storage view, lifecycle view and requirement→inventory/task→criterion/evaluation mappings for the selected trial. Deferred scope remains explicit; no runtime completion implied. |

**Plan gate — partial:** selected scope and most policies are defined; PLAN-02/03/05 remain incomplete. Approve the design and evaluation/release/monitoring plans for the selected scope. Resolve decisions needed for that scope; record later decisions and their prerequisites.

## 2. Configure the shared foundation

Work may reuse or adapt existing implementation after assessment. Start with framework features and the shared model/tool loop. Treat concrete scenarios as evaluation cases; introduce dedicated tools or middleware when a required boundary or observed failure calls for them.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| BUILD-01 | Configure reproducible runtime and model — C2, C5–C6; [runtime design](agent-spec.md#runtime-and-tool-contracts--c2-c5); D1 | Verify account access and freeze the documented gpt-6-luna/high Standard rate card/profile; verify effective secondary limits, framework compaction and absence of delegation; retain versioned settings/overrides. | Partial | Model/Responses API, locked dependencies and framework runtime exist; benchmark limits/profile, no-delegation setting and full accounting are incomplete. [§10.1](#101-runtime-and-model). |
| BUILD-02 | Configure context, skills and planning — C1–C2; [context design](agent-spec.md#context-assembly--c1-c2) | Request/history/reference selection, source IDs, approved skills, todo state; versioned compaction prompt/trigger, retained history, retrieval and failure behavior per §2.7. | Partial | Context injection, todos, skills, read-only memory and built-in compaction exist. Benchmark reference isolation and recorded effective compaction settings remain. [§10.2](#102-context-skills-and-planning). |
| BUILD-03 | Configure sandbox and file/code tools — C2, C5, C7; [deployment design](agent-spec.md#42-deployment-architecture-and-trust-boundaries) | Tool contracts, working-copy boundary, package/image configuration, host/sandbox credentials and scoped access. | Partial | Remote sandbox, snapshot recipe, execution tools and copy-in/out exist; verify scoped network/image and immutable benchmark inputs. [§10.3](#103-sandbox-and-file-tools). |
| BUILD-04 | Implement artifact creation and validation — C3, C8–C11; §2.3 | First benchmark: openpyxl + selected LibreOffice image, saved recalculated formula values, independent figures and rendered visual review per §3.2 and its fixture/rubric; no final rewrite that discards caches. | Partial | openpyxl is owner-confirmed available; validation skill and structural checks exist. No selected LibreOffice recalculation/rendering pipeline or independent Excel grader found. [§10.4](#104-artifacts-and-spreadsheet-tooling). |
| BUILD-05 | Implement persistent threads and file transfer — C4, C7; [persistence design](agent-spec.md#state-files-and-recovery--c4-c7) | Verify selected SQLite/thread folders, application-driven export milestones, local archive/retention and transfer limits (§4.2); record any work lost after the last confirmed durable export. | Partial | SQLite threads, local task folders, locks, manifests and exit-time export exist; milestone export, archive/retention and transfer caps remain. [§10.5](#105-persistence-and-transfer). |
| BUILD-06 | Implement permissions and budgets — C5; [runtime](agent-spec.md#runtime-and-tool-contracts--c2-c5) and [access design](agent-spec.md#access-and-approval-enforcement--c3-c5-c7) | Enforced 10-minute/US$1 model-API limits, conservative per-call cost reservation including retries/compaction/delegation, supplied-data-only scope and access restrictions; evidence of budget exhaustion handling. | Partial | Admission/call limits and reference protections exist; no dollar reservation, complete attempt accounting or hard remaining-time enforcement. Benchmark network/source restrictions need alignment. [§10.6](#106-permissions-and-budgets). |
| BUILD-07 | Implement outcomes and recovery — C2, C4–C5; §2.2 | At most five eligible retries including SDK retries; visible attempt counts, backoff and shared budgets; explicit partial/failure states, write reconciliation and bounded preservation/cleanup. | Partial | Failure logging, retained-sandbox recovery and SDK retries exist; five-retry policy, deadline-aware backoff, output completeness and bounded cleanup remain. [§10.7](#107-outcomes-and-recovery). |
| BUILD-08 | Implement provenance and review — C3, C6; [evidence design](agent-spec.md#evidence-and-configuration--c6) | Traces, work log, effective configuration/overrides and prompt/middleware/subagent versions, source/output identities, actual-check reports and version-specific approvals. | Partial | Tracing/export, run logs, file hashes and approval commands exist; complete effective configuration/usage manifests and policy enforcement remain. [§10.8](#108-provenance-and-review). |
| BUILD-09 | Create cases and graders — §§3.2–3.3 | Versioned case IDs linked to requirements, criteria, evaluation layers and functions exercised; fixtures/rubrics, expected results, thresholds, repetitions, setup/reset and seeded defects to check graders. | Partial | Two CSV cases/runner, engineering tests and Excel design fixture exist; Excel input/oracle separation, graders and current case records are incomplete. [§10.9](#109-cases-and-evaluation-evidence). |
| BUILD-10 | Configure operational monitoring — §§4–5 | Applicable automatic checks, signal collection, owner review/routing, access/retention and stop/recovery controls; alerts when the operating model requires them. | Partial | CLI progress, structural checks, work logs and trace exports provide monitoring foundations; current cost/retention/review operations remain. [§10.10](#1010-monitoring-and-release). |

**Configure gate — not met for the new benchmark:** existing CSV/workbook activity does not satisfy the selected configuration and Excel criteria. To meet this gate, a representative task must complete the intended path, and fixtures, graders, instrumentation, and recovery procedures must be ready for evaluation. Completion of this gate does not establish task quality across the planned scope.

## 3. Evaluate the foundation

Cover shared behavior and operating requirements alongside reusable file work, following spec §3. Use code graders for precise outcomes and calibrated judgment for meaning or quality. Reuse evidence across requirements where the case actually exercises them; add targeted failure/boundary cases and repeat model-dependent trials.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| TEST-01 | E-PLAT-1 — C1–C3, C8 / SC-1 | Representative CSV, missing/conflicting-input, repeated compaction, revision-reference and selected delegation cases; compare configuration candidates with independent outputs/rubric and total usage/latency. | Partial | Historical CSV smoke and fake-model context/skill checks exist; no current-profile long-context/correction/three-run evidence. [§10.9](#109-cases-and-evaluation-evidence). |
| TEST-02 | E-ART-1 — C3, C9–C11 / SC-1 | Three clean fresh-thread runs of the §3.2 Excel benchmark: fixed inputs/configuration, independent numbers, detailed grounded analysis, saved recalculated values, visual review and preservation. Each passes; later C10–C11/package checks when selected. | Missing | No completed three-run series for the agreed Excel fixture/profile found. Earlier workbook demonstrations do not meet this criterion. [§10.9](#109-cases-and-evaluation-evidence). |
| TEST-03 | E-FILE-1 — C4, C7 / SC-2 | Task isolation/file lookup, source preservation, restart/abrupt-loss recovery under the declared policy, overlap rejection (or coordination if enabled), exclusions, conflicts and transfer failure. | Partial | Historical transfer, locks, checkpoint and conflict tests in [engineering results](engineering-checks.md); new export/retention/limits and abrupt-loss contract remain unevaluated. |
| TEST-04 | E-CTRL-1 — C5 / SC-3 | Allowed/denied/adversarial cases, actual filesystem/network/identity checks and enforced shared budgets. | Partial | Historical reference-denial and shared-budget checks in [engineering results](engineering-checks.md); live sandbox boundaries, $1 cap and current-profile enforcement are not established. |
| TEST-05 | E-PROV-1 — C6 / SC-3, SC-4 | Input-to-output evidence walkthrough, stale-approval cases, separate approval scopes and complete configuration references. | Partial | Historical approval/hash and persistence checks in [engineering results](engineering-checks.md); full effective-profile/input-to-output walkthrough for the benchmark remains. |
| TEST-06 | E-REC-1 — C2, C4, C5 / SC-7 | Startup failure, timeout after possible effect, incomplete response, budget exhaustion, transfer/cleanup failure and safe resume/retry. | Partial | Historical lifecycle/runner failure checks and [manual recovery utility](../scripts/recover_sandbox.py) exist; five-retry, spend, hard-deadline and lost-provider scenarios remain. |

**Foundation gate — not met:** required current-profile evidence is incomplete. Mandatory criteria pass for the defined cases and repetitions, with case/grader/configuration versions, limitations, and a recorded decision. Preserve passing capability cases as regressions.

## 4. Define and evaluate the first finance workflow

Apply this section when a business workflow such as C12 is selected. It is not a prerequisite for an Excel-only trial or release.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| FIN-01 | Confirm workflow, scope and independent answers — §3.2; D2, D3 | Bank reconciliation or an explicitly selected alternative; representative inputs, expected matches/exceptions/balances, critical thresholds and review rubric. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| FIN-02 | Configure skill and evaluation materials — C1–C7, C12; §3.3 | Procedure, approved references, access/packages, supporting calculations and versioned normal/edge/adversarial cases. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. Existing [reconciliation skill](../skills/bank-reconciliation/SKILL.md) is reusable guidance, not evaluated finance evidence. |
| FIN-03 | E-FIN-1 and affected regressions — C12 / SC-1 | Critical finance checks and representative human review pass; source preservation, artifact consistency and foundation regressions included. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |

**Finance gate:** accept only the evaluated task scope. Draft proposed entries do not authorize posting. A demonstration does not replace independent financial and presentation checks.

## 5. Release within the approved scope

Prerequisite: foundation and work-capability evidence for the selected release; finance evidence when that workflow is included.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| REL-01 | E-REL-1 readiness review — §§4.1–4.3 / SC-5 | Release record: configuration/scope, owner, identities, storage, data/trace policy, budgets, monitoring, compatible state/memory and rehearsed stop/recovery/rollback. | Partial | [Release design](agent-spec.md#4-deploy-requirements-and-design) and recovery utilities exist; no accepted current-benchmark evidence/release record or complete rehearsal. [§10.10](#1010-monitoring-and-release). |
| REL-02 | Conduct approved parallel operation — §4.1 | Representative comparison with the normal process; consequential writes suppressed; discrepancies reviewed against agreed thresholds. | Missing | No recorded parallel-operation comparison for the selected scope found; synthetic smoke runs do not establish this. |
| REL-03 | Authorize supervised use — §4.1 | Explicit decision for a defined scope; every output reviewed; operational results, limits and recovery meet the stage criteria. | Missing | No approved supervised-use release record for the selected scope found. Per-file review commands alone do not authorize release. |

**Release gate — not met:** no approved release record for this scope. Authorize only the recorded stage and scope. Local deployment is a valid choice; supervised use may remain the endpoint. Broader access or autonomy needs separate evidence and approval.

## 6. Monitor and improve

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| MON-01 | Operate per-run checks and response paths — §5.2 | Versioned run/outcome records, applicable checks, owner review and demonstrated response; alert routing when selected. | Partial | Run/structure records and review commands exist; current-profile usage/retention and demonstrated per-run response remain. [§10.10](#1010-monitoring-and-release). |
| MON-02 | Review outputs and trends — §5.2 | Reviews at agreed cadence; quality, corrections, costs and workload comparisons by task/configuration; decisions recorded. | Missing | Review cadence is planned; no three-run benchmark review or ongoing trend records against the selected configuration found. |
| MON-03 | Diagnose findings and release fixes — §5.3 | Evidence, impact, owner and response; useful regression cases, verified fixes or accepted limitations; memory/state compatibility considered. | Partial | [Engineering fixes/regressions](engineering-checks.md#fixes-made-during-this-pass) document earlier improvement work; current benchmark incident/change/release loop is not established. |

**Monitoring requirement:** every material finding has an accountable response. Trace completion alone does not establish correctness or approval.

## 7. Add the Asana task workflow

Select this integration after the foundation and dispatched work have relevant evidence. Apply the finance gate if it will dispatch finance workflows. These are planned dependencies, not findings about current code.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| ASANA-01 | Define eligibility, identity, triggers and approvals — §2.2; D6 | Task/thread mapping, permitted publication, status transitions, actionable feedback, deduplication, locking and version-specific review semantics. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| ASANA-02 | Configure intake and execution ownership — C1, C4–C7; §2.2 | Authorized task/context collection, eligible trigger handling, thread restoration, concurrency control and operation records. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| ASANA-03 | Configure publication and revision — §2.2 | Scoped status/summary/link updates, review of identified versions, same-thread revisions, and suppression of agent-generated trigger loops. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| ASANA-04 | E-ASANA-1 plus affected regressions — §3.3 / SC-6 | Normal/revision/informational/duplicate/out-of-order/concurrent/failure/restart cases; approved sample/repetition plan and no duplicate effects. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| ASANA-05 | Review readiness and staged rollout — §§4–5 | Updated E-REL-1 evidence for new identity/access, trigger stop/recovery, monitoring and approved rollout scope. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |

## 8. Later changes

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| CHANGE-01 | Add a skill, tool, connector or workload — §§2, 3.2–3.3, 5.3 | New objective/scope, design/access impact, capability cases, relevant regressions and release/monitoring decision. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |
| CHANGE-02 | Change runtime settings, middleware, subagents, shared guidance or memory policy — C1–C6; §§2.7, 5.3; D1, D7 | Impact-based evaluation; representative existing/stale/conflicting state; migration/invalidation, rollback and separate asset approval where required. | Not assessed | Deferred for the first Excel trial; not assessed in this pass. |

## 9. Repository review procedure

Use the spec’s [implementation inventory](agent-spec.md#26-implementation-inventory) to select shared building blocks. This task list is the single place for implementation status, paths, gaps and evidence. Update the spec when the intended requirements or design change.

1. Select a requirement/task and record the requirement IDs, functions exercised and evaluation cases it covers, its intended behavior and completion evidence.
2. Locate relevant code/configuration and existing evaluation records. Record exact paths, versions and results.
3. Distinguish implementation evidence from behavioral verification and release approval. Check whether old evidence applies to the current configuration and criterion.
4. Set the assessment and link evidence. Record concrete gaps or necessary changes; reuse suitable work instead of rebuilding it.
5. For a task covering multiple components, record each finding. Use **Partial** if some required components meet the criterion and others remain incomplete; keep unreviewed components explicitly **Not assessed**.
6. Reconcile stage gates only after reviewing their required evidence. Keep original records available for comparison.

## 10. Repository assessment — October 25, 2026

**Basis:** reviewed source at local commit `e1729a8`, locked dependency declarations, installed harness source, skills, environment recipes and existing reports against spec v0.24. No new tests, model calls, sandbox allocations or provider-state checks were run. Private environment overrides were not inspected; coded defaults below are not assertions about an active process.

**Existing evidence:** the saved, ignored `.state/engineering-checks-latest.txt` is dated October 22, 2026 and records 58 passing tests with zero network attempts. The tracked [engineering report](engineering-checks.md) describes coverage and one earlier CSV/JSON smoke run. These are historical plumbing/limited task evidence, not a current Excel benchmark pass. No reports were found in `.state/evaluations/` during this review.

**How to interpret this review:** three planning items meet their documentary criteria. All ten composite build items are Partial because useful components are wired, but new requirements remain. Deferred features are not marked missing merely because they are out of scope. A checked component below means source presence, not evaluated reliability.

### 10.1 Runtime and model

**Present:** [agent.py](../src/accounting_finance_agent/agent.py) builds Deep Agents with the OpenAI Responses API; [config.py](../src/accounting_finance_agent/config.py) defaults to `gpt-6-luna`/high; [pyproject.toml](../pyproject.toml) and [uv.lock](../uv.lock) pin dependencies. [The terminal](../src/accounting_finance_agent/__main__.py) streams graph updates and connects the runtime, checkpointer, sandbox and controls. Installed harness source includes default summarization and a general-purpose subagent; the application does not disable it.

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

**Present:** [agent.py](../src/accounting_finance_agent/agent.py), [knowledge.py](../src/accounting_finance_agent/knowledge.py), [runtime.py](../src/accounting_finance_agent/runtime.py) and [file_metadata.py](../src/accounting_finance_agent/file_metadata.py) connect task messages, runtime context, todo state, read-only memory/skill routes and binary-file metadata. Default compaction is supplied by the installed framework; no custom summary prompt is required by the trial design.

**Remaining:** record effective compaction trigger/model/prompt/retained-history settings and verify repeated-compaction behavior. [Approved memory](../memory/AGENTS.md) currently directs demo finance work toward an older [CAD company profile](../memory/company-profile.md) and reconciliation skill. Isolate that business context from the new supplied-data-only USD benchmark; procedural guidance may remain. Document owner correction/deletion steps and evaluate cross-thread isolation. Historical fake-model tests establish wiring, not semantic retention.

### 10.3 Sandbox and file tools

**Present:** [sandbox.py](../src/accounting_finance_agent/sandbox.py) creates a temporary execution backend with explicit resource/time/network configuration; [workspace.py](../src/accounting_finance_agent/workspace.py) supplies working-copy transfer. A [snapshot recipe](../environments/finance/snapshot.json), [builder](../scripts/build_sandbox_snapshot.py) and [environment guide](../environments/finance/README.md) exist.

**Remaining:** the current default allowlist permits package hosts and SEC endpoints; the selected task sandbox should have no external data/package access during execution. Empty hosts are rejected by config, and an absent allowlist is not deny-all; design the provider-supported restriction and verify it. A snapshot recipe is not proof of the active image or its access boundaries. Input copies are writable, and merge-back can replace their working version while archiving the old one; exact source immutability for the benchmark needs enforcement or detection, not only instructions.

### 10.4 Artifacts and spreadsheet tooling

**Present:** the owner confirms openpyxl is installed in the sandbox; this review did not allocate a sandbox or determine its version. [File-delivery guidance](../skills/file-delivery-validation/SKILL.md) covers generation and checks. [validation.py](../src/accounting_finance_agent/validation.py) inspects ZIP/XML/CSV/JSON structure and reports missing formula caches, numerical and visual limitations.

**Remaining:** no repository-defined LibreOffice recalculation/rendering pipeline or Excel numerical grader was found. The [snapshot requirements](../environments/finance/requirements.txt) currently add no packages; LibreOffice availability in the remote base remains unverified, not proven absent. Missing formula caches currently produce warnings, not the benchmark-required acceptance failure. Reuse openpyxl; add verified recalculation/cached-value/rendering paths and independent graders. Permit PDF/page previews as validation evidence while retaining Excel as the business deliverable.

### 10.5 Persistence and transfer

**Present:** [persistence.py](../src/accounting_finance_agent/persistence.py) supplies SQLite threads/checkpoints; [workspace.py](../src/accounting_finance_agent/workspace.py) uses per-thread folders, hashes, conflict/version retention and atomic local replacement; [worklog.py](../src/accounting_finance_agent/worklog.py) supplies a local overlapping-run lock. Remote deletions do not silently delete local files.

**Remaining:** [sandbox.py](../src/accounting_finance_agent/sandbox.py) exports in its exit/finally path, not after each file-producing call. No selected 10 MiB/50 MiB transfer limits, automated local backup or 30-day retention process was found. Define/implement intermediate exports and exact loss reporting; a hard sandbox loss can occur before exit-time copying. Existing deletion timers also limit manual recovery time.

### 10.6 Permissions and budgets

**Present:** [RunControls](../src/accounting_finance_agent/runtime.py) reserves logical calls and checks elapsed time before model/tool work; execute timeouts are capped in middleware/backend. [Read-only reference routes](../src/accounting_finance_agent/knowledge.py) reject mutations. Historical tests cover local budget/route behavior.

**Remaining:** there is no USD reservation or full API-attempt accounting. Admission checks do not interrupt an already-running call, cap every operation to remaining run time, or establish accounting for SDK retries/compaction. Setup/export/cleanup require a total deadline design. The new source-only/network restrictions and actual provider boundaries remain unverified. Do not treat the proposed US$1/10-minute cap as currently enforced.

### 10.7 Outcomes and recovery

**Present:** [run_prompt](../src/accounting_finance_agent/__main__.py) records `failed`, `limited` or `needs_review`; missing message state and unfinished tool calls fail. It blocks structural errors. [sandbox.py](../src/accounting_finance_agent/sandbox.py) attempts export on ordinary failures and retains the sandbox after failed export; [recover_sandbox.py](../scripts/recover_sandbox.py) can retry copying without rerunning the model. The CLI avoids automatic task replay.

**Remaining:** no unified five-retry policy, per-attempt progress/backoff or bounded 60-second cleanup was found. `run_prompt` does not reject empty final AI text or require the benchmark workbook to exist: an empty structural-check list can still lead to `needs_review`. Add task-specific completeness and required-check gates. SDK retries of model requests do not establish safe retries/reconciliation for tool side effects. Manual recovery is possible only while the remote sandbox survives.

### 10.8 Provenance and review

**Present:** [worklog.py](../src/accounting_finance_agent/worklog.py) persists runs/events/manifests and hash-bound approvals; changed files display stale review and failed/other-thread runs cannot be approved. [export_traces.py](../scripts/export_traces.py) supports read-only export/sync of trace trees and available usage/cost fields. [CLI review commands](operating-guide.md) are available.

**Remaining:** run-start details contain selected model, timezone, workspace and snapshot, but not the complete effective settings, code/prompt/dependency/middleware versions or a price/accounting ledger. Trace metadata may contain additional fields; it does not replace an explicit effective-profile manifest. Verify tracing is on for the selected profile; its code default is false and environment overrides were not examined. Owner access/retention and benchmark review records still need evidence.

### 10.9 Cases and evaluation evidence

**Present:** [two CSV cases](../evaluations/csv-cases.jsonl) and [evaluate_agent.py](../scripts/evaluate_agent.py) separate expected answers from agent inputs, use fresh threads and compare source preservation/results. [Engineering tests](../tests/) cover framework wiring, transfer, limits, failure paths and review. The new [Excel fixture/rubric](evaluations/excel-benchmark.md) defines exact inputs and reference answers.

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

## Change log

| Version | Date | Change |
|---|---|---|
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
