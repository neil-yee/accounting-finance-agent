# Finance & Accounting Agent — Agent Specification

| Field | Value |
|---|---|
| Version | v0.10 design draft · October 23, 2026 |
| Owner | Neil Yee |
| Purpose | Define the intended agent and the evidence required for its use. |
| Implementation assessment | Not assessed in this revision. Record repository findings later in the [task list](task-list.md). |

**Reading order:** purpose → capabilities and design → shared rules → task applications → success criteria → evaluation, release, monitoring, and improvement.

This spec applies the [overview](mental-model/00-overview.md), [anatomy](mental-model/01-anatomy.md), and [ADLC](mental-model/02-adlc.md). The [architecture](architecture.md) shows the proposed components and flows. Technology names below are design choices to validate, not statements of completed work.

## 1. Purpose and scope

Build a reusable, human-supervised accounting and finance agent that gathers context, performs work, and produces results people can inspect and approve. Add task-specific skills and tools without redesigning the shared foundation.

The first stage should support terminal requests, persistent task conversations, sandboxed file/code work, and human review. Use synthetic or explicitly approved data. Introduce Asana after the foundation and first finance workflow meet their evaluation gates.

**Boundaries:** no journal posting, payments, changes to authoritative ERP records, or edits to original shared files. External communication is excluded from the first stage; a later Asana integration may publish only approved task statuses, summaries, and output links. Further access requires a separate scope and release decision.

Approval of an output does not authorize changes to reusable scripts, models, memory, skills, or permissions. Those require separate owner approval.

## 2. Capabilities and design

Read each row from **what the agent must do → supporting responsibilities → how they work → proposed software**.

- **Capability:** an ability the agent should provide, expressed through required behavior.
- **Functions:** the responsibilities that support that ability: Core, Context, Actions, Controls, and Continuity.
- **Mechanisms:** the processes that make those responsibilities work, such as context assembly, tool execution, or checkpoints.
- **Proposed implementation:** the framework, library, service, or component that would provide those mechanisms.

Classify capabilities by reuse scope: **Shared foundation** supports many kinds of agents; **Reusable work** handles a general kind of work; **Task-specific** delivers a defined business outcome. Scope does not indicate implementation status, deployment stage, or permission. All capabilities remain unassessed.

