# Finance & Accounting Agent — Agent Specification

| Field | Value |
|---|---|
| Version | v0.8 design draft · October 23, 2026 |
| Owner | Neil Yee |
| Purpose | Define the intended agent and the evidence required for its use. |
| Implementation assessment | Not assessed in this revision. Record repository findings later in the [task list](task-list.md). |

**Reading order:** purpose → capabilities → design → task applications → success criteria → evaluation, release, monitoring, and improvement.

This spec applies the [overview](mental-model/00-overview.md), [anatomy](mental-model/01-anatomy.md), and [ADLC](mental-model/02-adlc.md). The [architecture](architecture.md) shows the proposed components and flows. Technology names below are design choices to validate, not statements of completed work.

## 1. Purpose and scope

Build a reusable, human-supervised accounting and finance agent that gathers context, performs work, and produces results people can inspect and approve. Add task-specific skills and tools without redesigning the shared foundation.

The first stage should support terminal requests, persistent task conversations, sandboxed file/code work, and human review. Use synthetic or explicitly approved data. Introduce Asana after the foundation and first finance workflow meet their evaluation gates.

**Boundaries:** no journal posting, payments, changes to authoritative ERP records, or edits to original shared files. External communication is excluded from the first stage; a later Asana integration may publish only approved task statuses, summaries, and output links. Further access requires a separate scope and release decision.

Approval of an output does not authorize changes to reusable scripts, models, memory, skills, or permissions. Those require separate owner approval.

## 2. Shared capabilities

| ID | The agent should be able to… | Supporting functions |
|---|---|---|
| C1 | Understand the request using relevant inputs, instructions, skills, knowledge, and feedback; clarify material gaps. | Context, Core |
| C2 | Plan and execute work through tools, code, and optional delegation. | Core, Actions, Context |
| C3 | Create and check deliverables; explain results, assumptions, exceptions, and limitations. | Actions, Context, Controls |
| C4 | Preserve inputs, outputs, and task state so work can resume or be revised. | Continuity, Actions, Controls |
| C5 | Stay within approved access and operating limits; report failures and partial work accurately. | Controls, Core |
| C6 | Connect outputs to sources, checks, run records, and human decisions. | Continuity, Context, Controls |

Capabilities describe what the agent must do. Functions describe the responsibilities that support them. Mechanisms explain how those responsibilities work; implementation choices name the software or services to provide them. One capability may depend on several functions.

## 3. How the capabilities should work

Use Deep Agents / LangChain as the proposed orchestration framework, with an OpenAI model and a separate execution sandbox. Validate the framework's behavior and extension points against these requirements. Exact versions, model settings, limits, and hosted infrastructure are decisions in §7.

### 3.1 Core

**Role:** choose and coordinate the next step — C1, C2, C5.

| Concept | Mechanism | Intended behavior / design choice |
|---|---|---|
| Model | Model invocation | Configure model/version, reasoning, context/output limits, timeouts, and bounded retries. Record settings with each evaluated configuration. |
| Orchestration | Control loop, context assembly, output handling | Use the harness to route requests, answers, refusals, invalid/incomplete responses, and failures. Support waiting, revision, stopping, and recovery. |
| Completion | Outcome checks, state transitions | Distinguish execution completion, Needs review, approved output, Blocked, and failed/partial work. An empty response or exhausted budget must not imply success. |
| Limits and retries | Program checks around calls and actions | Apply shared budgets across the run and any delegated work. Retry only eligible failures after checking possible side effects; bound total attempts, time, and usage. |

### 3.2 Context

**Role:** supply relevant information for each decision — C1, C2, C3, C6.

| Concept | Mechanism | Intended behavior / design choice |
|---|---|---|
| Request and instructions | Context assembly | Include the task, boundaries, relevant input descriptions, and output expectations. Ask for material missing information instead of inventing it. |
| History and results | State selection, context assembly | Restore relevant conversation and tool results. Manage context limits without silently discarding requirements, decisions, or source identity. |
| Plan / todos | Tool, state | Provide a todo/planning tool such as `TodoListMiddleware`. Use it when useful; completion marks do not replace output checks. |
| Skills | Discovery/loading, tools, storage | Advertise approved procedures and load details as needed. `SkillsMiddleware` and read-only file routes are candidate mechanisms. Skills do not grant permissions. |
| Knowledge and memory | Retrieval, storage, access checks | Load approved business references and memory with source, scope, and version. Use clearly labeled fictional references for synthetic trials. |
| Revision context | Storage, retrieval | Include actionable feedback and the exact prior output version. Preserve earlier constraints unless explicitly changed. |

