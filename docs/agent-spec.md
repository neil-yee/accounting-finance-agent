# Finance & Accounting Agent — Agent Specification

| Field | Value |
|---|---|
| Version | v0.14 design draft · October 24, 2026 |
| Owner | Neil Yee |
| Purpose | Define the intended agent and the evidence required for its use. |
| Implementation assessment | Not assessed in this revision. Record repository findings later in the [task list](task-list.md). |

**Reading order:** why we need the agent → what it must do and how → how an assignment proceeds → what counts as success → how we evaluate, release, monitor and improve it.

This spec applies the [overview](mental-model/00-overview.md), [anatomy](mental-model/01-anatomy.md), and [ADLC](mental-model/02-adlc.md). Use the [architecture](architecture.md) for technical detail and the [task list](task-list.md) for implementation work and assessment evidence. All technology choices are proposals to validate.

## 1. Purpose and scope

Build a reusable, human-supervised accounting and finance agent that gathers context, performs work, and produces results people can inspect and approve. Add task-specific skills and tools without redesigning the shared foundation.

**First stage**

- Accept terminal requests.
- Maintain persistent task conversations.
- Perform sandboxed file/code work.
- Support human review.
- Use synthetic or explicitly approved data.

Introduce Asana after the foundation and first finance workflow meet their evaluation gates.

**Boundaries**

- No journal posting or payments.
- No changes to authoritative ERP records or original shared files.
- No external communication in the first stage.
- Later Asana publication is limited to approved task statuses, summaries and output links.
- Further access requires a separate scope and release decision.

Approval of an output does not authorize changes to reusable scripts, models, memory, skills, or permissions. Those require separate owner approval.

## 2. Capabilities and design

The purpose in §1 requires the abilities below. Read each row from **required behavior → functions → mechanisms → proposed implementation**. The capability ID follows that requirement through the rest of the spec.

- **Capability:** an ability the agent should provide, expressed through required behavior.
- **Functions:** the responsibilities that support that ability: Core, Context, Actions, Controls, and Continuity.
- **Mechanisms:** the processes that make those responsibilities work, such as context assembly, tool execution, or checkpoints.
- **Proposed implementation:** the framework, library, service, or component that would provide those mechanisms.

**Reuse scope**

- **Shared foundation:** supports many kinds of agents.
- **Reusable work:** handles a general kind of work.
- **Task-specific:** delivers a defined business outcome.

Scope describes reuse. Implementation status, deployment stage and permissions are assessed separately. All capabilities remain unassessed.

