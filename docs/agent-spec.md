# Finance & Accounting Agent — Agent Specification

| Document field | Value |
|---|---|
| Version | v0.6 working draft |
| Owner | Neil Yee |
| Document date | October 22, 2026 |
| Status | Project plan and proposed design; implementation and verification status is tracked in the [README](../README.md). |
| Configuration version | To be assigned for a release. |
| Initial scope | Platform foundation and one initial finance workflow. |

This specification applies the [agent mental models](mental-model/00-overview.md). The [anatomy](mental-model/01-anatomy.md) defines five agent functions and the mechanisms that implement them. The [ADLC](mental-model/02-adlc.md) defines how people plan, configure, test, deploy, and monitor this agent. See the [architecture](architecture.md) for the component, run, and deployment views, and the [task list](task-list.md) for phase-by-phase project work.

## 1. Purpose

### 1.1 General agent objective

Build a reusable, human-supervised accounting and finance agent that accepts work, gathers relevant context, follows task-specific procedures, and produces outputs people can inspect and approve.

### 1.2 Initial task objectives

| Task scope | Objective | Status |
|---|---|---|
| Platform validation task | Summarize a provided CSV into a reviewable output to exercise the reusable foundation. | Starter task; completion alone does not establish finance quality or release readiness. |
| First finance workflow | Reconcile a bank statement to a ledger, identify matches and exceptions, and produce reviewable supporting work. | Monthly bank reconciliation is provisional; known-answer cases and acceptance thresholds are still being prepared. |
| Later task-specific skills | Add a specific work objective and procedure while reusing the shared agent capabilities and controls. | Each task type should have its own workflow or skill detail and evaluation cases. |

The foundation is intended to support additional finance tasks over time. A successful demonstration of one task is not a finance-quality or release claim.

### 1.3 Scope and boundaries

| In scope for the initial foundation | Out of scope initially |
|---|---|
| Local agent foundation; persistent threads; optional sandbox execution; input-copy and output-preservation workflow; a narrow platform CSV task; preparation for a first finance skill. | Posting journal entries, initiating payments, changing authoritative ERP records, sending external communications, or editing original shared files. |
| Human-readable artifacts, supporting code where useful, run provenance, and human review. | Automatically promoting scripts, models, skills, memory, or permission changes without separate approval. |
| Provisional bank-reconciliation procedure and fictional demonstration context. | Claiming verified finance quality before independently known cases and human review pass. |

The first finance workflow is a candidate, not yet a demonstrated capability. Real company policies and access are not configured.

### 1.4 Output standard

Each completed task should provide an artifact appropriate to the request, a concise summary, unresolved issues or missing inputs, and supporting code or provenance when those help review. Financial artifacts should state the reporting period, units/currency, sources, assumptions, calculations, tie-outs, exceptions, and applicable limitations. Review approval applies to the identified output version only; it does not approve reusable assets or permissions.

## 2. Capabilities: anatomy, mechanisms, implementation

This section describes the reusable capabilities through the agent's five functions, then maps each function to the mechanisms that implement it and the current project status. A task-specific skill applies these capabilities to one defined objective. A mechanism is the implementation means; it is not itself the function. The README remains the detailed implementation inventory.

### 2.1 Core: what reasons and drives the work

| Decision | Current mechanism and status |
|---|---|
| Model | OpenAI chat model through the Deep Agents harness. Model and reasoning settings are configurable. |
| Loop | Harness control loop assembles context, invokes the model, routes tool requests, returns tool results to context, and stops on a final answer or enforced limit. |
| Planning | `TodoListMiddleware` exposes `write_todos`; todo state is checkpointed with the conversation. The model decides when a plan is useful. |
| Limits and stopping | Runtime controls implement shared model/tool-call budgets, a deadline, timeout caps, retries, and bounded sandbox commands. Some live enforcement remains unverified; cost is not a hard monetary cap. |

### 2.2 Context: what the model sees