Stored information affects the model only when made available through its input or tool results. Provider-retained context is acceptable if its scope and lifecycle are understood.

### 3.3 Actions

**Role:** perform authorized operations — C2, C3, C4.

| Concept | Mechanism | Intended behavior / design choice |
|---|---|---|
| Files and calculations | File tools, execution environment | Read, list, create, and revise working copies. Support declared file types and validate calculations and cross-file consistency. |
| Code execution | Execution tool, sandbox | Run generated code in an isolated environment. Proposed provider: LangSmith sandbox. Keep orchestration and model credentials on the host. |
| Reference access | Routed storage, file tools | Expose approved skills/memory read-only. Copy required execution assets deliberately; a virtual reference route is not necessarily mounted in the sandbox. |
| Delegation | Another agent execution | Optional. Give each subtask explicit context, tools, scope, and shared budgets; do not assume separate context means security isolation. |
| Connectors / MCP | Host-side adapters, scoped identities | Add only for an approved task need. Prefer read-only business access initially. Define permissions, returned data, failures, and side effects for each exposed operation. |

Use copy-in/copy-out for sandbox files. Preserve eligible outputs and supporting work before cleanup; define excluded files, size limits, conflict handling, and transfer failure behavior. Cloud sync and live co-editing require their own design and evaluation.

### 3.4 Controls

**Role:** govern inputs, actions, state changes, and delivery — C3–C6.

| Control | Mechanism | Required behavior |
|---|---|---|
| Task boundaries | Instructions plus program/environment checks | Treat source documents as data. Enforce permissions outside the model, including against instructions embedded in inputs. |
| References and source files | Access rules, working copies | Reject agent edits to approved shared references and original inputs. Preserve prior output versions and concurrent edits; remote deletion must not silently erase retained local work. |
| Operating budgets | Runtime checks | Bound model/tool calls, output size, elapsed time, retries, and delegated work. Define the cost policy and measurement limits explicitly. |
| Execution isolation | Environment and identity policy | Restrict filesystem, process, network, and resource access. Keep host secrets out of generated-code environments unless separately authorized. Verify effective restrictions. |
| Output approval | Human decision, versioned record | Approve/reject an identified output manifest. File changes invalidate the earlier approval for the changed version. Initial review occurs between runs. |
| Reusable asset promotion | Separate owner decision | Require approval and relevant evaluations before changing shared scripts, models, skills, memory policy, or access. |
| External effects | Authorization, operation records | Deny actions outside scope. For allowed writes, record intent/result and prevent duplicates across retries or concurrent workers. |

Assess each control at its actual boundary. Instructions, program checks, human review, and environment restrictions provide different protections; none is sufficient merely because of its label.

### 3.5 Continuity

**Role:** retain and recover what later steps need — C4, C6.

| Concept | Mechanism | Required behavior / design choice |
|---|---|---|
| Run and thread state | Checkpoints, thread identity | Persist required messages, results, plans, and execution state. Define run/thread semantics and prevent overlapping ownership of the same task. SQLite is an option for local trials. |
| Working files | Durable workspace, versioned transfer | Keep per-task/thread files beyond sandbox lifetime. Associate outputs and conflicts with their run and source versions. |
| Recovery | Checkpoints, action records, reconciliation | After interruption, determine what completed before retrying. Preserve recoverable work; identify missing or uncertain results. Checkpoints cannot undo external effects. |
| Approved memory | Scoped storage, owner updates | Begin with owner-maintained reusable guidance. Define ownership, source/version, retention, correction, and deletion. Automatic memory writes require a later policy and evaluation decision. |
| Provenance and review | Structured records, tracing | Record outcomes, input/output fingerprints, relevant actions, checks, usage, and approvals. Use LangSmith tracing for evaluations and pilots under an approved data policy. |
| Configuration identity | Versioned manifest | Identify code/dependencies, model/settings, instructions, skills/tools, access, environment, and storage schema. Link relevant input and memory versions separately. |

## 4. Applying the capabilities

### 4.1 Initial evaluation tasks

