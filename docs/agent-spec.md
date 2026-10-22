# Finance & Accounting Agent — Agent Specification

**Version:** v0.4 working draft

**Owner:** Neil Yee

**Document date:** October 21, 2026

**Status:** Project plan and proposed design; implementation status is tracked in the README.

**Initial scope:** Platform foundation plus one initial finance skill.

See the [architecture diagram](architecture.md) for components, execution locations, storage, and approval boundaries.

## 1. Goal and design direction

Build a general finance and accounting agent that accepts work through Asana, uses sandboxed code execution to perform it, and returns outputs that people can inspect and approve.

The foundation should support different finance and accounting tasks through relevant context, skills, general execution capabilities, and controlled access to external systems. The first demonstrated task is an initial capability, not the permanent scope of the agent.

Design principles:

- Use Asana as the main work interface for assignment, context, review, and feedback.
- Start with one agent. Multiple role-specific agents may be considered later.
- Run the dispatcher and agent loop outside the execution sandbox.
- Use general code execution and file capabilities rather than a separate business tool function for every calculation or workflow.
- Use skills for task-specific procedures.
- Produce human-readable artifacts as well as supporting code.
- Require separate human approval before promoting reusable scripts, models, memory, or skill changes.

Evaluate the local agent foundation first, then evaluate the provisional bank-reconciliation skill using synthetic cases with independently known results. Add Asana after the foundation and first finance workflow are ready. Asana remains the intended eventual work interface, not the first implementation milestone.

## 2. Work intake and statuses

The initial work statuses are:

**To do → Agent working → Needs review → Done**, with **Blocked** for work that cannot continue.

| Event | Intended behavior |
| --- | --- |
| An eligible task is assigned to the agent | Gather context and start work. |
| A human provides actionable feedback on a task in Needs review | Start a revision using the same task thread. |
| A reviewer moves the task to Done | Approve the current output version. |
| The agent or dispatcher publishes a status update | Do not trigger another run. |
| Work fails or required inputs are missing | Set a clear Blocked state and explain what is needed. |

In the initial version, review happens between runs rather than through a mid-run interrupt. Work stays in Needs review until approval or actionable feedback arrives.

The exact eligibility rule, trigger mechanism, status representation in Asana, and definition of actionable feedback remain open. An informational comment should not automatically cause a revision.

## 3. Context and inputs

The dispatcher gathers the context needed for a task:

- Task title, description, relevant fields, comments, and attachments.
- What changed and why the agent was triggered.
- Relevant business knowledge and skills.
- Approved memory notes and reusable scripts or models.
- Previous outputs when revising the same task.

Copy task inputs and approved assets into the sandbox. Do not modify original working files.

Phase 2 may add read-only SQL Server or SYSPRO access through a controlled connector or MCP server. This access is outside the initial platform scope.

## 4. Execution capabilities

The execution environment should provide:

- General code execution in the sandbox.
- File reading, listing, and writing within the sandbox.
- Packages such as pandas, openpyxl, and pdfplumber, according to the task's needs.
- A workbook recalculation method where Excel formulas require it.
- External-system access through separately controlled connectors.

The agent may draft reusable scripts, calculation tools, and financial models. A person reviews and approves versions before they become reusable assets.

The security target is to keep external-system credentials outside the sandbox and restrict network and filesystem access through environment controls. These are implementation requirements to establish and verify, not guarantees provided by this specification.

## 5. Initial supported work

**Platform test:** Summarize an attached CSV and produce a reviewable output.

**First real finance skill:** Bank reconciliation is the current candidate. Select representative inputs and define expected results before implementing and testing the skill.

## 6. Approvals and operating limits

| Item | Required approval |
| --- | --- |
| Work output | A reviewer approves the current output version. |
| New reusable script or model | Separate review before promotion to the approved library. |
| Memory proposal | Explicit review before retention. |
| Skill revision | Owner approval before use as an approved version. |
| Permissions or external access | An owner-controlled change. |

Approval of a task output must not automatically approve memory, scripts, models, skills, or permission changes.

Set limits for execution duration, model calls, cost, and revision rounds. The values and enforcement mechanisms remain undecided.

## 7. Outputs and preservation

Each completed run should produce:

- A human-readable artifact appropriate to the request.
- A short Asana summary with output links and unresolved issues.
- Supporting code and provenance.

For financial workbooks, include the following where relevant:

- Summary, inputs, and assumptions.
- Traceable calculations.
- Source tie-outs and checks.
- Exceptions and explanations.
- Input and tool versions.

Use Excel formulas where useful for review or editing. Python-derived results are also acceptable when their logic and evidence are documented.

Copy outputs, supporting code, and proposals to persistent storage before removing the sandbox. Preserve output versions so a reviewer can distinguish an initial result from a revision.

