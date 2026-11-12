# Accounting & Finance Agent — Delivery and Assessment Plan

| Field | Value |
|---|---|
| Version | v0.32 Documentation organization · November 11, 2026 |
| Owner | Neil Yee; assign additional owners during planning. |
| Specification and design | [Agent specification and design](agent-spec.md) v0.30 |
| Assessment baseline | Initial review against spec v0.24; first build increment at `8eb7d90` reviewed against unchanged requirements in spec v0.25. Historical evidence is labeled; no new tests or paid runs. |

This plan follows the [ADLC](mental-model/02-adlc.md). Assessments below distinguish existing implementation, historical evidence and remaining gaps against the selected requirements. The initial review is in [§10](#10-repository-assessment--october-25-2026); subsequent build changes are in [§11](#11-build-progress). Reuse the foundation before adding missing behavior.

**Assessment values:** Not assessed · Missing · Partial · Meets completion criterion. Keep evidence links beside each finding. **Meets completion criterion** is the equivalent of checking off that row, for its stated scope. **Partial** means useful work exists but the full criterion is unmet. **Missing** means required implementation or evidence was not found in the inspected repository. Assess each item against its stage: planning requires documented decisions and an actionable design; build requires configured or implemented components; evaluation requires results; release requires readiness evidence and the corresponding approval. A gate is met only when its required evidence is complete. “Not met” can mean evidence is missing; it does not necessarily mean a test failed.

**Scope first:** select the next trial or release under spec §1. Deferred features stay unassessed and do not block unrelated work. Include finance, Asana, delegation, memory and concurrency checks when the selected scope uses them.

The owner selected the [two-month Excel benchmark](agent-spec.md#32-starter-evaluation-tasks) and [strict trial settings](agent-spec.md#27-runtime-configuration-and-customization). All selected Build components are implemented and connected. The final fixture v4 series passed all technical checks on three fresh trials under the earlier v3 runtime, and the owner approved those exact outputs. A later v5 series passed numerical checks and independent recalculation in all three trials; the owner approved those exact output manifests on November 5, 2026. Selected foundation checks were repeated under v5; subsequent [live ceiling probes](evaluations/v5-live-ceiling-probes-2026-11-05.md) confirmed both controls and exposed a separate graph recursion limit. This is evidence for the selected scope, not release approval. See [v5 Excel results](evaluations/excel-v5-results.md), [v5 foundation checks](evaluations/foundation-v5-2026-11-05.md), and the earlier [follow-up report](history/test-gate-followup-2026-10-25.md).

## 1. Plan

Planning is complete when the selected scope, design, acceptance rules and responsibilities are defined well enough to build and evaluate. Working code, pinned build outputs and passing runs belong to later tasks. Reopen planning if implementation exposes an unresolved choice that changes the agreed design.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| PLAN-01 | Agree objective, boundaries, capabilities and criteria — §§1–3 | Reviewed anatomy and C1–C12 behavior/work/operating requirements → design → SC-1–SC-7 mapping; assumptions and exclusions explicit. | Meets completion criterion | [Spec scope and requirements](agent-spec.md#1-purpose-and-scope), owner decisions and [benchmark](evaluations/excel-benchmark.md) define the selected trial. Planning completion only. |
| PLAN-02 | Define task outputs and evaluation plan — §§2.3, 3.1–3.3; D2, D3 | Define inputs/outputs, independent reference answers and their separation from agent context, four evaluation dimensions, three-run design, thresholds and seeded-defect checks. | Meets completion criterion | [Fixture/rubric](evaluations/excel-benchmark.md) and [evaluation design](agent-spec.md#3-test-requirements-and-evaluation-design) define the contract. Creating runnable inputs/oracles/graders is BUILD-09; recording benchmark outcomes is TEST-02. |
| PLAN-03 | Select configuration and release design — §§2, 4; [deployment design](agent-spec.md#42-deployment-architecture-and-trust-boundaries); D1, D5 | Document runtime choices/rationale, host/storage, identities, concurrency, data policy, transfer limits and stop/recovery/rollback design; define how the environment baseline will be frozen. | Meets completion criterion | [Settings](agent-spec.md#27-runtime-configuration-and-customization) and [deployment/recovery design](agent-spec.md#4-deploy-requirements-and-design) select the trial baseline, including openpyxl/LibreOffice and an immutable image. Profile configuration is BUILD-01, image/tooling is BUILD-03/04, and the rate card/accounting is BUILD-06. Runtime verification belongs to Test; recovery implementation and release evidence remain BUILD-05/07 and REL-01–03. |
| PLAN-04 | Define monitoring and response — §5.2; D4 | SC-1–SC-7 signals, data sources, thresholds, owners, cadence, trace access/retention and incident responses. | Meets completion criterion | [Monitoring plan](agent-spec.md#5-monitor-and-improve-requirements-and-design) defines signals, owner, cadence, failure response and retention; operating it is BUILD-10/MON-01–03. |
| PLAN-05 | Define references and memory policy — C1, C4–C6; §§2.7, 5.3; D7 | Define ownership, permitted sources, read/write scope, version/compatibility handling and retention/deletion; state whether automatic learning or promotion is enabled. | Meets completion criterion | [Trial scope](agent-spec.md#1-purpose-and-scope), [storage policy](agent-spec.md#42-deployment-architecture-and-trust-boundaries) and [change policy](agent-spec.md#53-response-and-improvement-design) define thread-local work, owner-maintained read-only guidance, retention and version compatibility; automatic learning is deferred. Aligning legacy company references and documenting owner correction/deletion steps is BUILD-02/05; isolation and preservation evidence is TEST-01/03. |
| PLAN-06 | Cross-check architecture and task coverage — §§2–6 | Architecture views cover agent execution, evaluation/operation and deployment boundaries; each requirement has work and evidence links. | Meets completion criterion | Reviewed spec loop, host/storage view, lifecycle view and requirement→inventory/task→criterion/evaluation mappings for the selected trial. Deferred scope remains explicit; no runtime completion implied. |

**Plan gate — met for the selected Excel trial:** all six planning items have documented decisions/design evidence, including owner-authorized defaults. This permits proceeding with configuration and implementation; it does not establish that the runtime meets the design or that a trial/release is ready. Deferred extensions need their own planning when selected.

## 2. Configure the shared foundation

Build status answers: **is the required implementation present and connected?** Test status answers: **does it satisfy the criteria when exercised?**

- **Meets completion criterion:** the scoped implementation is present and wired, based on the stated evidence. Runtime verification may still be pending.
- **Partial:** name the missing code, configuration, environment asset or operating procedure. An unrun evaluation alone does not make a Build task partial.
- Source review and executed checks are different evidence. For this increment, wiring was reviewed in source; no new execution checks have run. Completion here does not establish a working benchmark or release readiness.
- Reopen a Build task if verification reveals a defect or missing implementation. Keep the failed evaluation under its Test task as evidence.

Reuse framework features and the shared model/tool loop. Introduce specialized handling when a requirement or observed failure calls for it.

| ID | Work / spec reference | Build completion requires | Build assessment | Implementation evidence / remaining build work |
|---|---|---|---|---|
| BUILD-01 | Configure runtime and model — C2, C5–C6; §2.7; D1 | Versioned model/reasoning/tier/limit settings, override rules, locked host dependencies and explicit delegation configuration wired into the runner. | Meets completion criterion | [config.py](../src/accounting_finance_agent/config.py), [agent.py](../src/accounting_finance_agent/agent.py), [runner](../src/accounting_finance_agent/__main__.py) and [uv.lock](../uv.lock) supply the named baseline and wiring. Source-reviewed; runtime checks pending. Sandbox image belongs to BUILD-03; pricing/accounting/enforcement belongs to BUILD-06/07. |
| BUILD-02 | Configure context, skills and planning — C1–C2; §2.7 | Request/history context, selected read-only references/skills, todo state and pinned framework compaction wired in; record compaction configuration and document owner guidance updates. | Meets completion criterion | [agent.py](../src/accounting_finance_agent/agent.py), [knowledge.py](../src/accounting_finance_agent/knowledge.py), [runtime.py](../src/accounting_finance_agent/runtime.py) and [owner procedure](operating-guide.md#versioned-excel-trial-profile) supply the selected behavior. Source-reviewed; no known missing implementation within this scope. Isolation, retention and failure behavior still need evaluation. |
| BUILD-03 | Configure sandbox and file/code tools — C2, C5, C7; §4.2 | Sandbox/tool contracts, immutable image/package definition, credential wiring, source protection and filesystem/network restrictions configured. | Meets completion criterion | [sandbox.py](../src/accounting_finance_agent/sandbox.py), [provider.py](../src/accounting_finance_agent/provider.py), [workspace.py](../src/accounting_finance_agent/workspace.py) and [image release](../environments/finance/excel-v1-release.json) configure the frozen environment, namespace-enforced network boundary and protected input detection. Live probes passed; provider proxy alone was insufficient. [§11](#11-build-progress). |
| BUILD-04 | Implement artifact creation and validation — C3, C9; §2.3 | Workbook creation, LibreOffice recalculation, saved formula caches, preview generation and required-artifact/check gates integrated. Independent graders are BUILD-09. | Meets completion criterion | [recalculate.py](../skills/file-delivery-validation/recalculate.py), [spreadsheets.py](../src/accounting_finance_agent/spreadsheets.py) and runner gates provide final XLSX conversion/caches, PDF/PNG evidence and required-output checks. Live conversion returned cached value 5 for =2+3. Financial/visual benchmark evaluation remains TEST-02. |
| BUILD-05 | Implement persistence and transfer — C4, C7; §4.2 | Thread state/files, intermediate exports, loss/conflict reporting, transfer caps, backup/retention and owner deletion procedures implemented. | Meets completion criterion | [workspace.py](../src/accounting_finance_agent/workspace.py), [lifecycle.py](../src/accounting_finance_agent/lifecycle.py), sandbox/tool hooks and [retention command](../scripts/manage_retention.py) implement checkpoints, caps, consistent backup, closure/retention/deletion and explicit loss/failure reporting. Backup/retention engineering checks pass; no real retention deletion was executed. |
| BUILD-06 | Implement permissions and budgets — C5; §§2.2, 2.7 | Versioned rate card, conservative dollar reservations, complete API-attempt accounting, remaining-time enforcement and access/budget stop paths connected. Include retries and compaction. | Meets completion criterion | [budget.py](../src/accounting_finance_agent/budget.py), [rate card](../config/model-pricing.json), hard phase deadlines and namespace execution connect cost/time/access enforcement. Every synchronous HTTP attempt, including compaction, is metered; unknown usage retains reservations. Unpriced/direct non-image/hidden-history/async requests fail closed; embedded images use provider token preflight. Pricing was checked against provider documentation; actual billing reconciliation remains Test/Release work. |
| BUILD-07 | Implement outcomes and recovery — C2, C4–C5; §2.2 | Unified five-retry ceiling, eligible-error handling, visible backoff, shared deadlines/budgets, accurate partial/failure outcomes and bounded preservation/cleanup. | Meets completion criterion | HTTP and safe-read retry controllers, SDK retry disabling, outcome checks and shared work/cleanup deadlines are connected in [budget.py](../src/accounting_finance_agent/budget.py), [file_metadata.py](../src/accounting_finance_agent/file_metadata.py), [runner](../src/accounting_finance_agent/__main__.py) and sandbox lifecycle. Unsafe/uncertain writes are not replayed. Targeted retry/deadline tests pass. |
| BUILD-08 | Implement evidence and review — C3, C6; §§2.4, 2.7 | Persist source/output/configuration identities, prompt/middleware/dependency versions, provider usage/pricing, sandbox package identity, actual-check records and version-specific approvals. | Meets completion criterion | [provenance.py](../src/accounting_finance_agent/provenance.py), HTTP usage/rate/provider records, sandbox inventory events, existing hashes/check logs and approvals implement the evidence chain. Manifests include pricing/image-release identities. Full benchmark walkthrough remains TEST-05. |
| BUILD-09 | Create cases and graders — §§3.2–3.3 | Separate agent inputs and evaluator answers; executable independent graders, human rubrics, requirement/case links, reset/repetition controls and seeded-defect fixtures. | Meets completion criterion | [versioned inputs/oracle/rubric](../evaluations/excel-v4/), [original fixture generator](../scripts/prepare_excel_benchmark.py), [grader](../scripts/grade_excel_benchmark.py), [defect seeder](../scripts/seed_excel_defects.py) and [series runner](../scripts/run_excel_series.py) are implemented. Four seeded defect paths are detected. Series records fixture/configuration hashes and every outcome; current trial results and owner review are tracked under TEST-02. |
| BUILD-10 | Configure monitoring — §§4–5 | Signal collection, owner review/response procedures, access/retention and stop/recovery controls connected; alerts only if selected. | Meets completion criterion | [monitor_runs.py](../scripts/monitor_runs.py), [retention workflow](../scripts/manage_retention.py), API/transfer/check signals and [owner operating procedures](operating-guide.md#versioned-excel-trial-profile) connect monitoring, review, stop/recovery and retention. Hosted deletion is queued by exact root IDs and verified later; no deletion was performed. Operating cadence remains MON-01–03. |

### Verification and evaluation follow-up

These checks remain required even when the corresponding Build row is complete. Basic execution/configuration checks are recorded here alongside broader behavioral evaluations; none is implied by a source-reviewed Build status.

| Build work | Checks and evaluations | Evidence owner |
|---|---|---|
| BUILD-01 | Profile selection/overrides, provider model/tier/account access, configured limits and absence of delegation tools/child calls. | TEST-01, TEST-04, TEST-05 |
| BUILD-02 | Reference listing/read/search isolation, skill/todo wiring, profile switching, compaction retention, corrections and summarizer failure. | TEST-01, TEST-03, TEST-04, TEST-06 |
| BUILD-03 | Actual image/packages, tool operation, network/filesystem boundaries and input protection. | TEST-02, TEST-03, TEST-04 |
| BUILD-04 | Correct formulas/cached values, completed outputs and human visual review across the selected runs. | TEST-02 |
| BUILD-05 | Export/restart/loss/conflict/size/retention/deletion cases. | TEST-03, TEST-06 |
| BUILD-06 | Dollar/time/call exhaustion, usage reconciliation, retry/compaction accounting and denied-access cases. | TEST-04, TEST-06 |
| BUILD-07 | Retry eligibility/ceilings, incomplete responses, uncertain writes and cleanup failures. | TEST-06 |
| BUILD-08 | Saved manifest/provider identities, trace reconstruction, actual checks and stale-approval rejection. | TEST-05 |
| BUILD-09 | Graders detect seeded defects; independent expected answers and three-run results are recorded. | TEST-02, plus applicable TEST-01/03–06 |
| BUILD-10 | Signals and review/response procedures operate as intended; continuing review and retention are performed. | TEST-05/06, REL-01, MON-01–03 |

**Configure gate — met for the selected implementation scope:** BUILD-01–10 have their configured components, evaluation assets and operating procedures present and connected. Evidence includes source review, 78 offline checks, compiled tool inspection and a live frozen-image/network/recalculation probe. This is readiness to evaluate the controlled synthetic trial, not a benchmark pass or business-use release. The strict benchmark runner requires a POSIX host and the namespace-capable image.

## 3. Evaluate the foundation

Cover shared behavior and operating requirements alongside reusable file work, following spec §3. Use code graders for precise outcomes and calibrated judgment for meaning or quality. Reuse evidence across requirements where the case actually exercises them; add targeted failure/boundary cases and repeat model-dependent trials.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| TEST-01 | E-PLAT-1 — C1–C3, C8 / SC-1 | Profile/override and context/skill/todo wiring checks; representative CSV, missing/conflicting-input, repeated compaction, revision-reference and selected delegation cases; compare configuration candidates with independent outputs/rubric and total usage/latency. | Meets completion criterion | Seven live context cases pass under the unchanged-output rubric, including two actual summarizer cycles that retain and apply the identifier, authoritative correction, task scope and synthetic facts. This does not establish broad task consistency. [test-gate follow-up](history/test-gate-followup-2026-10-25.md). |
| TEST-02 | E-ART-1 — C3, C9–C11 / SC-1 | Check the graders against seeded defects, then three clean fresh-thread runs of the §3.2 Excel benchmark: fixed inputs/configuration, independent numbers, detailed grounded analysis, saved recalculated values, visual review and preservation. Each passes; later C10–C11/package checks when selected. | Meets completion criterion | Final fixture v4 series `df3feccd-26d4-44e0-8c7c-5ae0adfd1edb` passes all three numerical, independent recalculation, grounding and assistant visual checks. Sources, output hashes, traces and limits agree. Owner explicitly approved all three exact output manifests in chat on October 26, 2026; approvals are recorded in the work log. Earlier failures are retained. [Follow-up](history/test-gate-followup-2026-10-25.md). |
| TEST-03 | E-FILE-1 — C4, C7 / SC-2 | Task isolation/file lookup, source preservation, restart/abrupt-loss recovery under the declared policy, overlap rejection (or coordination if enabled), exclusions, conflicts and transfer failure. | Meets completion criterion | Selected file/recovery contract covered by offline transfer/isolation/conflict/failure checks plus live protected-source, abrupt-exit recovery, overlap and corrected delete/recreate probes. Unknown external business effects are outside this result. [Test report](history/test-phase-2026-10-25.md). |
| TEST-04 | E-CTRL-1 — C5 / SC-3 | Allowed/denied/adversarial cases, reference-route isolation, absence of delegation when disabled, provider access, actual filesystem/network/identity checks and enforced shared budgets. | Meets completion criterion | Live injection/context cases pass 7/7; neither case invoked mutating or execution tools and approved reference hashes stayed unchanged. The separately selected network and profile boundaries are in the follow-up report. [test-gate follow-up](history/test-gate-followup-2026-10-25.md). |
| TEST-05 | E-PROV-1 — C6 / SC-3, SC-4 | Input-to-output evidence walkthrough, saved effective settings/provider/sandbox identities and usage records, stale-approval cases, separate approval scopes and complete configuration references. | Meets completion criterion | All three source/configuration/provider/image/output/hash/backup/trace walks agree; stale-approval probe passes in disposable records. Owner approval of all three final output manifests is recorded; reusable-asset promotion is deferred. [Current evidence](history/test-gate-followup-2026-10-25.md); [earlier report](history/test-phase-2026-10-25.md). |
| TEST-06 | E-REC-1 — C2, C4, C5 / SC-7 | Startup failure, timeout after possible effect, incomplete response, budget exhaustion, transfer/cleanup or summarizer failure and safe resume/retry. | Meets completion criterion | Three integrated offline recovery cases pass, including lost-response write preservation, rejection of nonempty incomplete responses, and the single six-attempt summary/HTTP retry ceiling. Earlier live boundary probes and the live context compaction case provide complementary evidence. See the [test-gate follow-up](history/test-gate-followup-2026-10-25.md). |

**Historical foundation Test gate — met for the selected synthetic Excel scope under the v3 runtime:** TEST-01–06 have their required evidence, including owner approval of all three exact final output manifests on October 26, 2026. The v5 runtime subsequently completed the three-trial Excel series and owner review, and selected foundation checks were repeated. [Live ceiling probes](evaluations/v5-live-ceiling-probes-2026-11-05.md) confirmed both controls, subject to a separate graph recursion limit; the [v5 foundation report](evaluations/foundation-v5-2026-11-05.md) describes the remaining scope. Earlier failures remain recorded. This does not establish wider finance reliability or promote a Release gate. [v3 evidence](history/test-gate-followup-2026-10-25.md) · [v5 Excel results](evaluations/excel-v5-results.md).

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
| REL-01 | E-REL-1 readiness review — §§4.1–4.3 / SC-5 | Release record: configuration/scope, owner, identities, storage, data/trace policy, budgets, monitoring, compatible state/memory and rehearsed stop/recovery/rollback. | Partial | [Release design](agent-spec.md#4-deploy-requirements-and-design) and recovery utilities exist; no accepted current-benchmark evidence/release record or complete rehearsal. [§10.10](history/repository-assessment.md#1010-monitoring-and-release). |
| REL-02 | Conduct approved parallel operation — §4.1 | Representative comparison with the normal process; consequential writes suppressed; discrepancies reviewed against agreed thresholds. | Missing | No recorded parallel-operation comparison for the selected scope found; synthetic smoke runs do not establish this. |
| REL-03 | Authorize supervised use — §4.1 | Explicit decision for a defined scope; every output reviewed; operational results, limits and recovery meet the stage criteria. | Missing | No approved supervised-use release record for the selected scope found. Per-file review commands alone do not authorize release. |

**Release gate — not met:** no approved release record for this scope. Authorize only the recorded stage and scope. Local deployment is a valid choice; supervised use may remain the endpoint. Broader access or autonomy needs separate evidence and approval.

## 6. Monitor and improve

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| MON-01 | Operate per-run checks and response paths — §5.2 | Versioned run/outcome records, applicable checks, owner review and demonstrated response; alert routing when selected. | Partial | Run/structure records and review commands exist; current-profile usage/retention and demonstrated per-run response remain. [§10.10](history/repository-assessment.md#1010-monitoring-and-release). |
| MON-02 | Review outputs and trends — §5.2 | Reviews at agreed cadence; quality, corrections, costs and workload comparisons by task/configuration; decisions recorded. | Missing | Review cadence is planned; no three-run benchmark review or ongoing trend records against the selected configuration found. |
| MON-03 | Diagnose findings and release fixes — §5.3 | Evidence, impact, owner and response; useful regression cases, verified fixes or accepted limitations; memory/state compatibility considered. | Partial | [Engineering fixes/regressions](history/engineering-checks.md#fixes-made-during-this-pass) document earlier improvement work; current benchmark incident/change/release loop is not established. |

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
2. Locate evidence appropriate to the stage: decisions/design for planning, code/configuration for build, results for evaluation, and readiness/approval records for release. Record exact paths and applicable versions.
3. Distinguish design decisions from implementation, behavioral verification and release approval. Do not hold a planning item open for downstream implementation, or a Build item open solely for unrun evaluation. Record source review, execution checks and behavioral evaluation separately; an observed implementation defect does reopen Build. Check whether old evidence applies to the current configuration and criterion.
4. Set the assessment and link evidence. Record concrete gaps or necessary changes; reuse suitable work instead of rebuilding it.
5. For a task covering multiple components, record each finding. Use **Partial** if some required components meet the criterion and others remain incomplete; keep unreviewed components explicitly **Not assessed**.
6. Reconcile stage gates only after reviewing their required evidence. Keep original records available for comparison.

## 10. Repository assessment — October 25, 2026

The [initial assessment](history/repository-assessment.md#10-repository-assessment--october-25-2026) is retained as history. Its open gaps describe the earlier repository state; use the stage tables above and their versioned evidence for current decisions.

## 11. Build progress

The [build chronology](history/repository-assessment.md#11-build-progress) records implementation increments, demonstrations, configuration changes, and earlier Test results.

## Change log

| Version | Date | Change |
|---|---|---|
| v0.32 | 2026-11-11 | Moved detailed assessment/build history into a separate document; retained stage criteria, statuses, evidence, and section links. |

[Earlier revisions](history/repository-assessment.md#change-log).
