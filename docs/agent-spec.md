# Finance & Accounting Agent — Agent Specification

| Field | Value |
|---|---|
| Version | v0.7 working draft · October 23, 2026 |
| Owner | Neil Yee |
| Status | Local prototype. Requirements below are targets; verification is tracked in the [README](../README.md#implementation-status). |
| Release configuration | Not yet assigned. |

**Reading order:** purpose → shared capabilities → how they work → task applications → success criteria → evaluation, release, monitoring, and improvement.

The [mental models](mental-model/00-overview.md) define the vocabulary. This spec defines the agent; the [architecture](architecture.md) shows its components; the [task list](task-list.md) tracks implementation work.

## 1. Purpose and scope

Build a reusable, human-supervised accounting and finance agent that gathers context, performs work, and produces results people can inspect and approve. Add task-specific skills and tools as needed.

Start with a local foundation: persistent conversations, optional sandbox execution, file preservation, and human review. Real company policies and access are not configured.

**Boundaries:** no journal posting, payments, authoritative ERP changes, external communications, or editing original shared files. Approving a deliverable does not approve changes to reusable scripts, models, memory, skills, or permissions; those require separate approval.

## 2. Shared capabilities

These capabilities support the general objective. The functions in the last column explain which parts of the anatomy make each capability possible.

| ID | The agent should be able to… | Supporting functions |
|---|---|---|
| C1 | Understand the request using relevant inputs, instructions, skills, knowledge, and prior feedback. | [Context](#32-context), Core |
| C2 | Plan and carry out work through tools, code, and optional delegation. | [Core](#31-core), Actions, Context |
| C3 | Create and check deliverables, explain results, and report assumptions, exceptions, and limitations. | [Actions](#33-actions), Context, Controls |
| C4 | Preserve inputs, outputs, and conversation state so work can resume or be revised. | [Continuity](#35-continuity), Actions, Controls |
| C5 | Work within approved access and operating limits, and surface failures. | [Controls](#34-controls), Core |
| C6 | Make work reviewable: connect outputs to sources, checks, run records, and human decisions. | Continuity, Context, Controls |

A capability describes what the agent can do. A function describes the role of a part of the agent. A mechanism explains how that role works; an implementation names the code or service used here. Each capability can depend on several functions.

## 3. How the capabilities work

The tables connect familiar concepts to mechanisms from the [anatomy model](mental-model/01-anatomy.md). Implementation details here describe the current design; code presence alone does not establish reliability.

### 3.1 Core

**Role:** reason and drive the work — primarily C1, C2, and C5.

| Concept | Mechanism | Project implementation |
|---|---|---|
| Model | Model invocation | OpenAI chat model configured in `agent.py`; model, reasoning, and output limits are configurable. |
| Agent loop | Control loop, context assembly, output parsing | Deep Agents builds model input, interprets tool requests or a final answer, executes allowed requests, and returns results to the loop. |
| Stopping | Control loop and hooks | Stop on a final answer or an enforced limit. `RunControls` supplies shared model/tool budgets, deadline, timeouts, and bounded commands; model retries are configured. Some live enforcement remains unverified. |

### 3.2 Context

**Role:** supply what the model needs on each call — primarily C1, C2, C3, and C6.

| Concept | Mechanism | Project implementation |
|---|---|---|
| Request and instructions | Context assembly | Terminal prompt, thread inputs, system instructions, and `memory/AGENTS.md`. Asana gathering is planned in §4.2. |
| Conversation and tool results | State, context assembly | Harness assembles current history, tool definitions, and prior results; checkpoints restore thread state. |
| Plan / todos | Tool, state | `TodoListMiddleware` exposes `write_todos`. The model chooses when to use it; todo state persists with the conversation. |
| Skills | Hooks, tools, storage | `SkillsMiddleware` advertises skills; file tools read their `SKILL.md` through `/skills/`. CSV analysis, file-delivery validation, and provisional bank reconciliation exist. |
| Business knowledge and approved memory | Hooks, storage | `MemoryMiddleware` and `/memories/` provide owner-maintained guidance. The company profile is fictional. |
| Revision context | Storage, context assembly, tools | Same-thread history and prior files are available. Planned Asana intake adds review feedback and the relevant output version. |

Each model call receives freshly assembled input. Stored history, skills, and memory influence it only when their contents enter that input or a tool result.

### 3.3 Actions

**Role:** carry out model requests — primarily C2, C3, and C4.

| Concept | Mechanism | Project implementation |
|---|---|---|
| File operations | Tools, environment | Read, list, create, and revise files. Working paths use remote `/workspace` in sandbox mode and a thread virtual filesystem in default mode. |
| Code execution | Tool, environment | `execute` runs commands in a temporary LangSmith sandbox. The model client and agent loop stay on the host. Packages support file processing and calculations. |
| Reference access | Tools, routed storage | `/skills/` and `/memories/` are read-only host routes, not sandbox mounts. Read required content through file tools before copying it into sandbox code. |
| Delegation | Tool, another control loop | Harness sub-agents receive separate inputs and remain within configured runtime boundaries. |
| External systems / MCP | Tools, environment | Future controlled connectors may provide narrowly scoped, initially read-only access outside the sandbox. No ERP, SharePoint, Google Drive, or Asana connection is implemented. |

Task inputs are copied into the sandbox. New or changed eligible files are downloaded before cleanup; this is copy-in/copy-out transfer. Live mounts and continuous cloud sync are not implemented.

### 3.4 Controls

**Role:** decide what is allowed — primarily C3–C6.

| Concept | Mechanism / strength | Project rule and status |
|---|---|---|
| Task boundaries | Instructions | State scope and prohibitions. Instructions alone do not enforce them. |
| Approved references | Backend routing | Reject writes to `/skills/` and `/memories/`; the owner maintains them. |
| Operating limits | Runtime hooks | Enforce call budgets, deadlines, command/model/tool timeouts, and bounded retries. Live coverage remains incomplete; cost is not a hard monetary cap. |
| Sandbox isolation | Environment | Temporary execution with an owner-configurable network allowlist. Effective network isolation remains unverified. Local `.env` and API keys are not copied in. |
| Source protection | Transfer and storage | Use input copies; preserve local versions/conflicts and do not propagate remote deletions. These controls do not guarantee against every edit or data loss. |
| Output review | Human decision, review record | Approve/reject a successful run's unchanged file manifest. Asana review and mid-run approval interrupts are not implemented. |
| Asset promotion | Separate human approval | Reusable scripts, models, memory, skills, and permissions need separate approval. Proposal handling is not automated. |
| External writes | Access configuration | Posting, payments, original shared-file edits, and external communications are not enabled. Future access requires owner authorization and boundary tests. |

Evaluate controls at their actual strength: instruction, program check, human approval, or environment boundary.

### 3.5 Continuity

**Role:** keep what later calls and runs need — primarily C4 and C6.

| Concept | Mechanism | Project implementation |
|---|---|---|
| State within a run | State, context assembly | Harness carries messages, tool results, and todos into later calls. |
| Threads and resume | Checkpoint storage | SQLite saves graph state by thread ID. Terminal startup resumes the selected/last thread for that mode. |
| Working files | Storage, transfer | Local `workspace/threads/<thread-id>/` survives sandbox cleanup. Transfer preserves previous versions and conflicts. |
| Approved knowledge | Storage, controlled updates | Owner-maintained `memory/` and `skills/`; no automatic learning or silent promotion. |
| Provenance and review | Logs, traces, storage | Work log records outcomes, fingerprints, call/transfer events, validation, and review. Optional LangSmith tracing adds execution detail; neither captures every internal sandbox operation. |
| Configuration identity | Versioned records | Evaluation/release evidence must identify Git commit, lockfile, model settings, sandbox snapshot, and approved skills/memory. The CSV report does not yet capture the complete record. |

## 4. Applying the capabilities

### 4.1 Initial tasks

These tasks exercise the shared capabilities. They provide concrete evaluation cases without defining the permanent limits of the agent.

| Task | Specific objective | Capabilities / evaluation | Current status |
|---|---|---|---|
| CSV summary | Summarize supplied data into a reviewable output. | C1–C6; E-PLAT-1 | Starter cases drafted; planned evaluation pending. |
| Monthly bank reconciliation | Match bank and ledger items, explain exceptions, and produce supporting work. | C1–C6; E-FIN-1 | Provisional first finance workflow; procedure exists, known-answer fixtures and thresholds incomplete. |

For each later task, add its objective, required skill/tools/access, expected outputs, and evaluation cases. Keep detailed procedures in the skill or workflow document. A demonstration alone does not establish finance quality or release readiness.

### 4.2 Work lifecycle and interface

**Assign → gather context → execute → preserve outputs → review → approve or revise.** Work that cannot continue must surface its failure or missing input.

| Step | Current terminal prototype | Planned Asana workflow |
|---|---|---|
| Assign / gather | Prompt and files in a persistent thread. | Dispatcher gathers task fields, comments, attachments, trigger reason, changes, and prior feedback; one work item maps to one thread. |
| Execute / preserve | In sandbox mode: create sandbox, copy inputs, run tools, copy eligible new/changed files back, then clean up. | Same path, retaining outputs, supporting code, proposals, and failure details. |
| Return / review | Final response and local files; review record applies to the unchanged output manifest. | Publish status, summary, unresolved issues, and file links. Review occurs between runs. |
| Revise | Continue the same thread with feedback and prior files. | Actionable feedback starts a revision in the same task thread. Informational comments and agent status updates must not start duplicate runs. |

Planned Asana statuses: **To do → Agent working → Needs review → Done**, or **Blocked**. Eligibility, triggers, status representation, actionable feedback, and approval semantics remain open. Asana follows the foundation and finance release gates.

### 4.3 Output standard

Deliver the requested artifact, a concise summary, unresolved issues, and supporting code/provenance where useful. Financial work must state period, units/currency, sources, assumptions, calculations, tie-outs, exceptions, checks performed, and limitations. Approval covers the identified output version only.

## 5. Success criteria

These are the outcomes the capabilities must achieve. The evaluation IDs link each promise to its check in §6.1.

| ID | Capabilities / scope | Success means… | Evaluation |
|---|---|---|---|
| SC-1 | C1–C3; each released task | Results meet independent, task-specific acceptance checks on known-answer cases. | E-PLAT-1, E-FIN-1 |
| SC-2 | C4 | Source inputs stay unchanged; outputs survive cleanup and restart and remain associated with the correct run. | E-FILE-1 |
| SC-3 | C5, C6 | Permissions and limits hold; deliverables and reusable-asset/access changes receive their separate required approvals. | E-CTRL-1, E-PROV-1 |
| SC-4 | C3, C6 | Reviewers can inspect inputs, assumptions, exceptions, checks, and output/run/configuration provenance. | E-PROV-1 |
| SC-5 | All; release readiness | Required evaluations pass; owner, data policy, bounded access, stop/recovery, and monitoring are ready before hosted or expanded real-work use. | E-REL-1 |
| SC-6 | C1, C2, C4–C6; Asana | Intake, review, and revision preserve context/outputs through restart, without duplicate runs or trigger loops. | E-ASANA-1 |

Example: **C4 preserve work → Continuity + Actions + Controls → checkpoint/transfer mechanisms → SC-2 → E-FILE-1 → monitor missing files and resume failures.**

## 6. Evaluation, release, and improvement

The [ADLC](mental-model/02-adlc.md) is **Build (Plan, Configure) → Test → Deploy → Monitor → back to Build**. Define all three plans during Plan, implement checks during Configure, then collect evidence in Test and Monitor.

### 6.1 Evaluation plan

For every check, record the four dimensions below. Cases (normal, edge, adversarial) and pass thresholds are additional fields.

| Evaluation | What is checked | Who grades | When | Why |
|---|---|---|---|---|
| E-PLAT-1 | Output, trajectory, steps | Code | Offline | Capability; regression after acceptance |
| E-FILE-1 | Files, transfer steps, resume trajectory | Code | Offline; preservation checks also online | Capability and regression |
| E-FIN-1 | Financial outputs and procedure | Code + human finance reviewer | Offline; applicable tie-outs/review also online | Capability; regression after acceptance |
| E-CTRL-1 | Requests, boundary steps, run limits | Code + human access review | Offline; limit/boundary signals also online | Capability and regression |
| E-PROV-1 | Output evidence and run trajectory | Code + human reviewer | Offline and online | Capability and regression |
| E-REL-1 | Configuration and readiness evidence | Owner | Offline, before each release/stage | Capability and regression readiness |
| E-ASANA-1 | Full task trajectory and integration steps | Code + human reviewer | Offline; lifecycle signals later online | Capability; regression after acceptance |

Offline means controlled evaluation; online means checking live work. Online checks are planned unless their implementation is recorded. Use code when answers are known; an LLM judge may assess subjective criteria only after calibration against human judgments. Retain human review for consequential finance judgments and presentation.

| Evaluation | Mechanisms and cases | Pass condition | Status |
|---|---|---|---|
| E-PLAT-1 | Loop/limits, context/skills, file tools, execution. Two CSV cases: exact expected JSON, source bytes, calls/time. | Both cases complete normally within limits, match expected outputs, and preserve sources. Repeat to assess reliability. | Drafted; planned suite not run. Earlier smoke tasks are separate evidence. |
| E-FILE-1 | Transfer, hashes/versions/conflicts, checkpoints. Text, XLSX, binary, restart, and concurrent local edits. | Preservation/conflict rules pass; files survive cleanup and thread resumes. | Transfer check passed; broad restart/recovery evaluation incomplete. |
| E-FIN-1 | Skill, calculations, artifact generation/validation. Synthetic bank/ledger cases: matches, exceptions, balance bridges, proposed entries, source preservation, Excel/Word outputs. | Every defined critical check passes; human accepts representative output. | Fixtures/thresholds incomplete; evaluation not run. |
| E-CTRL-1 | Runtime hooks, reference routes, sandbox/network, external identity. Call/time limits, unauthorized writes, adversarial inputs, network/secret checks. | Limits stop runs; forbidden requests are blocked at the required layer; effective egress enforcement is verified. | Offline engineering checks passed; live enforcement/production identity unverified. |
| E-PROV-1 | Trace, work log, manifest, validation and configuration records. Follow input fingerprints through tool actions, artifacts, checks, and review. | Required evidence is present; approval identifies the unchanged output version and scope. | Local records/tracing exist; complete release provenance pending. |
| E-REL-1 | Release checklist, access, limits, configuration, stop/rollback, monitoring. Owner reviews evidence and recovery rehearsal. | All required readiness items confirmed; unresolved risks recorded. | Pending. |
| E-ASANA-1 | Dispatcher, connector, task/thread map, locking, persistence. Normal tasks, feedback, duplicates, failure/Blocked, restart/recovery. | Five consecutive tasks complete the path; no duplicate/loop runs; context and outputs survive restart. | Future integration. |

**Coverage:** every capability, success criterion, anatomy function, and run stage needs a check. Expand these evaluation groups into individual cases with expected results, grader, threshold, and configuration ID. A trace records behavior; correctness requires independent checks. Reliably passing capability cases join the regression set.

### 6.2 Release plan

Current stage: local prototype. Hosted deployment is not implemented. Use synthetic data or specifically approved tasks with human review until release gates pass.

| Stage | Use | Gate to advance |
|---|---|---|
| 0. Local evaluation | Engineering checks and synthetic examples; no business actions. | Planned checks pass, limitations recorded, configuration identified. |
| 1. Parallel run | Approved real tasks alongside the normal process; outputs are not authoritative. | Agreement on a defined representative sample; discrepancies understood. |
| 2. Supervised use | Human reviews every deliverable before use; no posting/payments. | Agreed thresholds met over a defined sample/period; stop and recovery exercised. |
| 3. Expanded use | Consider review frequency based on risk and evidence. | Owner approval, monitoring thresholds, access review, rollback readiness. |

Deployment decisions required before release:

| Area | Current arrangement | Required decision / evidence |
|---|---|---|
| Runtime | Host terminal/model client/agent loop; optional LangSmith tracing. | Hosted runtime/dispatcher; model/provider policy; trace access and retention. |
| Execution | Temporary LangSmith sandbox selected by immutable snapshot ID. | Verified network restrictions, resource ceilings, recovery; workbook recalculation where required. |
| Storage | Local SQLite and thread folders. | Durable hosted storage, backup, retention, restore. |
| Access and ownership | No real business-system integration. | Operational owner, data policy, named identities, least privilege; tests for any new connector. |
| Limits and readiness | Runtime controls and local review. | Recorded evaluation gate, exact configuration, model/tool/time limits, cost policy and revision limits; preservation/failure/recovery rehearsal. |

Document how to stop new work, handle active runs, disable triggers, and restore the last known-good configuration. Flag affected outputs for re-review; review any memory changes associated with the faulty release.

Gaps: no dispatcher stop control or distributed exactly-once guarantee; snapshot rollback has not been exercised live; egress enforcement remains unverified. Resolve these before automated Asana rollout.

### 6.3 Monitoring plan

Monitor the same promises evaluated before release. Define owners, cadence, and thresholds before a hosted pilot.

| Function / criteria | Signals | Source / gap |
|---|---|---|
| Core — SC-1, SC-3 | Completion/errors, time, model/tool calls, usage/cost. | LangSmith and local records; production thresholds unset. |
| Context — SC-1, SC-4 | Wrong skill/context, unsupported assumptions, missing-input questions, repeated misunderstandings. | Trace and review; systematic labels pending. |
| Actions — SC-1, SC-2 | Tool failures, transfer conflicts, artifact/tie-out failures, corrections. | Tool/transfer records and validation; finance checks incomplete. |
| Controls — SC-3, SC-5 | Limit hits, refusals, boundary attempts, unauthorized actions. | Runtime/sandbox records; effective egress unverified. |
| Continuity — SC-2, SC-4, SC-6 | Resume failures, missing/stale files, lost feedback, stale approvals. | Checkpoints, manifests, work log; service recovery pending. |
| Overall — SC-1, SC-5, SC-6 | Approval/rejection, revision rounds, discrepancies, repeat failures, drift by task/configuration. | Local review/work log; operational ownership/thresholds pending. |

- **Every run:** retain configuration/run ID, status, limits, tool/transfer events, check results, and review outcome. Perform applicable deterministic tie-outs and integrity checks before delivery.
- **Human review:** review every output during early supervised use. Reduce sampling only with defined risk thresholds and supporting evidence.
- **Trend review:** examine errors, corrections, approvals, revisions, and cost at the agreed cadence.

### 6.4 Respond and improve

| Finding | Response |
|---|---|
| Boundary breach, data loss, material incorrect result | Stop, investigate, and apply the rollback/re-review plan. |
| Repeated failure | Trace it to a capability, function, and mechanism; add a regression case; fix through Build and Test before release. |
| Accepted one-off issue | Record the decision and workaround; continue monitoring. |

For a new skill, add its task objective, procedure, and capability cases, then run existing regressions. Changes to tools/access also need boundary checks; changes to knowledge/instructions need affected regressions; model changes require the full evaluation set. A changed role/objective requires revisiting all three plans and rollout gates.

Memory remains owner-maintained. Monitoring cannot silently change approved memory, skills, or permissions. Before adding automatic learning, define memory ownership, scope, approval, retention/deletion, and compatibility checks when configurations change.

## 7. Open decisions

| Decision | Resolve before |
|---|---|
| Bank-reconciliation scope, known-answer fixtures, critical thresholds, workbook recalculation | Finance evaluation/release |
| Stage thresholds, cost ceilings, call/time/revision limits, review cadence and operational owner | Hosted pilot |
| Host, service identity, durable storage, retention/restore, data policy | Real-company data or hosted use |
| Effective filesystem/network restrictions and connector access boundaries | Expanded access |
| Asana eligibility/triggers/statuses, actionable feedback, output-version approval, locking and duplicate/loop prevention | Asana implementation/release |

Keep one agent as the foundation. Evaluate the foundation and first finance workflow, then implement and verify Asana before expanding automation or memory infrastructure. Detailed work and evidence belong in the [task list](task-list.md) and [README](../README.md).

## 8. Change log

| Version | Date | Change |
|---|---|---|
| v0.7 | 2026-10-23 | Added shared capability IDs and explicit links to functions, mechanisms, criteria, evaluations, and monitoring. Moved initial tasks after the design; shortened repeated text; made all four evaluation dimensions explicit. |
| v0.6 | 2026-10-22 | Separated the general agent objective from initial task objectives; placed capabilities before success criteria and moved the work interface after them. |
| v0.5 | 2026-10-22 | Reorganized around anatomy functions and mechanisms; connected success criteria to evals and added links to the mental models, architecture, and project task list. Preserved current prototype scope and release gaps. |
| v0.4 | 2026-10-21 | Previous structure retained in Git history; v0.5 reorganizes its project decisions around the anatomy and ADLC. |
