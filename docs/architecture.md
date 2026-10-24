# Finance & Accounting Agent — Target Architecture

| Field | Value |
|---|---|
| Version | v0.11 design draft · October 24, 2026 |
| Owner | Neil Yee |
| Specification | [Agent specification](agent-spec.md) v0.13 |
| Implementation assessment | Not assessed. Every component and path below describes intended behavior. |

The four views explain system boundaries, responsibilities, execution, and deployment. They apply the [anatomy](mental-model/01-anatomy.md) and link to the spec and evaluations. Solid arrows show calls/data flow; dotted arrows show oversight or policy influence. Line style does not indicate implementation status.

## 1. System overview

```mermaid
flowchart LR
    USER["Person: assign and review"] <--> UI["Terminal interface: first stage"]
    USER <--> ASANA["Asana: later approved stage"]
    UI <--> HOST["Agent host: orchestration and policies"]
    ASANA <--> ADAPTER["Task adapter / dispatcher"]
    ADAPTER <--> HOST
    HOST <--> MODEL["Model provider: proposed OpenAI"]
    HOST <--> SANDBOX["Execution sandbox: code and working copies"]
    HOST <--> STORE["Persistent state, files, operation and review records"]
    HOST --> TRACE["Traces and monitoring"]
    HOST <--> CONNECTOR["Optional scoped connector / MCP"]
    CONNECTOR <--> SYSTEM["Approved business sources"]
```

The foundation should work through the terminal. Asana and other connectors require their own approved scope and evidence. Code execution should use a sandbox; model invocation, orchestration, authorization, and credential management should remain on the host.

## 2. Anatomy view: responsibilities and mechanisms

```mermaid
flowchart TB
    SOURCE["Request, references, feedback"] --> CTX["CONTEXT: select and assemble relevant information"]
    CTX --> CORE["CORE: model calls, orchestration, output handling"]
    CORE -->|"operation request"| GATE["CONTROLS: authorize, validate, enforce budgets"]
    GATE -->|"allowed"| ACTION["ACTIONS: files, code, connectors, delegation"]
    ACTION -->|"result or error"| CTX
    GATE -->|"denied or approval needed"| CORE
    CORE -->|"candidate output"| DELIVERY["Validation and version-specific human review"]
    STATE["CONTINUITY: state, files, checkpoints, operation records"] <--> CORE
    STATE --> CTX
    ACTION <--> STATE
    POLICY["Access, budget, retention and approval policy"] -.-> GATE
    POLICY -.-> CORE
    POLICY -.-> STATE
    POLICY -.-> DELIVERY
    OBS["Observation: traces, outcomes, checks, review decisions"] -.-> CORE
    OBS -.-> ACTION
    OBS -.-> DELIVERY
```

These are responsibilities, not necessarily separate services. Observation spans the functions. Approval after delivery cannot replace authorization before an external action.

| Component / concept | Functions served | Mechanisms / proposed implementation |
|---|---|---|
| Agent harness | Core, Context, Actions | Deep Agents / LangChain orchestration, model adapter, response handling, tool routing. |
| Task adapter | Context, Controls, Continuity | Request normalization, task/thread mapping, eligibility, deduplication, concurrency control. |
| Skills, references, todos | Context, Continuity | Discovery/retrieval, read-only reference routes, planning tool, stored task state; middleware where suitable. |
| Execution and connector tools | Actions, Controls | Host-side authorization; sandbox file/code operations; separately scoped connector identities. |
| Runtime policy | Controls, Core | Checks before calls/actions, shared budgets, output checks, approval and access validation. |
| Durable state and artifact store | Continuity, Context | Checkpoints, per-task files, versions/hashes, operation records and recovery metadata. |
| Review and evidence records | Controls, Continuity | Versioned manifests, decisions, configuration/source IDs, traces and monitoring signals. |

A separate sub-agent context does not imply separate security. If delegation is enabled, its permissions, persistence, and usage must remain within the parent task's approved scope.