## 8. Boundaries

The initial version excludes:

- Posting journal entries or initiating payments.
- Changing authoritative ERP records.
- Sending external communications.
- Editing original shared files.
- Promoting scripts, models, memory, or skill changes without approval.

The dispatcher performs the controlled Asana updates needed to publish status, summaries, and output links.

## 9. Evaluation plan

The evaluation, release, and monitoring plans below apply to the whole configured agent. A passing engineering check or one successful run is evidence for a specific behavior; it is not by itself a release decision.

### Foundation evaluation

- Run the network-blocked engineering suite on each supported host environment before relying on platform behavior there.
- Run the two starter CSV cases as an explicitly authorized live baseline. Each case must complete normally, produce the exact expected JSON, and preserve the source bytes.
- Treat this two-case, one-run-per-case baseline as a smoke evaluation. It does not establish repeatability, financial accuracy, or general file-handling ability.
- Keep deterministic checks for exact facts and file integrity. Use human review for financial judgment and visual document quality. An LLM judge may assist with subjective criteria only after comparison against human judgments.
- Record results against the configuration that produced them. At minimum, release evidence should identify the Git commit, dependency lock, model settings, sandbox snapshot, and approved skill/memory versions. The current CSV report does not yet capture this complete configuration record.

### First finance workflow

- Define synthetic bank and ledger fixtures, expected matching/reconciling results, and acceptance criteria before running the skill.
- Check row coverage, balance tie-outs, matching and exception decisions, proposed entries, source preservation, and all output artifacts.
- Independently recalculate workbook results and review rendered Excel and Word deliverables. Structural file checks alone are insufficient.
- Require human review of the representative result before making a finance-quality claim.

### Eventual Asana workflow

- Five consecutive test tasks complete the intake, execution, output, review, and revision path.
- Duplicate updates do not cause duplicate work.
- Agent-generated updates do not create trigger loops.
- Failures produce a clear Blocked state.
- Outputs survive sandbox cleanup.
- Task context and preserved outputs survive a host restart.

Before adopting any release gate, define the cases, grader, pass threshold, and required human checks for that release. A new capability needs capability cases; changes to existing behavior also need regression cases. Repeat runs are needed when making a reliability claim.

## 10. Release plan

No hosted service or production deployment is currently implemented. Until a release plan passes its readiness checks, use the system as a local prototype with synthetic data or specifically approved tasks and human review.

### Rollout stages

| Stage | Use | Gate to advance |
| --- | --- | --- |
| **0. Local evaluation** | Engineering checks, synthetic datasets, and reviewed examples; outputs do not drive business actions. | Planned evaluation criteria pass, known limitations are recorded, and configuration provenance is available. |
| **1. Parallel run** | For approved real tasks, run alongside the normal process; the agent output is not authoritative. | Outputs agree with the normal process on a defined representative sample; failures and discrepancies are understood. |
| **2. Supervised use** | Outputs may support work, with a person reviewing every deliverable before use. No posting or payment actions. | A defined period and sample meet agreed acceptance thresholds; stop and recovery procedures have been exercised. |
| **3. Expanded use** | Consider risk-based review only after evidence supports it and controls remain effective. | Owner approval, monitoring thresholds, access review, and rollback readiness are confirmed. |

### Readiness, stop, and rollback

Before any hosted or real-work release, name an owner; confirm permitted data handling and least-privilege identities; identify the exact agent configuration and sandbox release; pass the release gate; set model/tool/time and cost limits; and test output preservation, failure handling, and recovery.

The release record must say how to stop new work, handle in-flight runs, disable external triggers, and return to the last known-good configuration. Outputs created by a faulty release must be identified for re-review. The current local runner has no dispatcher-level stop control or distributed exactly-once guarantee; these must be addressed and verified before an automated Asana rollout.

Deployment and rollback of sandbox snapshots are supported by tooling, but rollback has not been exercised live. A configured egress allowlist is not proof of enforced network isolation. These are release readiness items, not established guarantees.

## 11. Monitoring plan

Monitoring asks whether the deployed configuration continues to work and identifies which anatomy function or lever needs attention. Current tracing and the local work log provide partial evidence; production monitoring, thresholds, review cadence, and assigned operational ownership are not implemented.

### Signals

| Function | Signals to review |
| --- | --- |
| **Core** | Completion/error rate, elapsed time, model and tool calls, and usage/cost where available. |
| **Context** | Whether the right skill and business context were used; unsupported assumptions, missing-input questions, and repeated misunderstandings. |
| **Actions** | Tool failures, transfer conflicts, artifact checks, calculation tie-outs, and corrections made during review. |
| **Controls** | Limit hits, refused requests, attempted boundary violations, and any unauthorized external action. |
| **Continuity** | Resume failures, missing or stale files, revision rounds, and review state becoming stale after file changes. |
| **Overall** | Approval/rejection rates, unresolved discrepancies, repeated failures, and drift by task type and configuration. |