These are proposed applications of C1–C6, not limits on the reusable foundation.

| Task | Objective | Evaluation |
|---|---|---|
| CSV summary | Produce a correct summary from supplied data; clarify missing or ambiguous inputs. | E-PLAT-1 |
| Office-file package | Produce an Excel working paper, a Word analysis, and its PDF export from synthetic data. Check formulas, calculations, presentation, and agreement between files. | E-ART-1 |
| Monthly bank reconciliation | Match bank and ledger items, explain exceptions and balance bridges, and produce reviewable supporting work. Confirm this as the first finance workflow during planning. | E-FIN-1 |

For each task, define its inputs, procedure, supported formats, access, expected outputs, independent answers/rubric, and acceptance thresholds. Keep detailed procedures in linked skill/workflow documents. Add later tasks using the same structure.

### 4.2 Work lifecycle and interface

**Assign → gather context → execute → preserve → review → approve or revise.** Failures and missing inputs lead to an explicit failed/partial or Blocked outcome.

| Step | Intended behavior |
|---|---|
| Intake | Start with a terminal interface. Select or create a persistent thread. Later, an Asana dispatcher gathers eligible task fields, comments, attachments, changes, and feedback. |
| Execute | Restore context; prepare input copies and a sandbox when needed; run within permissions and budgets. |
| Preserve / return | Check outputs, preserve files/evidence, then clean up. Return summary, locations, limitations, and run outcome even when work is partial. |
| Review | Keep deliverables in Needs review until a reviewer approves that version or requests changes. |
| Revise | Continue the same task/thread with feedback and prior output versions. |

Proposed Asana task statuses: **To do → Agent working → Needs review → Done**, or **Blocked**. Technical run outcomes remain separate. Informational comments and agent-generated updates must not trigger revisions or duplicate runs. Define eligibility, locking, feedback rules, and approval semantics before integration.

### 4.3 Output standard

Provide the requested artifact, concise summary, unresolved issues, and useful supporting code/provenance. Financial work must identify period, currency/units, sources, assumptions, calculations, tie-outs, exceptions, checks performed, and limitations.

Distinguish file integrity, formula correctness, recalculation, and visual review. State what was actually checked. An unavailable check must be visible and must block acceptance where that check is required.

## 5. Success criteria

| ID | Capabilities / scope | Success means… | Evaluation |
|---|---|---|---|
| SC-1 | C1–C3; each task | Outputs meet independent expected results and presentation rubrics; material gaps are clarified or reported. | E-PLAT-1, E-ART-1, E-FIN-1 |
| SC-2 | C4 | Sources stay unchanged; required state/files survive cleanup and restart, with versions and conflicts traceable. | E-FILE-1 |
| SC-3 | C5, C6 | Permissions and limits hold; approvals apply only to their defined scope and version. | E-CTRL-1, E-PROV-1 |
| SC-4 | C3, C6 | Reviewers can follow sources, assumptions, actions, checks, configuration, and approvals to the delivered version. | E-PROV-1 |
| SC-5 | All; release | The proposed scope meets evaluation, ownership, access, data, recovery, and monitoring requirements before use. | E-REL-1 |
| SC-6 | C1, C2, C4–C6; Asana | Intake, review, revision, and restart preserve work without duplicate dispatch or trigger loops. | E-ASANA-1 |
| SC-7 | C2, C4, C5 | Interrupted or incomplete runs report accurate outcomes, preserve recoverable work, and retry without repeating completed external effects. | E-REC-1 |

Traceability example: **C4 → Continuity + Actions + Controls → checkpoint/transfer mechanisms → SC-2 → E-FILE-1 → missing-file/resume monitoring.**

## 6. Evaluation, release, and improvement

Follow **Build (Plan, Configure) → Test → Deploy → Monitor → back to Build**. Design the checks and operating plans before relying on the agent. All evaluations and gates below are requirements; their results are unassessed.

### 6.1 Evaluation plan

Each individual check must specify the four dimensions, cases, grader/rubric, threshold, repetitions/sample size, setup/reset, and configuration. These groups define coverage; they are not completed test results.