## 3. Run view: normal work and failure paths

```mermaid
flowchart TD
    IN["Receive task or revision"] --> ADMIT{"Eligible, authorized, and task ownership acquired?"}
    ADMIT -->|"no"| REJECT["Record blocked or duplicate event"]
    ADMIT -->|"yes"| PREP["Restore state; gather context; prepare working copies and sandbox as needed"]
    PREP --> LIMIT{"Budget available?"}
    LIMIT -->|"yes"| MODEL["Assemble context and invoke model"]
    MODEL --> ROUTE{"Handle response"}
    ROUTE -->|"operation"| CHECK["Validate request and authorize"]
    CHECK --> EXEC["Execute at approved location"]
    EXEC --> SAVE["Record result, operation identity and progress"]
    SAVE --> LIMIT
    ROUTE -->|"candidate answer"| VALIDATE["Check requested outputs and evidence"]
    VALIDATE -->|"repair needed; budget permits"| LIMIT
    VALIDATE -->|"ready for review, or unresolved limitation"| PRESERVE["Persist files, state, checks and outcome"]
    PREP -->|"error"| FAILURE["Record failure or uncertainty; reconcile partial effects"]
    MODEL -->|"error / timeout"| FAILURE
    ROUTE -->|"invalid / incomplete"| FAILURE
    CHECK -->|"denied / failed"| FAILURE
    EXEC -->|"error / uncertain effect"| FAILURE
    LIMIT -->|"no"| FAILURE
    FAILURE -->|"eligible bounded retry; safe resume point established"| PREP
    FAILURE -->|"stop or escalate"| PRESERVE
    PRESERVE --> DURABLE{"Required preservation complete?"}
    DURABLE -->|"yes"| CLEAN["Clean up execution resources; record cleanup outcome"]
    DURABLE -->|"no"| RECOVER["Report partial result; preserve remaining recoverable state; follow retention/recovery policy"]
    CLEAN --> OUT["Return files or recovery details and accurate status"]
    RECOVER --> OUT
    OUT -->|"Needs review"| REVIEW{"Human reviews identified version"}
    REVIEW -->|"approve"| DONE["Record approval / Done"]
    REVIEW -->|"revise"| IN
```

Retry from a verified safe point, not blindly from the beginning. A timeout may follow a completed external effect. Operation records and reconciliation must prevent repeated effects. Cleanup errors remain visible; do not claim complete preservation or success without the required evidence.

Review binds to a specific output version. Revised files require a new decision. The later Asana path must distinguish human feedback from informational comments and agent-generated updates.

## 4. Deployment and trust boundaries

```mermaid
flowchart LR
    UI["Terminal / approved task adapter"] --> AGENT
    subgraph HOST["Agent host: local trial or selected service runtime"]
        AGENT["Orchestration, context, authorization, budgets"]
        REFS["Approved skills / memory: read-only to agent"]
        TRANSFER["Workspace transfer and conflict handling"]
        CONNECTOR["Optional connector with scoped identity"]
        SECRETS["Host credential manager"]
        AGENT --> REFS
        AGENT <--> TRANSFER
        AGENT <--> CONNECTOR
        SECRETS --> AGENT
        SECRETS --> CONNECTOR
    end
    DATA["Durable checkpoints, task files, action/review/configuration records"] <--> AGENT
    DATA <--> TRANSFER
    PROVIDER["Model API"] <--> AGENT
    AGENT --> TRACE["LangSmith traces / monitoring: approved data policy"]
    subgraph SBX["Temporary execution boundary"]
        EXEC["Generated code and file tools"] <--> COPY["Working copies"]
    end
    AGENT <-->|"authorized operations and results"| EXEC
    TRANSFER <-->|"copy in / preserve out"| COPY
    CONNECTOR <--> REMOTE["Approved external system"]
```

