# Accounting & Finance Agent — Delivery and Assessment Plan

| Field | Value |
|---|---|
| Version | v0.19 design draft · October 25, 2026 |
| Owner | Neil Yee; assign additional owners during planning. |
| Specification and design | [Agent specification and design](agent-spec.md) v0.24 |
| Assessment baseline | Every item is **Not assessed**. This does not mean the implementation is absent or needs rebuilding. |

This plan follows the [ADLC](mental-model/02-adlc.md). It defines work and acceptance evidence independently of the repository's implementation. During the later review, inspect existing code, configuration, and results against these items; record evidence and gaps before deciding what to build.

**Assessment values:** Not assessed · Missing · Partial · Meets completion criterion. Keep evidence links beside each finding. Code presence can satisfy a build item; evaluation items require results, and release items require the corresponding approval. An unchecked gate is unassessed, not a declaration that it failed.

**Scope first:** select the next trial or release under spec §1. Deferred features stay unassessed and do not block unrelated work. Include finance, Asana, delegation, memory and concurrency checks when the selected scope uses them.

The owner has selected the [two-month Excel benchmark](agent-spec.md#32-starter-evaluation-tasks) and [trial settings](agent-spec.md#27-runtime-configuration-and-customization). The [fixture and rubric](evaluations/excel-benchmark.md) and labeled defaults now settle the design choices. Work items remain unassessed: materialized cases, account/tool support, configuration and enforcement still need evidence.

## 1. Plan

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| PLAN-01 | Agree objective, boundaries, capabilities and criteria — §§1–3 | Reviewed anatomy and C1–C12 behavior/work/operating requirements → design → SC-1–SC-7 mapping; assumptions and exclusions explicit. | Not assessed | — |
| PLAN-02 | Define task outputs and evaluation plan — §§2.3, 3.1–3.3; D2, D3 | Materialize the selected fixture/rubric into separate agent inputs and independent evaluator answers; retain four dimensions, three-run design, thresholds and seeded-defect checks. | Not assessed | — |
| PLAN-03 | Select configuration and release design — §§2, 4; [deployment design](agent-spec.md#42-deployment-architecture-and-trust-boundaries); D1, D5 | Runtime choices and rationale per §2.7; host/storage, identities, concurrency, data policy, transfer limits and stop/recovery/rollback plan. | Not assessed | — |
| PLAN-04 | Define monitoring and response — §5.2; D4 | SC-1–SC-7 signals, data sources, thresholds, owners, cadence, trace access/retention and incident responses. | Not assessed | — |
| PLAN-05 | Define references and memory policy — C1, C4–C6; §§2.7, 5.3; D7 | Ownership, scope, versions, read/write rules, retention/deletion, compatibility and promotion rules. | Not assessed | — |
| PLAN-06 | Cross-check architecture and task coverage — §§2–6 | Architecture views cover agent execution, evaluation/operation and deployment boundaries; each requirement has work and evidence links. | Not assessed | — |

**Plan gate:** approve the design and evaluation/release/monitoring plans for the selected scope. Resolve decisions needed for that scope; record later decisions and their prerequisites.

## 2. Configure the shared foundation

Work may reuse or adapt existing implementation after assessment. Start with framework features and the shared model/tool loop. Treat concrete scenarios as evaluation cases; introduce dedicated tools or middleware when a required boundary or observed failure calls for them.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| BUILD-01 | Configure reproducible runtime and model — C2, C5–C6; [runtime design](agent-spec.md#runtime-and-tool-contracts--c2-c5); D1 | Verify account access and freeze the documented gpt-6-luna/high Standard rate card/profile; verify effective secondary limits, framework compaction and absence of delegation; retain versioned settings/overrides. | Not assessed | — |
| BUILD-02 | Configure context, skills and planning — C1–C2; [context design](agent-spec.md#context-assembly--c1-c2) | Request/history/reference selection, source IDs, approved skills, todo state; versioned compaction prompt/trigger, retained history, retrieval and failure behavior per §2.7. | Not assessed | — |
| BUILD-03 | Configure sandbox and file/code tools — C2, C5, C7; [deployment design](agent-spec.md#42-deployment-architecture-and-trust-boundaries) | Tool contracts, working-copy boundary, package/image configuration, host/sandbox credentials and scoped access. | Not assessed | — |
| BUILD-04 | Implement artifact creation and validation — C3, C8–C11; §2.3 | First benchmark: openpyxl + selected LibreOffice image, saved recalculated formula values, independent figures and rendered visual review per §3.2 and its fixture/rubric; no final rewrite that discards caches. | Not assessed | — |
| BUILD-05 | Implement persistent threads and file transfer — C4, C7; [persistence design](agent-spec.md#state-files-and-recovery--c4-c7) | Verify selected SQLite/thread folders, application-driven export milestones, local archive/retention and transfer limits (§4.2); record any work lost after the last confirmed durable export. | Not assessed | — |
| BUILD-06 | Implement permissions and budgets — C5; [runtime](agent-spec.md#runtime-and-tool-contracts--c2-c5) and [access design](agent-spec.md#access-and-approval-enforcement--c3-c5-c7) | Enforced 10-minute/US$1 model-API limits, conservative per-call cost reservation including retries/compaction/delegation, supplied-data-only scope and access restrictions; evidence of budget exhaustion handling. | Not assessed | — |
| BUILD-07 | Implement outcomes and recovery — C2, C4–C5; §2.2 | At most five eligible retries including SDK retries; visible attempt counts, backoff and shared budgets; explicit partial/failure states, write reconciliation and bounded preservation/cleanup. | Not assessed | — |
| BUILD-08 | Implement provenance and review — C3, C6; [evidence design](agent-spec.md#evidence-and-configuration--c6) | Traces, work log, effective configuration/overrides and prompt/middleware/subagent versions, source/output identities, actual-check reports and version-specific approvals. | Not assessed | — |
| BUILD-09 | Create cases and graders — §§3.2–3.3 | Versioned case IDs linked to requirements, criteria, evaluation layers and functions exercised; fixtures/rubrics, expected results, thresholds, repetitions, setup/reset and seeded defects to check graders. | Not assessed | — |
| BUILD-10 | Configure operational monitoring — §§4–5 | Applicable automatic checks, signal collection, owner review/routing, access/retention and stop/recovery controls; alerts when the operating model requires them. | Not assessed | — |

**Configure gate:** a representative task completes the intended path; fixtures, graders, instrumentation, and recovery procedures are ready for evaluation. Completion of this gate does not establish task quality across the planned scope.

## 3. Evaluate the foundation

Cover shared behavior and operating requirements alongside reusable file work, following spec §3. Use code graders for precise outcomes and calibrated judgment for meaning or quality. Reuse evidence across requirements where the case actually exercises them; add targeted failure/boundary cases and repeat model-dependent trials.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| TEST-01 | E-PLAT-1 — C1–C3, C8 / SC-1 | Representative CSV, missing/conflicting-input, repeated compaction, revision-reference and selected delegation cases; compare configuration candidates with independent outputs/rubric and total usage/latency. | Not assessed | — |
| TEST-02 | E-ART-1 — C3, C9–C11 / SC-1 | Three clean fresh-thread runs of the §3.2 Excel benchmark: fixed inputs/configuration, independent numbers, detailed grounded analysis, saved recalculated values, visual review and preservation. Each passes; later C10–C11/package checks when selected. | Not assessed | — |
| TEST-03 | E-FILE-1 — C4, C7 / SC-2 | Task isolation/file lookup, source preservation, restart/abrupt-loss recovery under the declared policy, overlap rejection (or coordination if enabled), exclusions, conflicts and transfer failure. | Not assessed | — |
| TEST-04 | E-CTRL-1 — C5 / SC-3 | Allowed/denied/adversarial cases, actual filesystem/network/identity checks and enforced shared budgets. | Not assessed | — |
| TEST-05 | E-PROV-1 — C6 / SC-3, SC-4 | Input-to-output evidence walkthrough, stale-approval cases, separate approval scopes and complete configuration references. | Not assessed | — |
| TEST-06 | E-REC-1 — C2, C4, C5 / SC-7 | Startup failure, timeout after possible effect, incomplete response, budget exhaustion, transfer/cleanup failure and safe resume/retry. | Not assessed | — |

**Foundation gate:** mandatory criteria pass for the defined cases and repetitions, with case/grader/configuration versions, limitations, and a recorded decision. Preserve passing capability cases as regressions.

## 4. Define and evaluate the first finance workflow

Apply this section when a business workflow such as C12 is selected. It is not a prerequisite for an Excel-only trial or release.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| FIN-01 | Confirm workflow, scope and independent answers — §3.2; D2, D3 | Bank reconciliation or an explicitly selected alternative; representative inputs, expected matches/exceptions/balances, critical thresholds and review rubric. | Not assessed | — |
| FIN-02 | Configure skill and evaluation materials — C1–C7, C12; §3.3 | Procedure, approved references, access/packages, supporting calculations and versioned normal/edge/adversarial cases. | Not assessed | — |
| FIN-03 | E-FIN-1 and affected regressions — C12 / SC-1 | Critical finance checks and representative human review pass; source preservation, artifact consistency and foundation regressions included. | Not assessed | — |

**Finance gate:** accept only the evaluated task scope. Draft proposed entries do not authorize posting. A demonstration does not replace independent financial and presentation checks.

## 5. Release within the approved scope

Prerequisite: foundation and work-capability evidence for the selected release; finance evidence when that workflow is included.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| REL-01 | E-REL-1 readiness review — §§4.1–4.3 / SC-5 | Release record: configuration/scope, owner, identities, storage, data/trace policy, budgets, monitoring, compatible state/memory and rehearsed stop/recovery/rollback. | Not assessed | — |
| REL-02 | Conduct approved parallel operation — §4.1 | Representative comparison with the normal process; consequential writes suppressed; discrepancies reviewed against agreed thresholds. | Not assessed | — |
| REL-03 | Authorize supervised use — §4.1 | Explicit decision for a defined scope; every output reviewed; operational results, limits and recovery meet the stage criteria. | Not assessed | — |

**Release gate:** authorize only the recorded stage and scope. Local deployment is a valid choice; supervised use may remain the endpoint. Broader access or autonomy needs separate evidence and approval.

## 6. Monitor and improve

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| MON-01 | Operate per-run checks and response paths — §5.2 | Versioned run/outcome records, applicable checks, owner review and demonstrated response; alert routing when selected. | Not assessed | — |
| MON-02 | Review outputs and trends — §5.2 | Reviews at agreed cadence; quality, corrections, costs and workload comparisons by task/configuration; decisions recorded. | Not assessed | — |
| MON-03 | Diagnose findings and release fixes — §5.3 | Evidence, impact, owner and response; useful regression cases, verified fixes or accepted limitations; memory/state compatibility considered. | Not assessed | — |

**Monitoring requirement:** every material finding has an accountable response. Trace completion alone does not establish correctness or approval.

## 7. Add the Asana task workflow

Select this integration after the foundation and dispatched work have relevant evidence. Apply the finance gate if it will dispatch finance workflows. These are planned dependencies, not findings about current code.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| ASANA-01 | Define eligibility, identity, triggers and approvals — §2.2; D6 | Task/thread mapping, permitted publication, status transitions, actionable feedback, deduplication, locking and version-specific review semantics. | Not assessed | — |
| ASANA-02 | Configure intake and execution ownership — C1, C4–C7; §2.2 | Authorized task/context collection, eligible trigger handling, thread restoration, concurrency control and operation records. | Not assessed | — |
| ASANA-03 | Configure publication and revision — §2.2 | Scoped status/summary/link updates, review of identified versions, same-thread revisions, and suppression of agent-generated trigger loops. | Not assessed | — |
| ASANA-04 | E-ASANA-1 plus affected regressions — §3.3 / SC-6 | Normal/revision/informational/duplicate/out-of-order/concurrent/failure/restart cases; approved sample/repetition plan and no duplicate effects. | Not assessed | — |
| ASANA-05 | Review readiness and staged rollout — §§4–5 | Updated E-REL-1 evidence for new identity/access, trigger stop/recovery, monitoring and approved rollout scope. | Not assessed | — |

## 8. Later changes

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| CHANGE-01 | Add a skill, tool, connector or workload — §§2, 3.2–3.3, 5.3 | New objective/scope, design/access impact, capability cases, relevant regressions and release/monitoring decision. | Not assessed | — |
| CHANGE-02 | Change runtime settings, middleware, subagents, shared guidance or memory policy — C1–C6; §§2.7, 5.3; D1, D7 | Impact-based evaluation; representative existing/stale/conflicting state; migration/invalidation, rollback and separate asset approval where required. | Not assessed | — |

## 9. Repository review procedure

Use the spec’s [implementation inventory](agent-spec.md#26-implementation-inventory) to select shared building blocks. This task list is the single place for implementation status, paths, gaps and evidence. Update the spec when the intended requirements or design change.

1. Select a requirement/task and record the requirement IDs, functions exercised and evaluation cases it covers, its intended behavior and completion evidence.
2. Locate relevant code/configuration and existing evaluation records. Record exact paths, versions and results.
3. Distinguish implementation evidence from behavioral verification and release approval. Check whether old evidence applies to the current configuration and criterion.
4. Set the assessment and link evidence. Record concrete gaps or necessary changes; reuse suitable work instead of rebuilding it.
5. For a task covering multiple components, record each finding. Use **Partial** if some required components meet the criterion and others remain incomplete; keep unreviewed components explicitly **Not assessed**.
6. Reconcile stage gates only after reviewing their required evidence. Keep original records available for comparison.

## Change log

| Version | Date | Change |
|---|---|---|
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