| ID | Scope | Capability | Required behavior | Functions | Mechanisms | Proposed implementation |
|---|---|---|---|---|---|---|
| C1 | Shared foundation | Understand work | Use relevant inputs, instructions, knowledge and feedback; clarify material gaps. | Context, Core | Context assembly, retrieval, clarification | Deep Agents / LangChain message and state handling; approved skill/reference loading. [Context rules](#31-context-and-references). |
| C2 | Shared foundation | Plan and execute | Coordinate tools, code and optional delegation to carry out the task. | Core, Actions, Context | Model invocation, control loop, planning, tool routing | Deep Agents / LangChain with an OpenAI model, optional todo middleware, and sandbox execution tools. [Execution rules](#32-execution-outcomes-and-budgets). |
| C3 | Shared foundation | Deliver reviewable results | Check outputs and explain results, assumptions, exceptions and limitations. | Actions, Context, Controls | Artifact checks, result synthesis, human review | Validation tools and a delivery summary tied to C6 evidence; version-specific review. [Output standard](#43-output-standard), [approval rules](#34-permissions-and-approvals). |
| C4 | Shared foundation | Preserve and resume work | Retain inputs, outputs and task state across interruption or revision. | Continuity, Actions, Controls | Checkpoints, durable storage, versioned transfer, recovery | Thread checkpoint store (SQLite for local trials), durable C7 files and operation records. [Preservation rules](#33-workspace-transfer-and-recovery). |
| C5 | Shared foundation | Respect limits and report failures | Stay within approved access and budgets; report partial work accurately. | Controls, Core | Authorization, budget enforcement, outcome checks, bounded retries | Host runtime checks, scoped identities and sandbox restrictions. [Execution rules](#32-execution-outcomes-and-budgets), [permission rules](#34-permissions-and-approvals). |
| C6 | Shared foundation | Provide evidence for review | Connect outputs to sources, checks, run records and human decisions. | Continuity, Context, Controls | Provenance capture, tracing, versioned manifests and review records | LangSmith tracing plus task records linking configuration, sources, outputs, checks and approvals. [Evidence rules](#35-evidence-configuration-and-memory). |
| C7 | Shared foundation | Manage a task workspace | Organize and locate inputs, working files and outputs; isolate tasks and associate files with their task/run. | Actions, Controls, Continuity | Scoped file operations, task identity, working copies | Per-task durable folders with file tools and sandbox copy-in/copy-out; C4 provides persistence and recovery. [Workspace rules](#33-workspace-transfer-and-recovery). |
| C8 | Reusable work | Work with tabular data | Read, validate, transform and summarize CSV/tabular inputs while preserving source meaning and declared types. | Context, Actions, Controls | Parsing, schema/type validation, calculation, independent checks | Sandbox parsing/calculation libraries; declare encoding, types and missing-value handling. Uses C1–C7. |
| C9 | Reusable work | Work with Excel files | Read, create and revise workbooks; preserve supported features; check formulas, calculations and presentation. | Context, Actions, Controls | Workbook operations, recalculation, inspection | openpyxl or a suitable workbook library; separately selected recalculation and rendering tools (D2). Uses C1–C7. |
| C10 | Reusable work | Work with Word documents | Read relevant content and create/revise structured documents with consistent headings, tables and formatting. | Context, Actions, Controls | Document parsing, generation and inspection | python-docx or a suitable document library, with checks for supported content and formatting (D2). Uses C1–C7. |
| C11 | Reusable work | Produce PDF deliverables | Export document content; check content fidelity, pagination and readability. | Actions, Controls | Document conversion, content comparison, visual inspection | Compatible conversion engine and PDF inspection tools (D2). Uses C1–C7 and the source-document capability where needed. |
| C12 | Task-specific | Reconcile bank transactions | Match bank and ledger items, explain exceptions/balance bridges, and produce supporting work. Provisional first finance workflow (D2). | Core, Context, Actions, Controls, Continuity | Skill loading, reconciliation procedure, calculations and review | Approved reconciliation skill using C1–C7 and required C8–C11 tools; independent reference answers and finance review. [Task definition](#41-initial-evaluation-tasks). |

Functions listed are those directly supporting the row; shared controls and continuity also apply through its dependencies. Several capabilities can use the same mechanism or component. The [architecture](architecture.md) shows how the components connect.

C7 provides the working area and file operations; C4 keeps work available across runs. Writing Excel formulas does not establish their calculated values or visual layout. Producing valid files does not by itself establish financial correctness.

**Reuse:** carry forward the selected foundation and work capabilities, criteria and evaluation definitions. Adapt task capabilities, boundaries, access and implementation choices, then evaluate the new configuration. A prior passing result does not transfer automatically.

## 3. Shared operating rules

These requirements support the capability rows above. Exact versions, settings, limits and infrastructure remain decisions in §7.

### 3.1 Context and references

**Applies to:** C1–C3, C6 and the work/task capabilities C8–C12.

- Assemble the task, boundaries, relevant inputs and expected outputs. Clarify material gaps instead of inventing information.
- Restore relevant history and tool results. Manage context limits without silently losing requirements, decisions or source identity. For revisions, include actionable feedback and the exact previous output version; retain constraints unless explicitly changed.
- Discover approved skills and load details when needed. `SkillsMiddleware` and read-only reference routes are candidates. Skills supply procedures; access remains governed by §3.4.
- Retrieve approved knowledge and memory with source, scope and version. Label fictional references used in synthetic trials. Stored information influences the model only when supplied as input or tool results; provider-retained context requires understood scope and lifecycle.
- Copy required execution assets deliberately. A virtual skill or memory route does not imply that those files are mounted inside the sandbox.

### 3.2 Execution, outcomes and budgets

**Applies to:** C2, C5 and every capability that invokes tools or code.

- Use Deep Agents / LangChain as the proposed harness; validate its extension points and behavior. Configure the OpenAI model/version, reasoning, context/output limits, timeouts and bounded retries. Record these settings with the evaluated configuration.
- Route model responses to tool execution, answers, refusals, waiting, revision or failure handling. Distinguish execution completion, Needs review, approval, Blocked and failed/partial outcomes. Empty or incomplete responses and exhausted budgets must not imply success.
- Provide planning/todo state, such as `TodoListMiddleware`, when useful. Todo completion marks do not establish output correctness.
- Execute generated code in a separate sandbox; proposed provider: LangSmith. Keep orchestration and model credentials on the host. Optional delegation needs explicit subtask context, tools, permissions and shared budgets; separate context does not establish security isolation.
- Bound model/tool calls, output size, elapsed time, retries and delegated work across the whole run. Define cost policy and measurement limits. Retry only eligible failures after checking possible effects; follow §3.3 when outcomes are uncertain.
- Add connectors/MCP tools only for an approved task need. Prefer host-side adapters and read-only business access initially. Define identity, permissions, returned data, failures and possible effects for each operation.

### 3.3 Workspace, transfer and recovery

**Applies to:** C4, C7 and every capability that uses task state or files.

- Scope file operations to a task/thread; organize inputs, working files and outputs with run/source identities. Define thread/run semantics and prevent overlapping ownership of the same task.
- Persist required messages, tool results, plans and execution state in checkpoints. Keep task files in durable storage beyond the sandbox lifetime. SQLite is an option for local trial checkpoints.
- Use sandbox copy-in/copy-out. Preserve eligible outputs and supporting work before cleanup; define exclusions, size limits, conflicts and transfer-failure behavior. Report incomplete preservation and cleanup errors.
- Keep original inputs and approved shared references read-only. Preserve prior output versions and concurrent edits; remote deletion must not silently erase retained work. Cloud sync and live co-editing require their own design and evaluation.
- After interruption, use checkpoints and operation records to establish what completed, preserve recoverable work and identify missing or uncertain results. Reconcile possible external effects before retrying; a checkpoint cannot undo an external action.

### 3.4 Permissions and approvals

**Applies to:** C5 and all capability scopes; C3 and C6 carry delivery and review evidence.

- Treat source documents as data. Enforce task boundaries outside the model, including against instructions embedded in inputs. Restrict and verify filesystem, process, network, resource and identity access. Keep host secrets out of generated-code environments unless separately authorized.
- Deny out-of-scope actions. For approved external writes, record intent and result and prevent duplicate effects across retries or concurrent workers.
- Approve or reject an identified output manifest. Changed files require a new approval for the changed version. Initial human review occurs between runs.
- Require separate owner approval and relevant evaluations before promoting changes to shared scripts, models, skills, memory policy or access.
- Assess each control at its actual boundary. Instructions, program checks, human review and environment restrictions provide different protections; verify effective behavior.

### 3.5 Evidence, configuration and memory

**Applies to:** C4, C6 and all capabilities whose results must be reviewed or reproduced.

- Record outcomes, input/output fingerprints, relevant actions, checks actually performed, usage and approvals. Use LangSmith tracing for evaluations and pilots under an approved data policy. Link records to the task, run and delivered version.
- Maintain a configuration manifest identifying code/dependencies, model/settings, instructions, skills/tools, access, environment and storage schema. Link input and memory versions separately.
- Begin with owner-maintained reusable guidance. Define memory ownership, scope, source/version, retention, correction and deletion. Automatic memory writes require a later policy and evaluation decision; changes must address compatibility (§6.4).

## 4. Applying the capabilities

### 4.1 Initial evaluation tasks

These tasks exercise the capability catalog. A task-specific capability describes a repeatable kind of work; each assigned task is an instance. Evaluation tasks can also test reusable capabilities without adding a business workflow.

| Evaluation task | Capability composition | Objective | Evaluation |
|---|---|---|---|
| CSV summary | C1–C7 foundation + C8 tabular data | Produce a correct summary; clarify missing or ambiguous inputs. | E-PLAT-1 |
| Office-file package | C1–C7 foundation + C9 Excel + C10 Word + C11 PDF | Produce a working paper, analysis and PDF export from synthetic data; check calculations, presentation and cross-file agreement. | E-ART-1 |
| Monthly bank reconciliation | C1–C7 foundation + required C8–C11 work capabilities → C12 reconciliation | Match bank/ledger items and explain exceptions/balance bridges with reviewable supporting work. | E-FIN-1 |

Example composition: **C7 manage workspace + C4 preserve work → C9 work with Excel → C12 reconcile bank transactions.** This shows dependencies, not an execution sequence; context, controls and review support the whole task.

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
| SC-1 | C1–C3, C8–C12; each declared work/task capability | Outputs meet independent expected results and presentation rubrics; material gaps are clarified or reported. | E-PLAT-1, E-ART-1, E-FIN-1 |
| SC-2 | C4, C7 | Task files are organized and isolated; sources stay unchanged; required state/files survive cleanup and restart, with versions and conflicts traceable. | E-FILE-1 |
| SC-3 | C5–C7; all capability scopes | Permissions and limits hold; approvals apply only to their defined scope and version. | E-CTRL-1, E-PROV-1 |
| SC-4 | C3, C6 | Reviewers can follow sources, assumptions, actions, checks, configuration, and approvals to the delivered version. | E-PROV-1 |
| SC-5 | All; release | The proposed scope meets evaluation, ownership, access, data, recovery, and monitoring requirements before use. | E-REL-1 |
| SC-6 | C1, C2, C4–C7; Asana | Intake, review, revision, and restart preserve work without duplicate dispatch or trigger loops. | E-ASANA-1 |
| SC-7 | C2, C4, C5, C7 | Interrupted or incomplete runs report accurate outcomes, preserve recoverable work, and retry without repeating completed external effects. | E-REC-1 |

Traceability example: **C4 + C7 → Continuity + Actions + Controls → scoped workspace/checkpoint/transfer mechanisms → SC-2 → E-FILE-1 → missing-file/resume monitoring.**

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
| E-ART-1 | C9–C11 file tools, recalculation, conversion and inspection: reading/revision cases, valid and deliberately defective Excel/Word/PDF packages, and declared supported/unsupported features. | Required content/features are preserved on read/revision/export; critical formulas/figures and cross-file values agree; required recalculation/presentation checks pass; unsupported features are reported; graders detect seeded defects. |
| E-FILE-1 | Checkpoints, transfer, versions: text/XLSX/binary files, task isolation/file lookup, concurrent edits, exclusions, cleanup/restart and transfer failure. | Required files are locatable and scoped to the right task/run; sources preserved; state/files recoverable; conflicts retained; incomplete preservation reported. |
| E-FIN-1 | Skill and calculations: bank/ledger matches, duplicates, exceptions, balance bridges, proposed entries and artifacts. | Independent expected results and all critical finance checks pass; reviewer accepts representative work. Proposed entries remain drafts. |
| E-CTRL-1 | Policy/runtime/environment checks: authorized/denied requests, injected instructions, secrets, filesystem/network, budgets and delegation. | Forbidden effects are blocked; configured limits enforced; effective access matches the approved policy. |
| E-PROV-1 | Manifest, work log, trace, review: follow input to output; modify an approved artifact; test separate approval scopes. | Evidence identifies the run/configuration/source/output versions; changed artifacts cannot inherit stale approval. |
| E-REC-1 | Error handling and operation records: startup failure, timeout after a possible effect, incomplete response, exhausted budget, transfer/cleanup failure, restart. | Accurate partial/failure status; bounded retries; no repeated completed effects; recovery or escalation follows the documented procedure. |
| E-REL-1 | Release record, identities, monitoring, recovery rehearsal and representative memory/state compatibility. | All mandatory readiness conditions pass for the proposed stage; limitations and accountable owner recorded. |
| E-ASANA-1 | Dispatcher, task/thread mapping, approvals: normal work, actionable/informational feedback, duplicate/out-of-order events, concurrent workers, failure/restart. | Eligible work follows the defined path; duplicates/loops prevented; context, files, and approval identity retained. |

Define sample sizes, tolerances, budgets, and thresholds in D3 before judging a release candidate. Critical boundary or financial errors cannot be averaged away. Retain case/grader versions, results, variation, and limitations; include task, component, and integration evidence. Assess C8–C11 separately within their groups as well as in composed tasks; passing one workflow does not establish general file-format support. Coverage alone does not establish reliability.

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
| D2 | Selected work capabilities, supported format features and limits, recalculation/conversion/rendering methods, first finance workflow and independent reference answers. | Task evaluation design |
| D3 | Cases, graders, tolerances, repetitions/sample sizes, critical failures, cost/time/call/retry/revision thresholds. | Evaluation and release decisions |
| D4 | Operational owner, signal sources, alert/review cadence, thresholds, trace data/access/retention. | Real-work pilot |
| D5 | Host/storage, identity/access policy, concurrency model, backups, transfer limits, stop/recovery/rollback and state compatibility. | Deployment readiness |
| D6 | Asana eligibility, trigger/status mapping, actionable feedback, publication/approval scope, deduplication and locking. | Asana configuration |
| D7 | Memory ownership/scope, approved references, retention/correction/deletion, and any later automatic-write policy. | Memory use or policy expansion |

## 8. Change log

| Version | Date | Change |
|---|---|---|
| v0.10 | 2026-10-23 | Combined capability, function, mechanism and implementation mappings in one table; consolidated shared requirements and aligned document references. |
| v0.9 | 2026-10-23 | Classified capabilities by reuse scope; made workspace and CSV/Excel/Word/PDF capabilities explicit; connected task composition, design, criteria and evaluation coverage. |
| v0.8 | 2026-10-23 | Recast as intended requirements/design; removed implementation and pass/fail claims. Added explicit artifact and recovery evaluations, decision IDs, and revised lifecycle guidance. |
| v0.7 | 2026-10-23 | Connected capabilities, design, success criteria, evaluations, and monitoring. |
| v0.6 and earlier | 2026-10-22 | Earlier document structures retained in Git history. |