| Evaluation | What is checked | Who grades | When / setting | Why |
|---|---|---|---|---|
| E-PLAT-1 | Output, required trajectory, steps | Code + human rubric for clarification | Offline | Capability; retain as regression |
| E-ART-1 | Artifacts, calculations, cross-file agreement | Code + human presentation review | Offline; applicable checks online | Capability and regression |
| E-FILE-1 | Files, transfer, resume | Code | Offline; preservation checks online | Capability and regression |
| E-FIN-1 | Financial results and required procedure | Code + finance reviewer | Offline; tie-outs/review online | Capability; retain as regression |
| E-CTRL-1 | Permission boundaries and budgets | Code + access reviewer | Offline; boundary signals online | Capability and regression |
| E-PROV-1 | Evidence and review records | Code + human reviewer | Offline and online | Capability and regression |
| E-REC-1 | Failure, partial progress, retry/resume | Code + operator review | Offline; failure signals online | Capability and regression |
| E-REL-1 | Release step and readiness record | Owner | Offline, before release or scope expansion | Capability and regression |
| E-ASANA-1 | Full assignment-to-review path | Code + human reviewer | Offline; lifecycle signals online | Capability; retain as regression |

Use deterministic checks for exact answers/invariants and rubrics for judgment. Calibrate any LLM judge against human ratings. Offline checks can run after release too; consistency means acceptable outcomes, not identical wording or tool sequences.

| Evaluation | Required cases / mechanisms | Acceptance condition |
|---|---|---|
| E-PLAT-1 | Model loop, context selection, skills, tools: representative CSV tasks, missing/conflicting inputs, repeat trials. | Expected results match within declared tolerances; unsupported assumptions are surfaced; budgets hold. |
| E-ART-1 | File generation, recalculation, validation: valid and deliberately defective Excel/Word/PDF packages. | Critical formulas/figures and cross-file values agree; required recalculation and presentation checks pass; graders detect seeded defects. |
| E-FILE-1 | Checkpoints, transfer, versions: text/XLSX/binary files, concurrent edits, exclusions, cleanup/restart and transfer failure. | Sources preserved; required files/state recoverable; conflicts retained; incomplete preservation reported. |
| E-FIN-1 | Skill and calculations: bank/ledger matches, duplicates, exceptions, balance bridges, proposed entries and artifacts. | Independent expected results and all critical finance checks pass; reviewer accepts representative work. Proposed entries remain drafts. |
| E-CTRL-1 | Policy/runtime/environment checks: authorized/denied requests, injected instructions, secrets, filesystem/network, budgets and delegation. | Forbidden effects are blocked; configured limits enforced; effective access matches the approved policy. |
| E-PROV-1 | Manifest, work log, trace, review: follow input to output; modify an approved artifact; test separate approval scopes. | Evidence identifies the run/configuration/source/output versions; changed artifacts cannot inherit stale approval. |
| E-REC-1 | Error handling and operation records: startup failure, timeout after a possible effect, incomplete response, exhausted budget, transfer/cleanup failure, restart. | Accurate partial/failure status; bounded retries; no repeated completed effects; recovery or escalation follows the documented procedure. |
| E-REL-1 | Release record, identities, monitoring, recovery rehearsal and representative memory/state compatibility. | All mandatory readiness conditions pass for the proposed stage; limitations and accountable owner recorded. |
| E-ASANA-1 | Dispatcher, task/thread mapping, approvals: normal work, actionable/informational feedback, duplicate/out-of-order events, concurrent workers, failure/restart. | Eligible work follows the defined path; duplicates/loops prevented; context, files, and approval identity retained. |

Define sample sizes, tolerances, budgets, and thresholds in D3 before judging a release candidate. Critical boundary or financial errors cannot be averaged away. Retain case/grader versions, results, variation, and limitations; include task, component, and integration evidence. Coverage alone does not establish reliability.

### 6.2 Release plan

| Stage | Authorized use | Evidence to enter / expand |
|---|---|---|
| 0. Controlled trial | Synthetic or explicitly approved cases with restricted access. | Trial scope, identities, limits, and data handling agreed. |
| 1. Parallel operation | Approved real tasks alongside the normal process; outputs non-authoritative and consequential writes suppressed. | Required offline evaluations and readiness review pass. |
| 2. Supervised use | Every deliverable reviewed before business use; no posting/payments. | Reviewed representative trials meet agreed quality, cost/time, and recovery criteria. |
| 3. Broader use, if justified | Specifically approved workload/access expansion. | Evidence for added scope, relevant regressions, monitoring and recovery readiness. |

