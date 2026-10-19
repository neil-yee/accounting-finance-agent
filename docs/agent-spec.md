# Finance & Accounting Agent — Agent Specification

**Version:** v0.3 working draft  
**Owner:** Neil Yee  
**Document date:** October 15, 2026  
**Status:** Proposed design; this document does not describe an implemented system.  
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

Build a walking skeleton first: one small task moves from Asana, through the agent and sandbox, and back to Asana for review and revision. Add the first real finance skill after that path works.

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

## 9. Success criteria

### Platform

- Five consecutive test tasks complete the intake, execution, output, review, and revision path.
- Duplicate updates do not cause duplicate work.
- Agent-generated updates do not create trigger loops.
- Failures produce a clear Blocked state.
- Outputs survive sandbox cleanup.
- Task context and preserved outputs survive a host restart.

### First finance skill

- Expected results and acceptance criteria are defined before testing.
- Critical financial checks and permission boundaries pass.
- One representative real request is completed with human approval.

## 10. Deployment and persistence

| Component | Proposed location or choice |
| --- | --- |
| Dispatcher and agent loop | Local host initially. |
| External connectors or MCP clients | Outside the execution sandbox. |
| Code execution | Hosted sandbox or restricted local container; choice open. |
| Checkpointer | Persistent storage; SQLite is the initial candidate. |
| Workspace and output storage | Local folder or SharePoint; choice open. |
| Model provider and model | Undecided. |

Use one Asana task as the initial conversation/thread scope. Subsequent revisions restore that task's context.

The run lifecycle is:

1. Gather task context and relevant changes.
2. Create a sandbox and prepare the task workspace.
3. Copy inputs and approved assets into the sandbox.
4. Execute the task.
5. Preserve outputs, supporting code, proposals, and failure details.
6. Clean up the sandbox.
7. Publish the resulting status, summary, and output links through the dispatcher.

Stopping the dispatcher prevents new dispatches. Cancellation of work already running requires a separate mechanism.

## 11. Monitoring and shared-file awareness

- Trace runs through the chosen tracing platform; LangSmith is the current candidate.
- Record input and output fingerprints, run IDs, and approved asset versions.
- Detect changed inputs before revising or publishing results.
- Treat a changed file as a reason to reassess, rather than automatically as an authoritative correction.
- Turn observed failures into regression cases.
- Record files copied into and out of the sandbox in a transfer log.

The transfer log is not automatically a complete record of every file operation inside the sandbox.

Confirm permitted data handling before using company information with external services.

## 12. Knowledge, learning, and reusable assets

| Type | Policy |
| --- | --- |
| Business knowledge | Human-maintained reference context; read-only to the agent. |
| Agent memory | Proposed lessons retained after explicit review. |
| Work log | Program-generated factual records of inputs, runs, transfers, and versions. |
| Reusable scripts and models | Agent drafts with tests; human approves versions. |
| Skills | Agent may propose revisions; owner approves changes. |

Keep pending proposals separate from approved assets. Output approval and asset approval are separate decisions.

Shared business knowledge may serve multiple agents later. Learnings may be shared or role-specific according to relevance and access permissions.

## Open decisions

Resolve these as the walking skeleton is built:

- Asana eligibility rules and how statuses are represented.
- Which comments count as actionable feedback and how approval identifies an output version.
- Trigger mechanism, task locking, and duplicate prevention.
- Sandbox provider and enforceable filesystem/network restrictions.
- Persistent workspace location and file-transfer approach.
- Model provider, model, and tracing platform.
- Execution, model-call, cost, and revision limits.
- Workbook recalculation method when required by the first finance skill.
- Final selection of the first finance skill and its acceptance criteria.

Keep the implementation focused on one agent and the complete task-to-review path before adding more capabilities or elaborate memory infrastructure.