| Boundary | Required design |
|---|---|
| Host → model / tracing | Use host credentials and approved data handling. Record model/configuration identity; minimize sensitive trace content. |
| Host → sandbox | Transfer only eligible task data/assets. Do not copy host secrets by default. Restrict and verify filesystem, process, network, and resource access. |
| Sandbox → persistent storage | Preserve outputs and operation evidence before destructive cleanup. Version conflicts; report incomplete transfer. |
| Host → external system | Use a named, scoped connector identity. Initial business access is read-only; Asana task updates require their explicit publication scope. |
| Agent → shared references | Enforce read-only access; owner-approved changes follow the release process. |
| Work item → other tasks/users | Scope state, files, retrieved memory, credentials, and review records. Define ownership/locking for concurrent execution. |

Proposed choices: Deep Agents orchestration, OpenAI model, LangSmith sandbox/tracing, SQLite for local checkpoints, and per-task durable files. Hosted storage, exact versions, retention, identities, and concurrency behavior are decisions D1, D4, D5, and D7 in the spec. A virtual path or provider name alone does not prove isolation.

### 4.1 Context assembly — C1, C2

- Select the task, constraints, expected outputs, relevant history/tool results and revision feedback. Context compaction must preserve material requirements, decisions and source/version identity.
- Discover approved skills and load details when needed; `SkillsMiddleware` and read-only routes are candidates. Retrieve knowledge/memory with source, scope and version; label fictional trial references. Provider-retained context needs an understood scope and lifecycle. Stored information influences the model through supplied input or tool results.
- Copy required execution assets deliberately: virtual skill/memory paths are not necessarily mounted inside the sandbox. Skills provide procedures; host authorization controls access.

### 4.2 Runtime and tool contracts — C2, C5

- Validate Deep Agents / LangChain behavior and extension points. Configure and record model/version, reasoning, context/output limits, timeouts and bounded retries. Supply todo state, such as `TodoListMiddleware`, when useful.
- Route answers, tool requests, refusals, invalid/incomplete responses and failures to explicit outcomes. Support waiting, revision, stopping and recovery. Empty responses and exhausted budgets cannot count as success.
- Keep orchestration and model credentials on the host; execute generated code in the sandbox. Delegated tasks need explicit context, tools, scope and budgets shared with the parent. Separate context does not establish security isolation.
- Enforce call, output, time, retry and delegation limits across the whole run. Define cost policy and measurement limits. Retry only eligible failures after establishing possible effects.
- Add host-side connectors/MCP tools for approved needs. Define each operation's identity, permissions, returned data, errors and side effects. Prefer read-only business access initially.

### 4.3 State, files and recovery — C4, C7