Supervised use may remain the endpoint. Asana requires its own gate after foundation and finance evaluation. Introducing another connector or automatic memory writes requires a separate scope decision.

The release record must name the configuration and input/memory compatibility, scope/stage, operational owner, identities, data/trace retention, budgets, deployment/storage choices, monitoring thresholds, and accepted limitations.

Rehearse **stop** (new and active work), **recover** (reconcile completed/partial effects before retry), **rollback** (compatible configuration/state), and **repair** (re-review outputs and correct external effects). Do not assume reverting code reverses actions or stored data.

### 6.3 Monitoring plan

| Function / criteria | Signals and evidence to collect | Response to define |
|---|---|---|
| Core — SC-1, SC-3, SC-7 | Outcome/error rates, incomplete responses, time, calls, tokens/cost, retries. | Investigate model/orchestration/dependencies; enforce budgets. |
| Context — SC-1, SC-4 | Wrong sources/skills, unsupported assumptions, missed feedback or material inputs. | Review retrieval, instructions, and context selection. |
| Actions — SC-1, SC-2 | Tool failures, artifact defects, cross-file discrepancies, transfer conflicts, human corrections. | Contain faulty outputs; inspect inputs, code, validation. |
| Controls — SC-3, SC-5 | Limit hits, denied requests, unauthorized effects, stale approvals. | Stop/contain breaches; review access and enforcement. |
| Continuity — SC-2, SC-6, SC-7 | Failed resumes, stale/missing files, duplicate effects, memory incompatibility. | Preserve evidence; reconcile state before recovery. |
| User outcome — SC-1, SC-5, SC-6 | Acceptance/rejection, revisions, unresolved work, reviewer effort by task/configuration. | Compare with intended value; adjust scope or design. |

Retain appropriate per-run records and perform applicable automatic checks before delivery. Review every output during supervised use; set sample/trend review cadence, thresholds, and responsible owner in D4. Minimize sensitive trace content and define access/retention. A signal is a starting point for diagnosis, not proof of a particular cause.

### 6.4 Respond and improve

Stop and investigate material incorrect results, boundary breaches, or data loss. Diagnose repeatable defects, add useful regression cases, and verify changes before release. Record accepted limitations with an owner and rationale.

Scale the work to impact: new skills need capability cases and relevant regressions; new tools/access need boundary and retry checks; model/orchestration changes need broad representative coverage. Revisit all plans when purpose or authority changes.

Owner-maintained guidance is the initial memory policy. Later automatic updates must define scope, validation, correction/expiry/deletion, and compatibility with software changes. Evaluate empty, existing, stale, and conflicting memory; plan migration/invalidation and rollback before policy/schema changes.

## 7. Decisions to resolve

These are design decisions, not findings about repository implementation. Owner: Neil Yee, with specialist review where required.

| ID | Decision | Resolve before |
|---|---|---|
| D1 | Exact model/framework versions, settings, dependencies, execution provider/image, and runtime budget enforcement. | Configuration baseline |
| D2 | Supported file formats, required recalculation/rendering checks, first finance workflow and independent reference answers. | Task evaluation design |
| D3 | Cases, graders, tolerances, repetitions/sample sizes, critical failures, cost/time/call/retry/revision thresholds. | Evaluation and release decisions |
| D4 | Operational owner, signal sources, alert/review cadence, thresholds, trace data/access/retention. | Real-work pilot |
| D5 | Host/storage, identity/access policy, concurrency model, backups, transfer limits, stop/recovery/rollback and state compatibility. | Deployment readiness |
| D6 | Asana eligibility, trigger/status mapping, actionable feedback, publication/approval scope, deduplication and locking. | Asana configuration |
| D7 | Memory ownership/scope, approved references, retention/correction/deletion, and any later automatic-write policy. | Memory use or policy expansion |

## 8. Change log

| Version | Date | Change |
|---|---|---|
| v0.8 | 2026-10-23 | Recast as intended requirements/design; removed implementation and pass/fail claims. Added explicit artifact and recovery evaluations, decision IDs, and revised lifecycle guidance. |
| v0.7 | 2026-10-23 | Connected capabilities, design, success criteria, evaluations, and monitoring. |
| v0.6 and earlier | 2026-10-22 | Earlier document structures retained in Git history. |