| ID | Scope | Capability | Required behavior | Functions | Mechanisms | Proposed implementation |
|---|---|---|---|---|---|---|
| C1 | Shared foundation | Understand work | • Use relevant inputs, approved references, history and feedback; clarify material gaps.<br>• Preserve constraints and source identity when shortening context; use the exact prior version for revisions. | Context, Core | Context assembly, retrieval, clarification | Deep Agents / LangChain context handling; approved skill/reference loading. Technical detail: [context assembly](architecture.md#41-context-assembly--c1-c2). |
| C2 | Shared foundation | Plan and execute | • Plan and coordinate tools, sandboxed code and optional delegation.<br>• Handle answers, tool requests, refusals and incomplete responses explicitly.<br>• Distinguish execution completion from approval; todo completion alone is insufficient.<br>• Follow C4–C5 for recovery and limits. | Core, Actions, Context | Model invocation, control loop, planning, tool routing | Deep Agents / LangChain, OpenAI model, optional todo middleware and LangSmith sandbox tools. Technical detail: [execution](architecture.md#42-runtime-and-tool-contracts--c2-c5). |
| C3 | Shared foundation | Deliver reviewable results | • Check outputs; explain results, assumptions, exceptions and limitations.<br>• Report unavailable checks.<br>• Obtain human approval for an identified output version before business use; changed files require renewed approval.<br>• Use C6 evidence. | Actions, Context, Controls | Artifact checks, result synthesis, human review | Validation tools, delivery summary and version-specific review records. See the [delivery standard](#32-delivery-standard). |
| C4 | Shared foundation | Preserve and resume work | • Preserve required state and files before sandbox cleanup.<br>• Resume with prior versions and feedback; report preservation failures and uncertain results.<br>• Reconcile completed effects before retrying.<br>• Keep reusable memory owner-maintained with defined scope, retention, correction and deletion. | Continuity, Actions, Controls | Checkpoints, durable storage, versioned transfer, recovery, scoped memory retention | Thread checkpoints (SQLite for local trials), durable C7 files, operation records and scoped memory storage. Technical detail: [persistence and recovery](architecture.md#43-state-files-and-recovery--c4-c7). |
| C5 | Shared foundation | Respect limits and report failures | • Enforce permissions and shared call, output, time and retry budgets outside the model.<br>• Treat source documents as data; protect secrets.<br>• Report blocked, incomplete and failed/partial work accurately.<br>• Prevent duplicate external effects.<br>• Require separate approval for reusable-asset or access changes. | Controls, Core | Authorization, budget enforcement, outcome checks, bounded retries | Host runtime checks, scoped identities, sandbox restrictions and approval records. Technical detail: [runtime](architecture.md#42-runtime-and-tool-contracts--c2-c5) and [access](architecture.md#44-access-and-approval-enforcement--c3-c5-c7). |
| C6 | Shared foundation | Provide evidence for review | • Link sources, configuration, actions, checks, usage and human decisions to the task/run and delivered version.<br>• Record what was actually verified; apply approved trace access and retention policies. | Continuity, Context, Controls | Provenance capture, tracing, versioned manifests and review records | LangSmith tracing, versioned manifests and review records. Technical detail: [evidence](architecture.md#45-evidence-and-configuration--c6). |
| C7 | Shared foundation | Manage a task workspace | • Organize and locate task inputs, working files and outputs.<br>• Isolate tasks; protect original inputs and approved references.<br>• Retain run identity, output versions and concurrent edits; prevent conflicting task ownership.<br>• Use C4 for persistence and recovery. | Actions, Controls, Continuity | Scoped file operations, task identity, working copies | Per-task durable folders, scoped file tools, task locks and sandbox copy-in/copy-out. Technical detail: [file transfer](architecture.md#43-state-files-and-recovery--c4-c7). |
| C8 | Reusable work | Work with tabular data | Read, validate, transform and summarize CSV/tabular inputs while preserving source meaning and declared types. | Context, Actions, Controls | Parsing, schema/type validation, calculation, independent checks | Sandbox parsing/calculation libraries; declare encoding, types and missing-value handling. Uses C1–C7. |
| C9 | Reusable work | Work with Excel files | • Read, create and revise workbooks.<br>• Preserve supported features.<br>• Check formulas, calculations and presentation. | Context, Actions, Controls | Workbook operations, recalculation, inspection | openpyxl or a suitable workbook library; separately selected recalculation and rendering tools (D2). Uses C1–C7. |
| C10 | Reusable work | Work with Word documents | Read relevant content and create/revise structured documents with consistent headings, tables and formatting. | Context, Actions, Controls | Document parsing, generation and inspection | python-docx or a suitable document library, with checks for supported content and formatting (D2). Uses C1–C7. |
| C11 | Reusable work | Produce PDF deliverables | • Export document content.<br>• Check content fidelity, pagination and readability. | Actions, Controls | Document conversion, content comparison, visual inspection | Compatible conversion engine and PDF inspection tools (D2). Uses C1–C7 and the source-document capability where needed. |
| C12 | Task-specific | Reconcile bank transactions | • Match bank and ledger items, explain exceptions/balance bridges, and produce supporting work.<br>• Provisional first finance workflow (D2). | Core, Context, Actions, Controls, Continuity | Skill loading, reconciliation procedure, calculations and review | Approved reconciliation skill using C1–C7 and required C8–C11 tools; independent reference answers and finance review. [Starter evaluation task](#51-starter-evaluation-tasks). |

**How the rows connect**

C8–C12 use C1–C7 as their foundation. For example, Excel work (C9) uses:

- **C7** to protect source files.
- **C4** to preserve progress.
- **C5** to enforce limits.
- **C3 and C6** to deliver reviewed, traceable results.

Those requirements belong to the referenced capabilities and apply whenever they are used.

Several capabilities may share functions, mechanisms or components. Exact implementation choices and limits are decisions in §6.

**Distinctions to keep in mind**

- **Workspace and persistence:** C7 provides the working area and file operations; C4 keeps work available across runs.
- **Excel validation:** formula writing, calculated values and visual layout need separate checks.
- **Financial validation:** valid files still need checks for financial correctness.

**Reusing the spec**

1. Carry forward the selected foundation and work capabilities, criteria and evaluation definitions.
2. Adapt task capabilities, boundaries, access and implementation choices.
3. Evaluate the new configuration. A prior passing result does not transfer automatically.

## 3. How the agent handles an assignment

Section 2 defines the abilities. This section shows when they are used during an assignment and what the person receives.

### 3.1 Assignment lifecycle

**Assign → gather context → execute → check and preserve → review → approve or revise.**

| Step | Required behavior | Capabilities used |
|---|---|---|
| Assign | Receive the request; select or create its thread and workspace. | C1, C4, C7 |
| Gather context | Restore relevant history, inputs, references and feedback; clarify material gaps. | C1, C4 |
| Execute | Plan the work, prepare input copies and a sandbox when needed, and use the selected tools within approved limits. | C2, C5, C7 + relevant C8–C12 |
| Check and preserve | Validate outputs, save files and evidence before cleanup, then return results and limitations. | C3, C4, C6, C7 |
| Review and approve | Hold deliverables in Needs review until a reviewer approves that version or requests changes. Record the decision. | C3, C5, C6 |
| Revise | Continue the same task/thread using feedback and the identified prior version; return to context gathering. | C1–C4, C6, C7 |
| Block or recover | At any step, report missing inputs or failed/partial work, preserve recoverable progress, and reconcile possible effects before retrying. | C4–C7 |

C5 permissions and budgets, and C6 evidence collection, apply throughout. Steps may repeat as the task develops.

**Work interface:** start with terminal requests. A later Asana dispatcher may gather eligible task fields, comments, attachments, changes and feedback through the same assignment lifecycle.

Proposed Asana task statuses: **To do → Agent working → Needs review → Done**, or **Blocked**.

Before integration, define:

- Which tasks are eligible and how execution is locked.
- Which feedback triggers a revision.
- How approval is recorded and interpreted.
- How informational comments and agent-generated updates are prevented from triggering revisions or duplicate runs.

Technical run outcomes remain separate from task statuses.

### 3.2 Delivery standard

This expands **C3** (reviewable results) and **C6** (evidence) into what accompanies each delivery.

**Every delivery includes:**

- The requested artifact.
- A concise summary and unresolved issues.
- Useful supporting code and provenance.

**Financial work also identifies:**

- Period, currency and units.
- Sources and assumptions.
- Calculations and tie-outs.
- Exceptions, checks performed and limitations.

**Report these checks separately:**

- File integrity.
- Formula correctness.
- Recalculation.
- Visual review.

State what was actually checked. An unavailable check must be visible and must block acceptance where that check is required.

## 4. Success criteria

Each criterion defines how to judge the capabilities and assignment behavior above. Its evaluation ID points to the checks in §5.2; monitoring in §5.4 tracks the same criterion during use.

| ID | Capabilities / scope | Success means… | Evaluation |
|---|---|---|---|
| SC-1 | C1–C3, C8–C12; each declared work/task capability | Outputs meet independent expected results and presentation rubrics; material gaps are clarified or reported. | E-PLAT-1, E-ART-1, E-FIN-1 |
| SC-2 | C4, C7 | Task files are organized and isolated; sources stay unchanged; required state/files survive cleanup and restart, with versions and conflicts traceable. | E-FILE-1 |
| SC-3 | C3, C5–C7; all capability scopes | Permissions and limits hold; approvals apply only to their defined scope and version. | E-CTRL-1, E-PROV-1 |
| SC-4 | C3, C6 | Reviewers can follow sources, assumptions, actions, checks, configuration, and approvals to the delivered version. | E-PROV-1 |
| SC-5 | All; release | The proposed scope meets evaluation, ownership, access, data, recovery, and monitoring requirements before use. | E-REL-1 |
| SC-6 | C1, C2, C4–C7; Asana | Intake, review, revision, and restart preserve work without duplicate dispatch or trigger loops. | E-ASANA-1 |
| SC-7 | C2, C4, C5, C7 | Interrupted or incomplete runs report accurate outcomes, preserve recoverable work, and retry without repeating completed external effects. | E-REC-1 |

**Example:** C4/C7 require files to survive cleanup → SC-2 defines successful preservation → E-FILE-1 checks cleanup and restart → SC-2 monitoring detects missing files → a finding triggers recovery and an updated regression case.

## 5. Evaluation, release, and improvement

Follow **Build (Plan, Configure) → Test → Deploy → Monitor → back to Build**. Design the checks and operating plans before relying on the agent. All evaluations and gates below are requirements; their results are unassessed.

Use the criteria in §4 to design evaluations, decide whether a release is ready, and respond to findings during use.

### 5.1 Starter evaluation tasks

These are the first assignments used to exercise the capabilities. They cover reusable file work and the proposed finance workflow; additional cases are needed for the full declared scope.

| Evaluation task | Capability composition | Objective | Evaluation |
|---|---|---|---|
| CSV summary | C1–C7 foundation + C8 tabular data | Produce a correct summary; clarify missing or ambiguous inputs. | E-PLAT-1 |
| Office-file package | C1–C7 foundation + C9 Excel + C10 Word + C11 PDF | Produce a working paper, analysis and PDF export from synthetic data; check calculations, presentation and cross-file agreement. | E-ART-1 |
| Monthly bank reconciliation | C1–C7 foundation + required C8–C11 work capabilities → C12 reconciliation | Match bank/ledger items and explain exceptions/balance bridges with reviewable supporting work. | E-FIN-1 |

For each task, define:

- Inputs and supported formats.
- Procedure and permitted access.
- Expected outputs.
- Independent reference answers or a grading rubric.
- Acceptance thresholds.

Keep detailed procedures in linked skill/workflow documents. Add later tasks using the same structure.

### 5.2 Evaluation plan

For each individual check, specify:

- **Four dimensions:** what is checked, who grades, when/setting, and why.
- **Cases and grading:** inputs, reference answers or rubric, and acceptance threshold.
- **Trial design:** repetitions or sample size, setup and reset procedure.
- **Configuration:** the version being evaluated.

The first table classifies each evaluation along the four dimensions and links it to its success criteria. The second defines cases and acceptance conditions. Results remain unassessed.

| Evaluation / criteria | What is checked | Who grades | When / setting | Why |
|---|---|---|---|---|
| E-PLAT-1<br>SC-1 | Output, required trajectory, steps | Code + human rubric for clarification | Offline | Capability; retain as regression |
| E-ART-1<br>SC-1 | Artifacts, calculations, cross-file agreement | Code + human presentation review | Offline; applicable checks online | Capability and regression |
| E-FILE-1<br>SC-2 | Files, transfer, resume | Code | Offline; preservation checks online | Capability and regression |
| E-FIN-1<br>SC-1 | Financial results and required procedure | Code + finance reviewer | Offline; tie-outs/review online | Capability; retain as regression |
| E-CTRL-1<br>SC-3 | Permission boundaries and budgets | Code + access reviewer | Offline; boundary signals online | Capability and regression |
| E-PROV-1<br>SC-3, SC-4 | Evidence and review records | Code + human reviewer | Offline and online | Capability and regression |
| E-REC-1<br>SC-7 | Failure, partial progress, retry/resume | Code + operator review | Offline; failure signals online | Capability and regression |
| E-REL-1<br>SC-5 | Release step and readiness record | Owner | Offline, before release or scope expansion | Capability and regression |
| E-ASANA-1<br>SC-6 | Full assignment-to-review path | Code + human reviewer | Offline; lifecycle signals online | Capability; retain as regression |

**Grading guidance**

- Use deterministic checks for exact answers and invariants.
- Use rubrics for judgment; calibrate any LLM judge against human ratings.
- Run offline checks after release when useful.
- Judge consistency by acceptable outcomes; wording and tool sequences may vary.

| Evaluation | Required cases / mechanisms | Acceptance condition |
|---|---|---|
| E-PLAT-1 | Model loop, context selection, skills, tools: representative CSV tasks, missing/conflicting inputs, repeat trials. | Expected results match within declared tolerances; unsupported assumptions are surfaced; budgets hold. |
| E-ART-1 | C9–C11 file tools, recalculation, conversion and inspection: reading/revision cases, valid and deliberately defective Excel/Word/PDF packages, and declared supported/unsupported features. | Required content/features are preserved on read/revision/export; critical formulas/figures and cross-file values agree; required recalculation/presentation checks pass; unsupported features are reported; graders detect seeded defects. |
| E-FILE-1 | Checkpoints, transfer, versions: text/XLSX/binary files, task isolation/file lookup, concurrent edits, exclusions, cleanup/restart and transfer failure. | Required files are locatable and scoped to the right task/run; sources preserved; state/files recoverable; conflicts retained; incomplete preservation reported. |
| E-FIN-1 | Skill and calculations: bank/ledger matches, duplicates, exceptions, balance bridges, proposed entries and artifacts. | Independent expected results and all critical finance checks pass; reviewer accepts representative work. Proposed entries remain drafts. |
| E-CTRL-1 | Policy/runtime/environment checks: authorized/denied requests, injected instructions, secrets, filesystem/network, budgets and delegation. | Forbidden effects are blocked; configured limits enforced; effective access matches the approved policy. |
| E-PROV-1 | Manifest, work log, trace, review: follow input to output; modify an approved artifact; test separate approval scopes. | Evidence identifies the run/configuration/source/output versions; changed artifacts cannot inherit stale approval. |
| E-REC-1 | Error handling and operation records: startup failure, timeout after a possible effect, incomplete response, exhausted budget, transfer/cleanup failure, restart. | Accurate partial/failure status; bounded retries; no repeated completed effects; recovery or escalation follows the documented procedure. |
| E-REL-1 | Release record, identities, monitoring, recovery rehearsal and representative memory/state compatibility. | All mandatory readiness conditions pass for the proposed stage; limitations and accountable owner recorded. |
| E-ASANA-1 | Dispatcher, task/thread mapping, approvals: normal work, actionable/informational feedback, duplicate/out-of-order events, concurrent workers, failure/restart. | Eligible work follows the defined path; duplicates/loops prevented; context, files, and approval identity retained. |

**Before accepting evaluation results**

- Define sample sizes, tolerances, budgets and thresholds in D3 before judging a release candidate.
- Treat critical boundary or financial errors as failures; do not average them away.
- Retain case/grader versions, results, variation and limitations.
- Include task, component and integration evidence.
- Assess C8–C11 separately and in composed tasks. Passing one workflow does not establish general file-format support.

Coverage alone does not establish reliability.

### 5.3 Release plan

Use the evaluation evidence to decide which scope of use is ready. **SC-5 / E-REL-1** governs the release decision, including required capability results and operational readiness.

| Stage | Authorized use | Evidence to enter / expand |
|---|---|---|
| 0. Controlled trial | Synthetic or explicitly approved cases with restricted access. | Trial scope, identities, limits, and data handling agreed. |
| 1. Parallel operation | Approved real tasks alongside the normal process; outputs non-authoritative and consequential writes suppressed. | Required offline evaluations and readiness review pass. |
| 2. Supervised use | Every deliverable reviewed before business use; no posting/payments. | Reviewed representative trials meet agreed quality, cost/time, and recovery criteria. |
| 3. Broader use, if justified | Specifically approved workload/access expansion. | Evidence for added scope, relevant regressions, monitoring and recovery readiness. |

**Scope expansion**

- Supervised use may remain the endpoint.
- Asana requires its own gate after foundation and finance evaluation.
- Another connector or automatic memory writes require a separate scope decision.

**Release record**

- Configuration and input/memory compatibility.
- Scope, stage and operational owner.
- Identities and data/trace retention.
- Budgets and deployment/storage choices.
- Monitoring thresholds and accepted limitations.

**Recovery rehearsals**

| Action | What to rehearse |
|---|---|
| Stop | Stop new and active work. |
| Recover | Reconcile completed or partial effects before retrying. |
| Rollback | Restore a compatible configuration and state. |
| Repair | Re-review outputs and correct external effects. |

Reverting code does not necessarily reverse actions or stored data.

### 5.4 Monitoring plan

Monitor the same success criteria used for evaluation, using run records, artifact checks and human review.

| Criterion / capabilities | Signals and evidence | Response to define |
|---|---|---|
| SC-1 — C1–C3, C8–C12: work quality | Wrong sources/skills, missed inputs or feedback, unsupported assumptions, artifact defects, financial discrepancies, acceptance/rejection, revisions, unresolved work and reviewer effort. | Inspect context, procedure, tools and validation; contain faulty outputs and add useful regression cases. |
| SC-2 — C4, C7: preserved work | Missing files, source changes, transfer conflicts, failed resumes and lost versions. | Preserve evidence; reconcile state and repair transfer or storage behavior. |
| SC-3 — C3, C5–C7: limits and approval | Denied requests, unauthorized effects, stale approvals, limit hits, calls, elapsed time and tokens/cost. | Stop or contain breaches; review enforcement, access, budgets and approval records. |
| SC-4 — C3, C6: review evidence | Missing source/configuration/output identities, unrecorded checks or decisions, difficulty tracing a result. | Repair evidence collection; identify affected deliverables and re-review them. |
| SC-5 — all: release readiness | Configuration/access drift, missing monitoring coverage, incompatible state/memory, workload beyond approved scope. | Reassess readiness; restrict or pause affected use until its release conditions hold. |
| SC-6 — C1, C2, C4–C7: task handling | Duplicate dispatch, trigger loops, lost feedback, incorrect statuses and broken revision links. | Pause affected triggers; reconcile task/thread state and correct routing. |
| SC-7 — C2, C4, C5, C7: recovery | Errors, timeouts, incomplete responses, unpreserved partial work, repeated effects and exhausted retries. | Establish completed effects and recoverable state; follow bounded recovery or escalate. |

**Operating routine**

- Retain appropriate records for each run.
- Perform applicable automatic checks before delivery.
- Review every output during supervised use.
- Set sample/trend review cadence, thresholds and the responsible owner in D4.
- Minimize sensitive trace content; define access and retention.

Use monitoring signals to guide diagnosis. Establish the cause through investigation.

### 5.5 Respond and improve

**Response sequence**

1. Stop and investigate material incorrect results, boundary breaches or data loss.
2. Link the finding to its capability and success criterion; diagnose the cause and add useful regression cases.
3. Update affected spec, architecture and task-list items; verify the change against relevant evaluations before release.
4. Record accepted limitations with an owner and rationale.

**Match evaluation to the change**

| Change | Evaluation needed |
|---|---|
| New skill | Capability cases and relevant regressions. |
| New tool or access | Boundary and retry checks. |
| Model or orchestration | Broad representative coverage. |
| Purpose or authority | Revisit all plans. |

**Memory changes**

Begin with owner-maintained guidance. Before enabling automatic updates or changing memory policy/schema:

- Define scope, validation, correction, expiry and deletion.
- Define compatibility with software changes.
- Evaluate empty, existing, stale and conflicting memory.
- Plan migration or invalidation, plus rollback.

## 6. Decisions to resolve

These are design decisions, not findings about repository implementation. Owner: Neil Yee, with specialist review where required.

| ID | Decision | Resolve before |
|---|---|---|
| D1 | Exact model/framework versions, settings, dependencies, execution provider/image, and runtime budget enforcement. | Configuration baseline |
| D2 | Selected work capabilities, supported format features and limits, recalculation/conversion/rendering methods, first finance workflow and independent reference answers. | Task evaluation design |
| D3 | Cases, graders, tolerances, repetitions/sample sizes, critical failures, cost/time/call/retry/revision thresholds. | Evaluation and release decisions |
| D4 | Operational owner, signal sources, alert/review cadence, thresholds, trace data/access/retention. | Real-work pilot |
| D5 | Host/storage, identity/access policy, concurrency model, backups, transfer limits, stop/recovery/rollback and state compatibility. | Deployment readiness |
| D6 | Asana eligibility, trigger/status mapping, actionable feedback, publication/approval scope, deduplication and locking. | Asana configuration |
| D7 | Memory ownership/scope, approved references, retention/correction/deletion, and any later automatic-write policy. | Memory use or policy expansion |

## 7. Change log

| Version | Date | Change |
|---|---|---|
| v0.14 | 2026-10-24 | Connected assignment steps to capability IDs and evaluations/monitoring to success criteria; clarified section purposes and reduced repeated explanations. |
| v0.13 | 2026-10-24 | Reordered operating flow before delivery and moved starter tasks alongside evaluation design. |
| v0.12 | 2026-10-24 | Reformatted dense prose into labeled lists, numbered steps and compact tables; separated requirements within capability cells for easier scanning. |
| v0.11 | 2026-10-24 | Moved essential rules into their capability rows, removed the shared-rules section, and relocated technical detail to the architecture. |
| v0.10 | 2026-10-23 | Combined capability, function, mechanism and implementation mappings in one table; consolidated shared requirements and aligned document references. |
| v0.9 | 2026-10-23 | Classified capabilities by reuse scope; made workspace and CSV/Excel/Word/PDF capabilities explicit; connected task composition, design, criteria and evaluation coverage. |
| v0.8 | 2026-10-23 | Recast as intended requirements/design; removed implementation and pass/fail claims. Added explicit artifact and recovery evaluations, decision IDs, and revised lifecycle guidance. |
| v0.7 | 2026-10-23 | Connected capabilities, design, success criteria, evaluations, and monitoring. |
| v0.6 and earlier | 2026-10-22 | Earlier document structures retained in Git history. |