| Context source | Function in the agent | Mechanism and current status |
|---|---|---|
| Task request and attachments | Define the work and its inputs. | Current: terminal prompt and files available in the selected thread. Planned: Asana fields, comments, attachments, trigger reason, and relevant changes gathered by a dispatcher. |
| Instructions | Define purpose, boundaries, and how to work. | Agent instructions assembled for each model call; project guidance is also maintained in `memory/AGENTS.md`. |
| Conversation and prior tool results | Let the stateless model continue the current run/thread. | Harness builds each model input from current graph state and history; SQLite checkpointer restores thread state. |
| Skills | Supply task procedures. | `SkillsMiddleware` exposes skill descriptions; file tools load the relevant `SKILL.md` from the read-only `/skills/` route. CSV analysis, file-delivery validation, and bank-reconciliation procedures exist. The finance procedure has not passed task evaluation. |
| Business knowledge | Supply entity and operating conventions. | `MemoryMiddleware` and read-only `/memories/` route; the current company profile is fictional demonstration context, not a real-company policy. |
| Prior outputs during a revision | Let a follow-up run see the work it is revising. | Current: prior files remain in the same thread workspace. Planned Asana workflow: dispatcher gathers the prior output version and relevant review feedback. |

The model input is assembled anew for each call. Memory, skills, and prior messages are not independent model capabilities; their contents reach the model through context assembly and tool results.

### 2.3 Actions: what the model can request

| Action | Mechanism | Execution location and access |
|---|---|---|
| Read, list, create, and revise working files | Built-in filesystem tools | In sandbox mode, ordinary working paths route to the temporary remote sandbox's `/workspace`; in default mode they use the thread's virtual filesystem. |
| Run general code | `execute` tool | Temporary LangSmith sandbox in sandbox mode. The agent/model client runs on the host; generated commands execute remotely. |
| Read approved skills and memory | File tools over routed backends | Local host routes, read-only to the agent; these are virtual routes, not sandbox mounts. |
| Delegate a subtask | General-purpose sub-agent capability from the harness | Separate model loop with its own input; remains within the configured agent/runtime boundaries. |
| Read external business systems | Not implemented for this prototype | A future controlled connector or MCP server may provide narrowly scoped, initially read-only access outside the sandbox. No ERP, SharePoint, or Google Drive integration is currently connected. |
| Intake or update a work tracker | Not implemented for Asana | Future dispatcher/connector may gather assignments and publish status, summaries, and output links under separate controls. |

Task inputs are copied to the sandbox and original working files are not modified. The app downloads new or changed workspace files before cleanup. Workspace transfer is copy-in/copy-out, not a live mount or continuous cloud sync.

### 2.4 Controls: which requests are allowed

| Control | Strength/mechanism | Current rule and status |
|---|---|---|
| Instruction boundaries | Instruction in model context | State the task scope and prohibitions; instructions alone are not an enforcement boundary. |
| Read-only approved references | Backend/environment routing | Mutations to `/memories/` and `/skills/` are rejected by the routed backend. Owner maintains these files. |
| Tool and run limits | Runtime hook/control | Shared call budgets, run deadline, bounded commands, model timeout/retries, and tool timeout caps are implemented; live enforcement is tracked in the README. |
| Sandbox isolation | Execution environment | Temporary sandbox, restricted execution, and owner-configurable network allowlist. Effective network isolation has not been verified. The local `.env` and API keys are not copied into the sandbox. |
| Source protection | Workspace transfer mechanism | Inputs are working copies. Local versions and conflicts are preserved; remote deletion is not propagated locally. This is not a guarantee against every application-level edit or data loss. |
| Deliverable review | Human decision and local review record | A local reviewer can approve/reject a successful run's unchanged file manifest. Automated Asana review and an in-flight interrupt are not implemented. |
| Reusable asset promotion | Human approval | Scripts, models, memory notes, skills, and permission changes require separate approval from task-output approval. Proposal workflow is not automated. |
| External-system writes | Not enabled | No ERP posting, payments, shared-file edits, or external communications. Future external access requires owner-controlled authorization and separate tests. |

Controls must be drawn and evaluated at the strength they actually have: a model instruction, a program check/hook, a human approval, or an environment boundary. A design statement alone does not prove enforcement.

### 2.5 Continuity: what carries over

| Item | Decision and mechanism |
|---|---|
| Within a model run | The harness carries messages, tool results, and todo state in graph state and includes relevant history in subsequent model inputs. |
| Across prompts in a thread | SQLite graph checkpoints persist conversation state; a thread ID groups the saved conversation. Terminal startup resumes the selected/last thread for the mode. |
| Working files | `workspace/threads/<thread-id>/` persists locally. Sandbox mode copies eligible files into `/workspace` for a run and merges new/changed files back, preserving versions and conflicts. |
| Approved knowledge and skills | Owner-maintained local Markdown under `memory/` and `skills/`; read-only agent routes. No automatic learning or silent promotion. |
| Run provenance and review | Local work log stores run outcomes, fingerprints, call/transfer events, validation findings, and review records. LangSmith tracing is optional. Neither is assumed to capture every internal sandbox operation. |
| Configuration identity | Release/evaluation evidence should identify the Git commit, lockfile, model settings, sandbox snapshot, and approved skills/memory. The current CSV report does not yet capture this complete record. |

