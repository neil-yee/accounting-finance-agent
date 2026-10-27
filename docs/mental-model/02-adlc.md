# Agent Mental Model: 02 ADLC

**Purpose:** turn an agent's intended capabilities into a system with evidence for its use, then improve it as requirements and conditions change.

**Version:** v0.6 working reference · **Owner:** Neil Yee · **Updated:** October 24, 2026

## 1. Why a lifecycle is needed

Behavior depends on **configuration + task/input + retained state + external conditions**. Model variation adds uncertainty. Testing provides evidence for a defined scope; passing examples does not guarantee every future result. Some program properties can be checked deterministically, while task quality needs representative evaluation.

The lifecycle manages that uncertainty:

**Build (Plan, Configure) → Test → Deploy → Monitor → back to Build.**

| Activity | Main question | Output / condition to proceed |
|---|---|---|
| **Plan** | What should it do, how will it work, and what evidence will justify use? | Specification and design document covering all four phases, plus a linked task list. Unknowns are explicit. |
| **Configure** | Can we implement the intended behavior and checks? | Code/configuration, skills/tools, cases/graders, instrumentation, and a working path through a representative task. |
| **Test** | Does this version meet the criteria for its intended scope? | Results, failure analysis, and a release decision tied to the evaluated configuration and cases. |
| **Deploy** | Where and under what authority may it operate? | Readiness record, approved scope, rollout stage, and stop/recovery procedures. |
| **Monitor** | Does it continue to meet expectations, and what needs action? | Signals, review findings, incident responses, and changes or new evaluation cases. |

Plan and Configure are parts of Build in this model. The phases overlap and repeat: prototypes inform plans, checks are built alongside features, and monitoring is prepared before deployment. People remain accountable even when agents help implement or evaluate changes.

## 2. Plan from purpose to evidence

Start with the objective and boundaries, then shared capabilities. Map capabilities to the [anatomy](01-anatomy.md): functions, mechanisms, and proposed implementation. Define observable success criteria, then how to evaluate, release, and monitor them. Iterate when a criterion exposes a missing design decision.

Separate shared capabilities from task applications. “Handle spreadsheets” is a capability to make precise; “reconcile this bank statement” is a task objective; a Python library is an implementation choice. General capabilities still need representative tasks to demonstrate them.

### 2.1 Minimum working artifacts

Use a combined **specification and design document** as the default planning artifact. It contains architecture views and evaluation, release and monitoring plans. Requirements state what must be true; design explains the proposed mechanisms, components and methods for achieving it.

The document can contain sections, tables and diagrams. Separate files are useful when ownership or detail warrants them; the distinctions below do not require separate documents.

| Artifact | Minimum contents | Used for |
|---|---|---|
| **Specification and design** | Purpose/scope; capabilities and required behavior; functions, mechanisms and proposed implementation; architecture views; success criteria; evaluation, deployment and monitoring requirements/plans; open decisions. | Agreeing what to build, how it should work and what evidence will justify use. |
| **Task list** | Work items linked to capabilities, design and checks; dependencies, owner, status and completion evidence. | Building, verifying and tracking the implementation. |
| **Cases and graders** | Inputs/setup, expected results or rubric, grader, thresholds, and reset/cleanup needs. | Repeatable evaluation. |
| **Evaluation record** | Configuration and case/grader versions, results, repetitions/sample size, failures, and limitations. | Accepting or rejecting a release candidate. |
| **Release record** | Approved version/scope/stage, readiness evidence, owner, and stop/recovery instructions. | Operating and recovering the system. |
| **Finding / change record** | Evidence, impact, diagnosis, response, and linked corrective work or accepted limitation. | Closing the improvement loop. |

**Organize the combined document around the lifecycle**

Start with purpose and scope. Within each phase, distinguish requirements from proposed design:

| Phase | Requirements: what must be true | Design: how to achieve or check it |
|---|---|---|
| **Build** | Capabilities, boundaries, assignment behavior and expected deliverables. | Functions, mechanisms, implementation choices, architecture and shared building blocks. |
| **Test** | Success criteria, required coverage and acceptance thresholds. | Cases, datasets, graders, trial setup and evidence collection. |
| **Deploy** | Release conditions, permitted use, ownership and recovery expectations. | Execution locations, storage, credentials, rollout and recovery procedures. |
| **Monitor and improve** | Operating expectations, required review and conditions for intervention. | Signals, thresholds, alerts, response procedures and how findings become changes. |

Plan all four phases before relying on the agent. Organizing the document by phase does not mean postponing evaluation or monitoring design until those phases begin.

**Place architecture where it explains the design**

- **Build:** show how the agent's components connect and how an assignment executes, including failure paths.
- **Test and operation:** show how a version, cases and graders produce evidence for release, and how live findings feed back into changes.
- **Deploy:** show execution locations, data flows, persistent storage, identities and trust boundaries.

Keep these as complementary views. A lifecycle arrow explains the process; an architecture view identifies the components, evidence and connections that support it.

Place an **implementation inventory** after the Build architecture when useful. Group the intended shared components, map them to capabilities, and link to the corresponding task-list items. Keep implementation status, findings and evidence in the task list so each assessment has one maintained source. Code/configuration is the actual implementation; inventory entries do not establish that it exists or works.

The three plans inside the document answer distinct questions:

- **Evaluation plan:** what to check, on which cases, by whom, with what pass criteria?
- **Release plan:** where and with which access, at what rollout stage, and how to stop or recover?
- **Monitoring plan:** which signals, thresholds, owners, and response procedures during use?

### 2.2 Traceability across requirements, design and evidence

Give capabilities, criteria, and evaluation cases stable IDs. Connect requirements to design, implementation work, results and monitoring. Link detailed descriptions rather than copying them into every table. One criterion can need several checks; one check can support several criteria.

| Criterion | Design dependency | Evaluation evidence | Release condition | Live signal / response |
|---|---|---|---|---|
| Preserve work through restart | Continuity + Actions: checkpoints, files, transfer | Interrupt/resume cases compare state and files | Required recovery cases pass | Missing output or failed resume → investigate/recover |
| Write only to approved destinations | Controls + Actions: authorization and destination checks | Allowed, denied, and adversarial requests | No forbidden write in the required cases; access reviewed | Unauthorized write → stop and investigate |

Use these links to find missing design, checks, or operating responses. Coverage alone does not establish that the checks are strong enough.

Record the configuration needed to interpret results: code/dependencies, model/provider/version and settings, instructions, skills/tools, access policy, environment, and storage schema. Record relevant input, retrieval, and memory versions or snapshots separately. Version identifiers support comparison; external services and model variation can still prevent exact reproduction.

## 3. Evals

An evaluation compares observed behavior or results with a stated criterion. Tracing supplies observations; a grader applies the criterion. Engineering tests check components; task evaluations check whether the configured agent accomplishes useful work. Both contribute evidence.

### 3.1 Design each check

1. Start from success criteria and important failure modes. Include final outcomes, required behavior, and boundaries.
2. Walk the anatomy and the full work path: intake, context, action, preservation, review, revision, failure, and recovery. Choose cases at consequential boundaries.
3. Define inputs/setup, expected answer or rubric, grading method, pass threshold, and allowed cost/time. Classify the check using the four dimensions below.
4. Choose normal, edge, and adversarial cases where relevant. Use representative real examples, synthetic known-answer cases, or reviewed incidents; keep evaluation data separate from development examples where practical.
5. Run enough cases and repetitions for the claim being made. Record sample size, variation, and limitations; a single success establishes only that trial's result.

### 3.2 Four dimensions of an eval

| Dimension | Options | Question |
|---|---|---|
| **What is checked** | Final output, trajectory (observable sequence), individual step | Is the result acceptable, was required behavior followed, or did one operation work? |
| **Who grades** | Code, LLM judge, person; combinations allowed | How is the criterion judged? |
| **When / setting** | Offline (controlled cases), online (live operation) | Is this a controlled evaluation or a check on real use? |
| **Why** | Capability, regression, or both | Does it establish ability, detect loss of previously acceptable behavior, or both? |