- Define task/thread/run identity and ownership locks. Checkpoint required messages, results, plans and execution state; SQLite is an option for local trials. Keep files in durable storage beyond sandbox lifetime.
- Transfer working copies in and eligible outputs/supporting work out before cleanup. Define exclusions, size limits, version/conflict handling and transfer-failure behavior. Preserve recoverable work and report incomplete transfer or cleanup errors.
- Retain original inputs, prior output versions and concurrent edits. Remote deletion must not silently erase retained work. Cloud sync and live co-editing require separate design and evaluation.
- Use checkpoints and operation records to reconcile completed, missing or uncertain effects before retry. Checkpoints cannot undo external actions.
- Keep reusable guidance owner-maintained. Configure memory ownership, scope, source/version, retention, correction and deletion. Automatic writes require a later policy, compatibility review and evaluation decision; see [spec improvement plan](agent-spec.md#55-respond-and-improve).

### 4.4 Access and approval enforcement — C3, C5, C7

- Enforce source/reference read-only access and task boundaries outside the model, including against instructions embedded in inputs. Restrict and verify filesystem, process, network, resource and identity access; keep host secrets out of generated-code environments unless separately authorized.
- Deny out-of-scope actions. For approved writes, record intent/result and prevent duplicate effects across retries or concurrent workers.
- Bind output approval to a versioned manifest; modifications invalidate approval for the changed version. Initial human review occurs between runs. Separately approve and evaluate changes to shared scripts, models, skills, memory policy or access.
- Assess controls at their actual enforcement boundaries. Instructions, program checks, human review and environment restrictions provide different protections; verify effective behavior.

### 4.5 Evidence and configuration — C6

- Record outcomes, input/output fingerprints, relevant actions, actual checks, usage and approvals; link them to the task/run and delivered version. Use LangSmith tracing for evaluations and pilots under the approved data, access and retention policy.
- Identify code/dependencies, model/settings, instructions, skills/tools, access, environment and storage schema in the configuration manifest. Link input and memory versions separately.

## 5. Traceability and evidence to seek

The spec classifies capabilities as shared foundation (C1–C7), reusable work capabilities (C8–C11), and task-specific capability (C12). These share the same components; the classification does not require separate services.

| Architecture responsibility | Spec | Evaluation | Evidence required during repository review |
|---|---|---|---|
| Model, loop, context and planning | [C1–C2](agent-spec.md#2-capabilities-and-design) | E-PLAT-1, E-REC-1 | Configuration, routing and state handling; representative runs and incomplete-response cases. |
| File/code work and validation | [C2, C7–C12 design](agent-spec.md#2-capabilities-and-design), [3.3 Output standard](agent-spec.md#32-delivery-standard) | E-ART-1, E-FIN-1 | Execution/validation paths and independent artifact/cross-file checks. |
| Permissions, budgets, identity and approval | [C3, C5–C7](agent-spec.md#2-capabilities-and-design) | E-CTRL-1, E-PROV-1 | Enforcement points, access policy, boundary cases and version-specific decisions. |
| Persistence, transfer and recovery | [C4, C7](agent-spec.md#2-capabilities-and-design) | E-FILE-1, E-REC-1 | Checkpoint/file/action records and interruption/conflict/retry evidence. |
| Task intake, publication and revision | [3.1 Assignment lifecycle](agent-spec.md#31-assignment-lifecycle) | E-ASANA-1 | Scope, mapping, trigger/locking rules and integration cases. |
| Release, observation and response | [5.2 Release](agent-spec.md#53-release-plan), [5.3 Monitoring](agent-spec.md#54-monitoring-plan), [C6](agent-spec.md#2-capabilities-and-design) | E-REL-1, E-PROV-1 | Configuration/release record, monitoring owners/thresholds, recovery rehearsal. |

## 6. Design review checklist

These checks describe acceptance of the design; no completion is asserted.

- [ ] Capabilities map to functions, mechanisms, components, criteria, and evaluations.
- [ ] Normal, denied, incomplete, failed, interrupted, and revised work have defined paths.
- [ ] Persistence and reconciliation cover partial effects and transfer/cleanup failure.
- [ ] Controls cover model calls, actions, state changes, and delivery at enforceable boundaries.
- [ ] Credentials, data flows, concurrency, and sandbox access are explicitly scoped.
- [ ] Review identifies output versions; task approval and reusable-asset approval stay distinct.
- [ ] Every required component has implementation and verification work in the task list.

## 7. Change log

| Version | Date | Change |
|---|---|---|
| v0.12 | 2026-10-24 | Updated traceability links for the assignment flow and moved evaluation tasks. |
| v0.11 | 2026-10-24 | Retained technical detail from the spec under capability-linked implementation sections; aligned spec references. |
| v0.10 | 2026-10-23 | Linked architecture responsibilities to the combined capability/design table and shared operating rules. |
| v0.9 | 2026-10-23 | Aligned the spec reference and capability-scope mapping. |
| v0.8 | 2026-10-23 | Recast all views as target design; removed implementation labels; expanded outcome, recovery, control and evidence mappings. |
| v0.7 and earlier | 2026-10-23 | Earlier architecture versions retained in Git history. |