### 2.6 Success criteria

These criteria describe the outcomes expected from the capabilities above. Their evaluation status is shown in Section 3.1.

| ID | Success criterion |
|---|---|
| SC-1 | For each released task type, the agent produces results that meet independently defined, task-specific acceptance checks on known-answer cases. |
| SC-2 | Source inputs remain unchanged, and new or changed deliverables and supporting files are preserved after sandbox cleanup and can be associated with the correct run. |
| SC-3 | The agent stays within its configured permissions and operating limits. Human approval is required for deliverables and separately for changes to reusable assets or access. |
| SC-4 | A reviewer can inspect the output, its assumptions and exceptions, relevant inputs, checks performed, and the configuration/run provenance needed to understand the result. |
| SC-5 | The foundation and first finance workflow pass defined release gates, with an owner, data policy, bounded access, tested stop/recovery, and monitoring plan, before hosted or expanded real-work use. |
| SC-6 | Before Asana automation is enabled, the task-to-review lifecycle works without duplicate runs or trigger loops, and preserves task context and outputs through revisions and restart. |

### 2.7 Work lifecycle and interface

This describes how people assign work, receive results, and review or revise them. It follows the agent capabilities because the interface is one way to operate the configured agent.

| Item | Current decision |
|---|---|
| How work arrives | Local terminal prompt. Asana is the intended work interface after the foundation and first finance workflow are ready. |
| Task scope | One conversation thread per work item is the target for the Asana workflow. Current terminal threads are persistent but are not mapped to Asana tasks. |
| How results return | Local prototype: final response and files in the selected thread workspace. Planned Asana workflow: status, summary, unresolved issues, and output links. |
| Review and feedback | Current local review records a decision against a successful run's unchanged file manifest. Planned Asana review happens between runs; actionable feedback starts a revision in the same task thread. |
| Statuses | Planned: **To do → Agent working → Needs review → Done**, with **Blocked** for work that cannot continue. |

Asana eligibility rules, status representation, trigger mechanism, approval semantics, and actionable-feedback rules remain open. Informational comments must not automatically start revisions; agent-generated status updates must not trigger duplicate runs.

## 3. Plans

The ADLC phases are **Build (Plan, then Configure) → Test → Deploy → Monitor → back to Build**. Plan creates the evaluation, release, and monitoring plans before testing; Configure implements them; Monitor findings become diagnosed changes and regression cases. See the [ADLC reference](mental-model/02-adlc.md).

### 3.1 Evaluation plan

Each evaluation row connects a project outcome to the anatomy function, its implementation mechanism, a specific check, and reviewable evidence. The criteria below are planned gates, not claims that the system has passed them.