The dimensions are independent. For example, an arithmetic check can use code to grade final outputs offline for a new capability, then become a regression check and an online validation.

Offline evaluation can run before or after release and can use a rubric instead of an exact answer. Online checks can use known outcomes, invariants, or human review. The same check may serve both settings; live monitoring also includes operational signals such as latency and outages.

Use deterministic code for exact answers and invariants. Use humans for judgment and representative presentation review; an LLM judge can help with subjective criteria when calibrated against human ratings and checked for bias or drift. Check the graders themselves.

### 3.3 What good coverage includes

| Area | Evidence to seek |
|---|---|
| **Task quality** | Independent expected results or a clear rubric; relevant sources, calculations, and usable artifacts. |
| **Context** | Correct sources/skills, handling of missing or conflicting information, and appropriate clarification. |
| **Actions** | Valid tool inputs, correct effects, appropriate output locations, and agreement across related deliverables. |
| **Controls** | Limits and permissions hold; adversarial inputs do not cause forbidden effects. |
| **Continuity / integration** | State/files survive required interruptions; revision uses feedback; retries do not duplicate external actions. |
| **Reliability and efficiency** | Acceptable outcomes across cases/repetitions, within latency, call, token, and cost budgets. |

Consistency means acceptable results within defined tolerances, not necessarily identical words or tool sequences. Grade a specific trajectory only when that behavior is required. File integrity alone does not establish content accuracy; a spreadsheet may open correctly while using the wrong formula or disagreeing with its report.

### 3.4 Release gate

Agree thresholds before assessing the release candidate. Identify mandatory conditions, tolerances, acceptable failure rates, and human review requirements. Do not average away a critical boundary failure with many easy passes.

Record case/grader versions, configuration, results, and unresolved limits. Reliably passing capability cases become part of the regression set. A passing gate authorizes only the evaluated scope and rollout stage.

## 4. Deployment and recovery

Deployment makes a version available for intended use; it need not mean cloud hosting. Define environment, identity/access, data handling, operational owner, limits, and monitoring before exposure to real work.

Choose a rollout proportionate to consequences. A common sequence is:

| Stage | Use | Evidence to expand |
|---|---|---|
| **Controlled trial** | Synthetic or approved cases with restricted access. | Evaluation gate and readiness checks pass. |
| **Parallel / shadow operation** | Compare with the normal process; suppress consequential external writes and keep outputs non-authoritative. | Reviewed agreement on representative work; discrepancies understood. |
| **Supervised use** | Outputs/actions are used with the defined human review or approval. | Quality and operating thresholds hold over an agreed sample/period. |
| **Broader use, if justified** | Expand workload, access, or autonomy within approved limits. | Evidence for the added scope, monitoring, and recovery. |

Permanent supervised use can be the right endpoint. Approval of one task type or stage does not authorize every capability or more access.

Before rollout, record the approved configuration and scope, owner, access/data policy, capacity/budgets, monitoring responses, and rehearsed stop/recovery procedure. Distinguish:

| Operation | What must be defined |
|---|---|
| **Stop** | Prevent new work; cancel or contain active runs; disable triggers or credentials when needed. |
| **Recover** | Identify completed and partial actions; preserve evidence; reconcile external state before bounded retries or resumption. |
| **Roll back** | Restore a compatible prior configuration; consider stored state and memory migrations. |
| **Repair effects** | Re-review affected outputs and correct/reverse external changes where possible. Reverting code does not undo them. |

## 5. Monitoring and response

Watch the same outcomes and boundaries used to justify release. For each signal, define its source, threshold, review cadence, owner, and response. A dashboard without a decision or response path is incomplete.