### Review tiers and response

- **Every run:** retain run/configuration identity, status, limits, tool and transfer events, output checks, and review outcome. Run applicable deterministic tie-outs and integrity checks before presenting outputs.
- **Human review:** review every output during early supervised use. Reduce the sample only after volume and risk-based thresholds are defined and evidence supports the change.
- **Trend review:** periodically examine errors, corrections, approvals/rejections, revisions, and operating cost. Set the cadence and thresholds before a hosted pilot.

Stop and investigate a boundary breach, data loss, or material incorrect result. Fix repeated failures by tracing them to a function or lever, updating the configuration, and adding a regression case. Record an accepted one-off issue and its workaround. Monitoring findings feed the next Build/Test cycle; they do not silently change approved memory, skills, or permissions.

## 12. Current implementation and future deployment choices

| Component | Current prototype | Future deployment decision |
| --- | --- | --- |
| Agent interface and host | Local terminal application. | Where the long-running dispatcher and agent process will run. |
| Model and tracing | OpenAI model; optional LangSmith tracing. | Model/version, provider policy, trace retention, and approved data handling for the deployed service. |
| Code execution | Temporary LangSmith sandbox selected by immutable snapshot ID. | Production sandbox policy, enforceable egress, resource ceilings, and recovery expectations. |
| Checkpoint and workspace | Local SQLite checkpoints and per-thread local folders. | Durable hosted storage, backup, retention, and restore procedures. |
| Work interface | Terminal; Asana is intended but not integrated. | Asana intake, status, review, revision, and duplicate/loop prevention. |
| External business systems | No ERP access. | Phase 2 may add read-only connectors; posting and payments remain excluded. |

The eventual Asana workflow maps one task to one conversation/thread so revisions can restore its context. This mapping is a design goal; it is not implemented in the local prototype.

The planned Asana-enabled run lifecycle is:

1. Gather task context and relevant changes.
2. Create a sandbox and prepare the task workspace.
3. Copy inputs and approved assets into the sandbox.
4. Execute the task.
5. Preserve outputs, supporting code, proposals, and failure details.
6. Clean up the sandbox.
7. Publish the resulting status, summary, and output links through the dispatcher.

The local user can exit the terminal to prevent new runs. A future dispatcher must have a tested stop procedure that prevents new dispatches and defines how in-flight runs are handled; that control is not currently implemented.

## 13. Shared-file awareness and provenance

- Optional LangSmith tracing is implemented; production retention and access policies remain to be decided.
- Record input and output fingerprints, run IDs, and approved asset versions.
- Detect changed inputs before revising or publishing results.
- Treat a changed file as a reason to reassess, rather than automatically as an authoritative correction.
- Turn observed failures into regression cases.
- Record files copied into and out of the sandbox in a transfer log.

The transfer log is not automatically a complete record of every file operation inside the sandbox.

Confirm permitted data handling before using company information with external services.

## 14. Knowledge, learning, and reusable assets

| Type | Policy |
| --- | --- |
| Business knowledge | Human-maintained reference context; read-only to the agent. |
| Agent memory | Proposed lessons retained after explicit review. |
| Work log | Program-generated factual records of inputs, runs, transfers, and versions. |
| Reusable scripts and models | Agent drafts with tests; human approves versions. |
| Skills | Agent may propose revisions; owner approves changes. |

Keep pending proposals separate from approved assets. Output approval and asset approval are separate decisions.

Shared business knowledge may serve multiple agents later. Learnings may be shared or role-specific according to relevance and access permissions.

## 15. Open decisions

Resolve these before the corresponding integration or release stage:

- Asana eligibility rules and how statuses are represented.
- Which comments count as actionable feedback and how approval identifies an output version.
- Trigger mechanism, task locking, duplicate prevention, and prevention of agent-generated trigger loops.
- Deployment host, service identity, durable workspace/checkpoint storage, and recovery procedures.
- How to enforce and verify filesystem/network restrictions under the selected sandbox and provider policy.
- Cost ceiling, execution/model-call limits, and revision limits for each release stage.
- Release-gate thresholds, human-review sample/cadence after the supervised stage, and monitoring owners.
- Workbook recalculation method when required by the first finance skill.
- Bank-reconciliation acceptance criteria and independently known evaluation fixtures.

Keep the implementation focused on one agent. Evaluate the foundation and first finance workflow before adding Asana, then verify the complete task-to-review path before adding more capabilities or elaborate memory infrastructure.