| Eval | Objective / criterion | Function and possible failure | Mechanism under test | Check, grader, and cases | Pass condition / current status |
|---|---|---|---|---|---|
| E-PLAT-1 | SC-1: platform foundation handles the starter task correctly. | Core: fails to stop or complete within configured limits. Context: wrong/missing skill or source. Actions: wrong calculation/output. | Control loop and runtime caps; prompt/context assembly; skill retrieval; file tools; sandbox `execute`. | Two starter CSV cases with exact expected JSON, source-byte checks, and recorded call/time behavior; deterministic code grader. Repeat runs are needed for reliability claims. | Each case completes normally within configured limits, exact outputs match, and source bytes are preserved. Starter suite is drafted, not yet run as the planned evaluation; earlier single smoke tasks are not a substitute. |
| E-FILE-1 | SC-2: preserve working inputs and outputs across sandbox cleanup/restart. | Actions and Continuity: input altered, output lost, conflict overwritten, state fails to resume. | Workspace transfer, hash/version/conflict handling, thread checkpoint. | Synthetic text, XLSX, and binary transfer cases; restart and concurrent-local-edit cases; deterministic checks. | All preservation and conflict rules pass, output survives cleanup, thread resumes. Transfer check passed; broad recovery/restart release evaluation remains incomplete. |
| E-FIN-1 | SC-1: first finance workflow reconciles to independent known results. | Context: wrong procedure/business assumptions. Actions: missed/false matches, wrong balances or deliverables. | Bank-reconciliation skill, code/calculation, workbook/document generation and validation. | Synthetic bank/ledger cases with expected matches, exceptions, balance bridges, proposed entries, source preservation, and Excel/Word artifacts; code grader plus human finance review. | All defined critical checks pass and a reviewer accepts a representative output. Fixtures and acceptance thresholds are still to be completed; evals have not run. |
| E-CTRL-1 | SC-3: stay within permissions and limits. | Core and Controls: runaway loop, unauthorized write, prompt injection or exposed credential. | Control loop and runtime hooks, read-only backend routes, sandbox/network policy, external identity. | Offline call/time/boundary cases; sandbox network/secret checks; adversarial inputs. | Limits stop the run and requests outside scope are blocked at the appropriate program or environment layer; effective egress enforcement is verified. Offline engineering checks passed; live enforcement and production identity remain unverified. |
| E-PROV-1 | SC-4: reviewers can inspect what produced an output. | Continuity and Context: output cannot be tied to inputs, run, or configuration. | LangSmith tracing, work log, transfer manifest, validation report, configuration record. | Follow known runs from prompt/input fingerprints to tool events, artifacts, check results, and human decision. | Required provenance is present and reviewable without assuming traces alone prove correctness. Tracing and local records exist; full release provenance is incomplete. |
| E-REL-1 | SC-5: establish readiness before hosted or expanded real-work use. | Controls and Continuity: inadequate access, no stop/recovery, or no accountable review. | Release checklist, configuration identity, permissions, operational limits, stop/rollback, and monitoring ownership. | Owner-led readiness review against recorded eval results, access, data policy, stop/recovery rehearsal, and monitoring plan. | Every required item is confirmed and unresolved risks are recorded; no release proceeds on an unverified assumption. Not yet completed. |
| E-ASANA-1 | SC-6: eventual task-to-review lifecycle works without duplicate or looped runs. | Actions, Controls, Continuity: duplicate dispatch, trigger loop, missing failure state or lost revision context. | Dispatcher, Asana connector, task/thread mapping, locking, persistence and status controls. | End-to-end normal, feedback/revision, duplicate-update, failure/Blocked, restart and recovery cases. | Five consecutive test tasks complete the defined path; no duplicate/loop runs; outputs and context survive restart. Asana is not implemented; evaluation is future work. |

For every evaluation, record whether it checks a final output, trajectory, or individual step; who grades it (code, calibrated LLM judge, or person); whether cases are normal, edge, or adversarial; and the explicit threshold. Use deterministic grading where answers are known. Use an LLM judge only for subjective criteria after comparison with human judgments; retain human review for consequential finance judgments and document presentation.