| Function / outcome | Useful signals | What they may prompt you to inspect |
|---|---|---|
| **Core** | Incomplete runs, errors, time, calls, tokens/cost | Model responses, orchestration, budgets, dependency failures |
| **Context** | Unsupported assumptions, wrong retrieval/skill, missed information | Sources, instructions, retrieval, context selection |
| **Actions** | Tool failures, incorrect calculations, artifact defects, human corrections | Tool contracts, scripts, inputs, validation |
| **Controls** | Limit hits, denied requests, attempted or completed forbidden effects | Authorization, approvals, policy coverage, identities |
| **Continuity** | Resume failures, stale/missing files, repeated actions, unsuitable memory use | Checkpoints, transfer, retry handling, memory scope/version |
| **User outcome** | Acceptance, correction/rejection, unresolved tasks, revision effort | Whether the capability meets the actual need |

These are diagnostic starting points; the same symptom can have several causes. Compare by task type and configuration so changes in workload do not masquerade as quality changes. Review decisions and authoritative external records can reveal problems absent from traces.

Combine three levels of observation:

- **Per run:** retain appropriate status, configuration/source IDs, action outcomes, limits/usage, artifact checks, and review decisions. Apply data minimization, access, and retention rules to logs and traces.
- **Sample review:** inspect outputs and trajectories at a frequency based on risk and volume; use full review where required.
- **Trend review:** examine quality, corrections, cost, and changing inputs over an agreed period. Check whether graders and thresholds still reflect the task.

Respond by impact: **stop/contain** material boundary breaches or harmful results; **diagnose and fix** repeatable defects; **accept with an owner and rationale** bounded limitations. Findings should link to evidence and a decision. Add reproducible evaluation cases where useful, then verify the fix and relevant regressions.

## 6. Changes after release

Use the same loop for changes, with effort proportional to impact. Revisit the affected requirements and plans; build, test, release, and monitor the change. A small fix need not recreate every artifact.

| Change | Review and evidence |
|---|---|
| New task or skill | Objective, procedure, representative capability cases, and relevant regressions; assess bundled code or added access too. |
| New tool, package, connector, or access | Tool behavior, permissions, side effects, failure/retry paths, and affected task regressions. |
| Instructions, retrieval, or knowledge | Cases depending on changed context, plus checks for unintended effects elsewhere. |
| Model or orchestration | Broad representative task and boundary regressions, cost/latency comparison; full release suite where dependencies are broad. |
| Storage or memory policy/schema | Existing-state compatibility, migration/deletion, isolation, resume behavior, and rollback. |
| Purpose, authority, or deployment scope | Revisit all three plans and the release evidence for the new scope. |

### Memory changes alongside software

Runtime updates—messages, working files, status, and permitted memory writes—follow the released policy. They do not each require a new software deployment. But memory can change later behavior even when code is unchanged.

Define whose information may be remembered, its source and scope, how writes are validated, and how it is corrected, expired, or deleted. Approval may be manual or automated according to the use case. Keep user, task, and shared organizational information appropriately separated.

When changing the agent, evaluate representative empty, existing, stale, and conflicting memory states. Decide which stored data remain compatible, which need migration, and which must be invalidated. Keep enough provenance to diagnose behavior and make rollback meaningful.

Agent-generated scripts or skill changes can be used or promoted only within granted authority. Draft generation is not itself authorization to change shared behavior or permissions. Whether a person or automation makes the change, its impact determines the required evidence and release controls.

## Change log

| Version | Date | Change |
|---|---|---|
| v0.6 | 2026-10-24 | Clarified that the implementation inventory maps intended components while the task list owns implementation status and evidence. |
| v0.5 | 2026-10-24 | Combined specification and design as the default planning artifact; placed architecture views and the implementation inventory within the lifecycle structure while keeping requirements, design, code and task tracking distinct. |
| v0.4 | 2026-10-23 | Connected planning artifacts and traceability; clarified evaluation dimensions, rollout/recovery, diagnosis, and memory compatibility; removed universal gates, cadences, and duplicate playbooks. |
| v0.3 | 2026-10-15 | Added release and monitoring plans, staged rollout, rollback, and response rules. |
| v0.2 | 2026-10-15 | Added evaluation design in Plan and cases/graders in Configure. |
| v0.1 | 2026-10-15 | Initial lifecycle model. |
