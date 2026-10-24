# Accounting & Finance Agent — Delivery and Assessment Plan

| Field | Value |
|---|---|
| Version | v0.7 design draft · October 24, 2026 |
| Owner | Neil Yee; assign additional owners during planning. |
| Specification | [Agent specification](agent-spec.md) v0.11 |
| Architecture | [Target architecture](architecture.md) v0.11 |
| Assessment baseline | Every item is **Not assessed**. This does not mean the implementation is absent or needs rebuilding. |

This plan follows the [ADLC](mental-model/02-adlc.md). It defines work and acceptance evidence independently of the repository's implementation. During the later review, inspect existing code, configuration, and results against these items; record evidence and gaps before deciding what to build.

**Assessment values:** Not assessed · Missing · Partial · Meets completion criterion. Keep evidence links beside each finding. Code presence can satisfy a build item; evaluation items require results, and release items require the corresponding approval. An unchecked gate is unassessed, not a declaration that it failed.

## 1. Plan

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| PLAN-01 | Agree objective, boundaries, capabilities and criteria — §§1–4 | Reviewed scope and C1–C12 by scope → design → SC-1–SC-7 mapping; assumptions and exclusions explicit. | Not assessed | — |
| PLAN-02 | Define task outputs and evaluation plan — §§3, 5.1; D2, D3 | Formats, independent answers/rubrics, cases, four dimensions, thresholds, sample sizes, budgets and grader checks. | Not assessed | — |
| PLAN-03 | Select configuration and release design — §§2, 5.2; [architecture §4](architecture.md#4-deployment-and-trust-boundaries); D1, D5 | Version/provider choices, host/storage, identities, concurrency, data policy, transfer limits and stop/recovery/rollback plan. | Not assessed | — |
| PLAN-04 | Define monitoring and response — §5.3; D4 | Signals, data sources, thresholds, owners, cadence, trace access/retention and incident responses. | Not assessed | — |
| PLAN-05 | Define references and memory policy — C1, C4–C6; §5.4; D7 | Ownership, scope, versions, read/write rules, retention/deletion, compatibility and promotion rules. | Not assessed | — |
| PLAN-06 | Cross-check architecture and task coverage — §§2–6 | Four views cover responsibilities, flows, failures and trust boundaries; each requirement has work and evidence links. | Not assessed | — |

**Plan gate:** approve the design and evaluation/release/monitoring plans for the selected scope. Resolve decisions needed for that scope; record later decisions and their prerequisites.

## 2. Configure the shared foundation

Work may reuse or adapt existing implementation after assessment.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| BUILD-01 | Configure reproducible runtime and model — C2, C5–C6; [runtime design](architecture.md#42-runtime-and-tool-contracts--c2-c5); D1 | Dependency/configuration manifest, provider settings and invocation path; a runnable minimal task. | Not assessed | — |
| BUILD-02 | Configure context, skills and planning — C1–C2; [context design](architecture.md#41-context-assembly--c1-c2) | Request/history/reference selection, source IDs, approved skills, todo state and context-limit behavior. | Not assessed | — |
| BUILD-03 | Configure sandbox and file/code tools — C2, C5, C7; [architecture §4](architecture.md#4-deployment-and-trust-boundaries) | Tool contracts, working-copy boundary, package/image configuration, host/sandbox credentials and scoped access. | Not assessed | — |
| BUILD-04 | Implement artifact creation and validation — C3, C8–C11; §3.3 | Selected C8–C11 paths with declared supported features; read/revision/export, independent calculations, formula/recalculation, presentation and cross-file checks. | Not assessed | — |
| BUILD-05 | Implement persistent threads and file transfer — C4, C7; [persistence design](architecture.md#43-state-files-and-recovery--c4-c7) | State/file stores, task ownership, checkpoints, manifests, versions, conflicts and transfer exclusions/limits. | Not assessed | — |
| BUILD-06 | Implement permissions and budgets — C5; [runtime](architecture.md#42-runtime-and-tool-contracts--c2-c5) and [access design](architecture.md#44-access-and-approval-enforcement--c3-c5-c7) | Checks across model/actions/storage/delivery; bounded calls/time/retries and delegation; enforced reference/source restrictions. | Not assessed | — |
| BUILD-07 | Implement outcomes and recovery — C2, C4–C5; §3.2 | Explicit partial/failure/review states, operation records, retry eligibility, reconciliation and cleanup-failure handling. | Not assessed | — |
| BUILD-08 | Implement provenance and review — C3, C6; [evidence design](architecture.md#45-evidence-and-configuration--c6) | Traces, work log, configuration/source/output identities, actual-check reports and version-specific approval records. | Not assessed | — |
| BUILD-09 | Create cases and graders — §5.1 | Versioned fixtures/rubrics, thresholds, repetitions, setup/reset, expected results and seeded defects to check graders. | Not assessed | — |
| BUILD-10 | Configure operational monitoring — §§5.2–5.3 | Automatic checks, signal collection, alerts/review routing, access/retention and stop/recovery controls. | Not assessed | — |

**Configure gate:** a representative task completes the intended path; fixtures, graders, instrumentation, and recovery procedures are ready for evaluation. Completion of this gate does not establish task quality across the planned scope.

## 3. Evaluate the foundation

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| TEST-01 | E-PLAT-1 — C1–C3, C8 / SC-1 | Representative CSV, missing/conflicting-input and repeat cases; independent outputs/rubric and budget results. | Not assessed | — |
| TEST-02 | E-ART-1 — C3, C9–C11 / SC-1 | Separate C9–C11 checks and composed packages: reading/revision, supported features, conversion fidelity, seeded defects, correct formulas/figures and presentation. | Not assessed | — |
| TEST-03 | E-FILE-1 — C4, C7 / SC-2 | Task isolation/file lookup, source preservation, state/file restart, concurrent edits, exclusions, conflicts and transfer-failure cases. | Not assessed | — |
| TEST-04 | E-CTRL-1 — C5 / SC-3 | Allowed/denied/adversarial cases, actual filesystem/network/identity checks and enforced shared budgets. | Not assessed | — |
| TEST-05 | E-PROV-1 — C6 / SC-3, SC-4 | Input-to-output evidence walkthrough, stale-approval cases, separate approval scopes and complete configuration references. | Not assessed | — |
| TEST-06 | E-REC-1 — C2, C4, C5 / SC-7 | Startup failure, timeout after possible effect, incomplete response, budget exhaustion, transfer/cleanup failure and safe resume/retry. | Not assessed | — |

**Foundation gate:** mandatory criteria pass for the defined cases and repetitions, with case/grader/configuration versions, limitations, and a recorded decision. Preserve passing capability cases as regressions.

## 4. Define and evaluate the first finance workflow

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| FIN-01 | Confirm workflow, scope and independent answers — §3.1; D2, D3 | Bank reconciliation or an explicitly selected alternative; representative inputs, expected matches/exceptions/balances, critical thresholds and review rubric. | Not assessed | — |
| FIN-02 | Configure skill and evaluation materials — C1–C7, C12; §5.1 | Procedure, approved references, access/packages, supporting calculations and versioned normal/edge/adversarial cases. | Not assessed | — |
| FIN-03 | E-FIN-1 and affected regressions — C12 / SC-1 | Critical finance checks and representative human review pass; source preservation, artifact consistency and foundation regressions included. | Not assessed | — |

**Finance gate:** accept only the evaluated task scope. Draft proposed entries do not authorize posting. A demonstration does not replace independent financial and presentation checks.

## 5. Release within the approved scope

Prerequisite: the required foundation and finance evidence for that release.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| REL-01 | E-REL-1 readiness review — §5.2 / SC-5 | Release record: configuration/scope, owner, identities, storage, data/trace policy, budgets, monitoring, compatible state/memory and rehearsed stop/recovery/rollback. | Not assessed | — |
| REL-02 | Conduct approved parallel operation — §5.2 | Representative comparison with the normal process; consequential writes suppressed; discrepancies reviewed against agreed thresholds. | Not assessed | — |
| REL-03 | Authorize supervised use — §5.2 | Explicit decision for a defined scope; every output reviewed; operational results, limits and recovery meet the stage criteria. | Not assessed | — |

**Release gate:** authorize only the recorded stage and scope. Local deployment is a valid choice; supervised use may remain the endpoint. Broader access or autonomy needs separate evidence and approval.

## 6. Monitor and improve

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| MON-01 | Operate per-run checks and response paths — §5.3 | Versioned run/outcome records, applicable automatic checks, alert ownership and demonstrated response routing. | Not assessed | — |
| MON-02 | Review outputs and trends — §5.3 | Reviews at agreed cadence; quality, corrections, costs and workload comparisons by task/configuration; decisions recorded. | Not assessed | — |
| MON-03 | Diagnose findings and release fixes — §5.4 | Evidence, impact, owner and response; useful regression cases, verified fixes or accepted limitations; memory/state compatibility considered. | Not assessed | — |

**Monitoring requirement:** every material finding has an accountable response. Trace completion alone does not establish correctness or approval.

## 7. Add the Asana task workflow

Scope this work after the foundation and finance gates. These are planned dependencies, not assertions about whether code exists.

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| ASANA-01 | Define eligibility, identity, triggers and approvals — §3.2; D6 | Task/thread mapping, permitted publication, status transitions, actionable feedback, deduplication, locking and version-specific review semantics. | Not assessed | — |
| ASANA-02 | Configure intake and execution ownership — C1, C4–C7; §3.2 | Authorized task/context collection, eligible trigger handling, thread restoration, concurrency control and operation records. | Not assessed | — |
| ASANA-03 | Configure publication and revision — §3.2 | Scoped status/summary/link updates, review of identified versions, same-thread revisions, and suppression of agent-generated trigger loops. | Not assessed | — |
| ASANA-04 | E-ASANA-1 plus affected regressions — §5.1 / SC-6 | Normal/revision/informational/duplicate/out-of-order/concurrent/failure/restart cases; approved sample/repetition plan and no duplicate effects. | Not assessed | — |
| ASANA-05 | Review readiness and staged rollout — §§5.2–5.3 | Updated E-REL-1 evidence for new identity/access, trigger stop/recovery, monitoring and approved rollout scope. | Not assessed | — |

## 8. Later changes

| ID | Work / spec reference | Completion evidence required | Assessment | Evidence |
|---|---|---|---|---|
| CHANGE-01 | Add a skill, tool, connector or workload — §§3.1, 5.4 | New objective/scope, design/access impact, capability cases, relevant regressions and release/monitoring decision. | Not assessed | — |
| CHANGE-02 | Change model, shared guidance or memory policy — C1, C4–C6; §5.4; D7 | Impact-based evaluation; representative existing/stale/conflicting state; migration/invalidation, rollback and separate asset approval where required. | Not assessed | — |

## 9. Repository review procedure

1. Select a requirement/task and identify its intended behavior and completion evidence.
2. Locate relevant code/configuration and existing evaluation records. Record exact paths, versions and results.
3. Distinguish implementation evidence from behavioral verification and release approval. Check whether old evidence applies to the current configuration and criterion.
4. Set the assessment and link evidence. Record concrete gaps or necessary changes; reuse suitable work instead of rebuilding it.
5. Reconcile stage gates only after reviewing their required evidence. Keep original records available for comparison.

## Change log

| Version | Date | Change |
|---|---|---|
| v0.7 | 2026-10-24 | Pointed requirements to capability IDs and architecture details after removal of the spec shared-rules section; renumbered lifecycle references. |
| v0.6 | 2026-10-23 | Aligned work references with the combined capability/design table and shared rules; retained all assessment fields. |
| v0.5 | 2026-10-23 | Mapped work and evaluation items to the classified capability catalog; retained unassessed evidence fields. |
| v0.4 | 2026-10-23 | Replaced implementation-based statuses with an unassessed delivery plan; added capability/evaluation mappings, evidence fields and a later repository review procedure. |
| v0.3 and earlier | 2026-10-23 | Earlier task lists retained in Git history. |