**Coverage rule:** every success criterion and every anatomy function must map to at least one evaluation. Use the anatomy failure analysis and run path in the [ADLC eval-design guide](mental-model/02-adlc.md#3-evals). A capability case that passes reliably becomes a regression case. A successful trace is evidence of a particular run, not a pass on its own.

### 3.2 Release plan

No hosted service or production deployment is currently implemented. Until release gates pass, use this as a local prototype with synthetic data or specifically approved tasks and human review.

| Stage | Use | Gate to advance |
|---|---|---|
| 0. Local evaluation | Engineering checks, synthetic datasets, and reviewed examples; outputs do not drive business actions. | Planned evaluation criteria pass, limitations are recorded, and configuration provenance is available. |
| 1. Parallel run | For approved real tasks, run alongside the normal process; agent output is not authoritative. | Outputs agree with the normal process on a defined representative sample; failures and discrepancies are understood. |
| 2. Supervised use | Outputs may support work, with a person reviewing every deliverable before use. No posting or payment actions. | A defined period and sample meet agreed thresholds; stop and recovery procedures have been exercised. |
| 3. Expanded use | Consider risk-based review only after evidence supports it and controls remain effective. | Owner approval, monitoring thresholds, access review, and rollback readiness are confirmed. |

Before release, name an owner; confirm data handling and least-privilege identities; identify the exact agent configuration and sandbox release; pass the release gate; set model/tool/time and cost limits; and test output preservation, failure handling, and recovery. Record how to stop new work, handle in-flight runs, disable external triggers, and return to the last known-good configuration. Identify outputs from a faulty release for re-review.

The local runner has no dispatcher-level stop control or distributed exactly-once guarantee. Snapshot rollback exists but has not been exercised live. A configured egress allowlist is not proof of enforced network isolation. Resolve these before an automated Asana rollout.

### 3.3 Monitoring plan

| Anatomy function | Signals to review | Current source / gap |
|---|---|---|
| Core | Completion/error rate, elapsed time, model/tool calls, usage/cost where available. | LangSmith and local run records; production thresholds and ownership are not set. |
| Context | Right skill/business context, unsupported assumptions, missing-input questions, repeated misunderstandings. | Trace and human review; systematic labels are not yet defined. |
| Actions | Tool failures, transfer conflicts, artifact checks, calculation tie-outs, reviewer corrections. | Tool/transfer records and validation; finance checks incomplete. |
| Controls | Limit hits, refusals, boundary attempts, unauthorized external actions. | Runtime and sandbox records; egress enforcement is unverified. |
| Continuity | Resume failures, missing/stale files, revision rounds, stale review after file changes. | Checkpointer, workspace manifest, work log; service-level recovery not implemented. |
| Overall | Approval/rejection rates, unresolved discrepancies, repeated failures, drift by task/configuration. | Local review/work log; thresholds and operational owner remain open. |

- **Every run:** retain configuration/run identity, status, limits, tool and transfer events, output checks, and review outcome. Run applicable deterministic tie-outs and integrity checks before presenting outputs.
- **Human review:** review every output during early supervised use. Reduce the sample only after workload and risk-based thresholds are defined and evidence supports the change.
- **Trend review:** periodically examine errors, corrections, approvals/rejections, revisions, and operating cost. Set cadence and thresholds before a hosted pilot.

Stop and investigate a boundary breach, data loss, or material incorrect result. Diagnose repeated failures to a function or lever, update the configuration, and add a regression case. Record accepted one-off issues and workarounds. Monitoring does not silently change approved memory, skills, or permissions.

## 4. Current implementation and future deployment choices

| Area | Current prototype | Future decision / gap |
|---|---|---|
| Host and work interface | Local terminal application; model client and agent loop run on the host. | Choose hosted dispatcher/runtime and implement Asana intake, status, review, revision, and duplicate/loop prevention. |
| Model and tracing | OpenAI model; optional LangSmith tracing. | Confirm model/provider policy, trace retention, access, and approved data handling. |
| Code execution | Temporary LangSmith sandbox, selected by immutable snapshot ID. | Verify production sandbox policy, enforceable egress, resource ceilings, and recovery behavior. |
| Checkpoints and workspace | Local SQLite checkpoints and per-thread local folders. | Choose durable hosted storage, backup, retention, and restore procedures. |
| Finance workflow | Bank-reconciliation skill and fictional profile are drafts; end-to-end known-answer evaluation remains pending. | Define fixtures, critical acceptance checks, review, and operating policy before any finance-quality claim. |
| External business systems | No ERP, SharePoint, or Google Drive connection. | Any future connector/MCP needs named identity, least privilege, access boundary, and its own evals. No posting/payments. |

Planned Asana-enabled run: gather task context and changes; create a sandbox and task workspace; copy in inputs and approved assets; execute; preserve outputs, code, proposals, and failure details; clean up; publish status, summary, and links. One task maps to one thread for revisions. This is a design goal, not current integration behavior.

## 5. Open decisions

Resolve these before the corresponding integration or release stage:

- Asana eligibility rules, trigger mechanism, status representation, actionable feedback, and output-version approval semantics.
- Dispatcher locking, duplicate prevention, and prevention of agent-generated trigger loops.
- Deployment host, service identity, durable workspace/checkpoint storage, retention, and recovery procedure.
- How filesystem/network restrictions are enforced and verified under the selected sandbox provider.
- Per-stage cost ceiling, execution/model-call limits, and revision limits.
- Release-gate thresholds, human-review sample/cadence after supervised use, and monitoring owner.
- Workbook recalculation method where required by the first finance skill.
- Bank-reconciliation acceptance criteria and independently known evaluation fixtures.
- Data policy and least-privilege design before any real-company information or external connector is used.

Keep the implementation focused on one agent. Evaluate the foundation and first finance workflow before adding Asana; verify the complete task-to-review path before expanding capabilities or memory infrastructure.

## 6. Change log

| Version | Date | Change |
|---|---|---|
| v0.6 | 2026-10-22 | Separated the general agent objective from initial task objectives; placed capabilities before success criteria and moved the work interface after them. |
| v0.5 | 2026-10-22 | Reorganized around anatomy functions and mechanisms; connected success criteria to evals and added links to the mental models, architecture, and project task list. Preserved current prototype scope and release gaps. |
| v0.4 | 2026-10-21 | Previous structure retained in Git history; v0.5 reorganizes its project decisions around the anatomy and ADLC. |
