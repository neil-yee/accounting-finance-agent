# Accounting & Finance Agent — Delivery and Assessment Plan

| Field | Value |
|---|---|
| Version | v0.27 request ceiling revised · October 25, 2026 |
| Owner | Neil Yee; assign additional owners during planning. |
| Specification and design | [Agent specification and design](agent-spec.md) v0.27 |
| Assessment baseline | Initial review against spec v0.24; first build increment at `8eb7d90` reviewed against unchanged requirements in spec v0.25. Historical evidence is labeled; no new tests or paid runs. |

This plan follows the [ADLC](mental-model/02-adlc.md). Assessments below distinguish existing implementation, historical evidence and remaining gaps against the selected requirements. The initial review is in [§10](#10-repository-assessment--october-25-2026); subsequent build changes are in [§11](#11-build-progress). Reuse the foundation before adding missing behavior.

**Assessment values:** Not assessed · Missing · Partial · Meets completion criterion. Keep evidence links beside each finding. **Meets completion criterion** is the equivalent of checking off that row, for its stated scope. **Partial** means useful work exists but the full criterion is unmet. **Missing** means required implementation or evidence was not found in the inspected repository. Assess each item against its stage: planning requires documented decisions and an actionable design; build requires configured or implemented components; evaluation requires results; release requires readiness evidence and the corresponding approval. A gate is met only when its required evidence is complete. “Not met” can mean evidence is missing; it does not necessarily mean a test failed.

**Scope first:** select the next trial or release under spec §1. Deferred features stay unassessed and do not block unrelated work. Include finance, Asana, delegation, memory and concurrency checks when the selected scope uses them.

The owner has selected the [two-month Excel benchmark](agent-spec.md#32-starter-evaluation-tasks) and [trial settings](agent-spec.md#27-runtime-configuration-and-customization). The [fixture and rubric](evaluations/excel-benchmark.md) and labeled defaults now settle the design choices. All selected Build components are now implemented and connected. Their current evidence is in §11; benchmark evaluation and release approval remain outstanding.

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
| BUILD-09 | Create cases and graders — §§3.2–3.3 | Separate agent inputs and evaluator answers; executable independent graders, human rubrics, requirement/case links, reset/repetition controls and seeded-defect fixtures. | Meets completion criterion | [versioned inputs/oracle/rubric](../evaluations/excel-v1/), [preparer](../scripts/prepare_excel_benchmark.py), [grader](../scripts/grade_excel_benchmark.py), [defect seeder](../scripts/seed_excel_defects.py) and [series runner](../scripts/run_excel_series.py) are implemented. Four seeded defect paths are detected. Series records fixture/configuration hashes and every outcome; three paid trials remain TEST-02. |
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
| TEST-01 | E-PLAT-1 — C1–C3, C8 / SC-1 | Profile/override and context/skill/todo wiring checks; representative CSV, missing/conflicting-input, repeated compaction, revision-reference and selected delegation cases; compare configuration candidates with independent outputs/rubric and total usage/latency. | Partial | Historical CSV smoke and fake-model context/skill checks exist; no current-profile long-context/correction/three-run evidence. [§10.9](#109-cases-and-evaluation-evidence). |
| TEST-02 | E-ART-1 — C3, C9–C11 / SC-1 | Check the graders against seeded defects, then three clean fresh-thread runs of the §3.2 Excel benchmark: fixed inputs/configuration, independent numbers, detailed grounded analysis, saved recalculated values, visual review and preservation. Each passes; later C10–C11/package checks when selected. | Missing | No completed three-run series for the agreed Excel fixture/profile found. Earlier workbook demonstrations do not meet this criterion. [§10.9](#109-cases-and-evaluation-evidence). |
| TEST-03 | E-FILE-1 — C4, C7 / SC-2 | Task isolation/file lookup, source preservation, restart/abrupt-loss recovery under the declared policy, overlap rejection (or coordination if enabled), exclusions, conflicts and transfer failure. | Partial | Historical transfer, locks, checkpoint and conflict tests in [engineering results](engineering-checks.md); new export/retention/limits and abrupt-loss contract remain unevaluated. |
| TEST-04 | E-CTRL-1 — C5 / SC-3 | Allowed/denied/adversarial cases, reference-route isolation, absence of delegation when disabled, provider access, actual filesystem/network/identity checks and enforced shared budgets. | Partial | Reference-denial, HTTP reservation/retry and namespace checks now pass; live sandbox DNS/direct-IP/re-entry probes also pass. Complete adversarial/current-profile evaluation remains. [Build evidence](build-evidence.json). |
| TEST-05 | E-PROV-1 — C6 / SC-3, SC-4 | Input-to-output evidence walkthrough, saved effective settings/provider/sandbox identities and usage records, stale-approval cases, separate approval scopes and complete configuration references. | Partial | Historical approval/hash and persistence checks in [engineering results](engineering-checks.md); full effective-profile/input-to-output walkthrough for the benchmark remains. |
| TEST-06 | E-REC-1 — C2, C4, C5 / SC-7 | Startup failure, timeout after possible effect, incomplete response, budget exhaustion, transfer/cleanup or summarizer failure and safe resume/retry. | Partial | Lifecycle/runner, five-retry, spend-reservation and hard-deadline checks pass offline; full task-level timeout/uncertain-write/lost-provider recovery scenarios remain. |

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
2. Locate evidence appropriate to the stage: decisions/design for planning, code/configuration for build, results for evaluation, and readiness/approval records for release. Record exact paths and applicable versions.
3. Distinguish design decisions from implementation, behavioral verification and release approval. Do not hold a planning item open for downstream implementation, or a Build item open solely for unrun evaluation. Record source review, execution checks and behavioral evaluation separately; an observed implementation defect does reopen Build. Check whether old evidence applies to the current configuration and criterion.
4. Set the assessment and link evidence. Record concrete gaps or necessary changes; reuse suitable work instead of rebuilding it.
5. For a task covering multiple components, record each finding. Use **Partial** if some required components meet the criterion and others remain incomplete; keep unreviewed components explicitly **Not assessed**.
6. Reconcile stage gates only after reviewing their required evidence. Keep original records available for comparison.

## 10. Repository assessment — October 25, 2026

This is the initial source-review snapshot. See [§11](#11-build-progress) for later changes; the task rows above reflect both.

**Basis:** reviewed source at local commit `e1729a8`, locked dependency declarations, installed harness source, skills, environment recipes and existing reports against spec v0.24. No new tests, model calls, sandbox allocations or provider-state checks were run. Private environment overrides were not inspected; coded defaults below are not assertions about an active process.

**Existing evidence:** the saved, ignored `.state/engineering-checks-latest.txt` is dated October 22, 2026 and records 58 passing tests with zero network attempts. The tracked [engineering report](engineering-checks.md) describes coverage and one earlier CSV/JSON smoke run. These are historical plumbing/limited task evidence, not a current Excel benchmark pass. No reports were found in `.state/evaluations/` during this review.

**How to interpret this review:** all six planning items meet their documentary criteria for the selected trial. The earlier v0.20 assessment incorrectly held PLAN-02/03/05 open for downstream implementation/verification; those gaps remain assigned to Build/Test/Release tasks. At that initial snapshot all ten composite Build items were Partial. The later increments complete BUILD-01–10; current evidence is recorded in §11. Deferred features are not marked missing merely because they are out of scope. A checked component below means source presence, not evaluated reliability.

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

## 11. Build progress

### Increment 1 — trial configuration, reference scope and provenance

Implemented in source on October 25, 2026; **not executed or tested**.

| Work | Code / documentation | Follow-up (Build / Test) |
|---|---|---|
| BUILD-01: fixed trial profile | [config.py](../src/accounting_finance_agent/config.py) defines `excel-benchmark-v1`; [agent.py](../src/accounting_finance_agent/agent.py) configures the API tier, SDK retry setting and default-subagent switch. | BUILD-01 is source-complete. Runtime/profile/delegation/provider checks: TEST-01/04/05. Image: BUILD-03; rates/accounting: BUILD-06. |
| BUILD-02: selected context | [knowledge.py](../src/accounting_finance_agent/knowledge.py) routes benchmark memory and only two procedural skills; [guidance](../references/excel-benchmark/memory/AGENTS.md) contains no company defaults; agent construction records computed framework compaction defaults. | BUILD-02 is source-complete. Exercise route isolation, retention and profile switching under TEST-01/03/04/06. |
| BUILD-08: configuration evidence | [provenance.py](../src/accounting_finance_agent/provenance.py) records settings, source/reference hashes and dependency versions; [runner](../src/accounting_finance_agent/__main__.py) stores the manifest and offers `--show-config`. | Build: implement usage/rate and sandbox package records. Test: verify saved manifests and identities under TEST-05. |
| BUILD-02: owner reference maintenance | [Operating guide](operating-guide.md#versioned-excel-trial-profile) documents correction/removal and fresh-thread handling. | Stale-context evaluation: TEST-01/03. Thread/trace/archive deletion implementation: BUILD-05. |

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
card records the counting contract. [Operating instructions](operating-guide.md#versioned-excel-trial-profile).

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
[attempt history and assessment](evaluations/management-review.md).

### Request ceiling revision

The owner requested a less restrictive request ceiling during the management-review
trial. Profile `excel-benchmark-v2` raises it from 20 to 40 provider requests.
Image-token preflights, inference retries and compaction share this counter. The
US$1 reservation policy, 600-second work deadline and 40-tool-attempt ceiling
remain unchanged. Existing v1 attempts retain their recorded configuration; the
revision applies to future runs and starts a new comparison baseline.

## Change log

| Version | Date | Change |
|---|---|---|
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
