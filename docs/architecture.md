# Finance & Accounting Agent — Architecture

| Document field | Value |
|---|---|
| Version | v0.5 working draft |
| Owner | Neil Yee |
| Specification | [Agent specification](agent-spec.md) v0.6 |
| Status | Current prototype with proposed Asana and external-system integrations. |

This architecture applies the [00 overview](mental-model/00-overview.md) and [01 anatomy](mental-model/01-anatomy.md) to the project. The anatomy view shows what the agent is made of; the run view shows how requests move through it; the deployment view shows where components run and what they can reach. Solid nodes and edges describe the current prototype. Dashed edges are proposed future integrations or release paths.

## 1. Overview

```mermaid
flowchart LR
    P["Person<br/>requests, reviews, approves"]
    T["Local terminal<br/>current work interface"]
    A["Accounting and finance agent<br/>Deep Agents harness"]
    M["OpenAI model provider"]
    S["Temporary sandbox<br/>code and working files"]
    D["Persistent local data<br/>threads, files, work log"]
    L["LangSmith<br/>optional tracing and sandbox service"]
    AS["Asana<br/>planned work interface"]

    P <-->|"prompts and responses"| T
    T <-->|"invoke and resume thread"| A
    A <-->|"model input and response"| M
    A <-->|"tools, code, and files"| S
    A <-->|"checkpoints, workspace, records"| D
    A -.->|"traces"| L
    A -.->|"task intake, review, output links"| AS
```

## 2. Anatomy view: functions and mechanisms

```mermaid
flowchart TB
    subgraph AGENT["Agent: what it is made of"]
      direction TB
      subgraph CORE["CORE — what reasons and drives the work"]
        LOOP["Harness control loop"]
        MODEL["OpenAI model invocation"]
        TODO["TodoListMiddleware<br/>write_todos and graph state"]
      end
      subgraph CONTEXT["CONTEXT — what the model sees"]
        PROMPT["Task prompt and instructions"]
        HISTORY["Messages and tool results"]
        SKILLS["Skills<br/>discovery plus read-only file tools"]
        KNOW["Approved memory and business references"]
        CTX["Context assembly on each model call"]
      end
      subgraph ACTIONS["ACTIONS — what the model can request"]
        FILES["File tools<br/>read, list, write, edit"]
        EXEC["execute tool<br/>remote sandbox code"]
        SUB["General-purpose sub-agent"]
        FUTURE["External connectors / MCP<br/>not implemented"]
      end
      subgraph CONTROLS["CONTROLS — which requests are allowed"]
        LIMITS["Runtime call, time, and command limits"]
        ROUTES["Read-only reference routes"]
        SANDBOX["Sandbox, filesystem, and egress policy"]
        REVIEW["Human review of output and assets"]
      end
      subgraph CONTINUITY["CONTINUITY — what carries over"]
        STATE["SQLite thread checkpoints"]
        WORKSPACE["Per-thread local workspace"]
        LOGS["Work log, validation, optional traces"]
      end
    end

    TASK["Prompt, instructions, history, references"] --> CTX --> MODEL
    LOOP --> CTX
    MODEL -->|"request or answer"| LOOP
    LOOP -->|"approved tool request"| FILES
    LOOP --> EXEC
    LOOP --> SUB
    LOOP -.-> FUTURE
    FILES -->|"tool result"| CTX
    EXEC -->|"tool result"| CTX
    SUB -->|"subtask result"| CTX
    LIMITS -.-> LOOP
    ROUTES -.-> FILES
    SANDBOX -.-> EXEC
    REVIEW -.-> WORKSPACE
    STATE <--> LOOP
    WORKSPACE <--> EXEC
    LOGS -.-> LOOP
    KNOW --> CTX
    SKILLS --> CTX
    TODO <--> LOOP
```

## 3. Run view: how one task flows

```mermaid
flowchart TB
    INPUT["Person submits prompt<br/>or selects a saved thread"] --> GATHER["Prepare context<br/>instructions, thread state, skills, references"]
    GATHER --> PREP["Sandbox mode: create temporary sandbox<br/>copy thread workspace into /workspace"]

    subgraph LOOP["Agent control loop — repeats until answer or limit"]
      ASSEMBLE["Assemble model input"] --> INVOKE["Invoke model"] --> ROUTE{"Tool request or final answer?"}
      ROUTE -->|"tool request"| CHECK["Apply runtime/backend controls"] --> TOOL{"Tool location"}
      TOOL -->|"file work or execution"| SBX["Remote sandbox"]
      TOOL -->|"memory or skill read"| HOSTREF["Read-only host route"]
      TOOL -->|"subtask"| SUB["Sub-agent loop"]
      SBX --> RESULT["Return tool result"]
      HOSTREF --> RESULT
      SUB --> RESULT
      RESULT --> ASSEMBLE
    end

    PREP --> ASSEMBLE
    ROUTE -->|"final answer"| PRESERVE["Download new/changed files<br/>record run and checks"]
    PRESERVE --> CLEAN["Delete sandbox after preservation"]
    CLEAN --> RETURN["Return summary and local file location"]
    RETURN --> HUMAN{"Human review"}
    HUMAN -->|"feedback"| INPUT
    HUMAN -->|"approve current output"| END["Done"]
    CHECK -->|"blocked or failed"| PRESERVE
    FUTURE["Asana intake, status, and review"] -.-> INPUT
    FUTURE -.-> RETURN
```

## 4. Deployment view: where it runs and what it can reach

```mermaid
flowchart LR
    PERSON["Person"] --> TERMINAL["Local terminal<br/>current"]
    ASANA["Asana<br/>planned"] -.-> DISPATCH["Future dispatcher"]

    subgraph HOST["Agent host — local in current prototype"]
      TERMINAL --> AGENT["Agent loop<br/>context, controls, tool routing"]
      DISPATCH -.-> AGENT
      STORE["SQLite checkpoints<br/>thread workspace<br/>work log"]
      REFS["Local memory and skills<br/>read-only file routes"]
      CONNECT["Controlled connector / MCP<br/>future; no SharePoint or ERP connection"]
      AGENT <--> STORE
      AGENT --> REFS
    end

    MODEL["OpenAI model provider"]
    TRACE["LangSmith tracing<br/>optional"]
    AGENT <-->|"model input and response"| MODEL
    AGENT -.->|"trace data"| TRACE

    subgraph REMOTE["Temporary LangSmith sandbox"]
      EXEC["Code and file tools<br/>Python environment"]
      WS["/workspace<br/>working copies"]
      EXEC <--> WS
    end
    AGENT <-->|"start run, tools, files"| REMOTE
    STORE -->|"copy files into run"| WS
    WS -->|"download changed files before cleanup"| STORE

    EXTERNAL["Business systems<br/>future, scoped read-only access"]
    CONNECT -.->|"controlled access"| EXTERNAL
    ASANA <--> DISPATCH

    CREDENTIALS["Current model and LangSmith credentials<br/>loaded on host; not copied into sandbox"]
    CREDENTIALS --> AGENT
```

**Trust boundary:** the agent loop and model client run on the host. The temporary sandbox executes generated commands and receives eligible workspace files. The application does not copy its local `.env` or API keys into the sandbox. Network egress is owner-configurable, but effective isolation has not been verified. A future external connector would run outside the sandbox and would need a separately defined identity and access scope. Do not infer that an integration or control exists just because it appears as a proposed component.

## 5. Traceability: architecture to specification

| Architecture element | View | Spec section | Current state |
|---|---|---|---|
| Core: loop, model, planning, limits | 2, 3, 4 | [2.1 Core](agent-spec.md#21-core-what-reasons-and-drives-the-work) | Implemented; some live limit checks pending |
| Context: task, instructions, history, skills, knowledge | 2, 3 | [2.2 Context](agent-spec.md#22-context-what-the-model-sees) | Implemented locally; Asana task gathering planned |
| Actions: file tools, execute, sub-agent | 2, 3, 4 | [2.3 Actions](agent-spec.md#23-actions-what-the-model-can-request) | Implemented |
| Controls: routes, runtime limits, sandbox, review | 2, 3, 4 | [2.4 Controls](agent-spec.md#24-controls-which-requests-are-allowed) | Partial; see README verification inventory |
| Continuity: checkpoint, workspace, work log, traces | 2, 3, 4 | [2.5 Continuity](agent-spec.md#25-continuity-what-carries-over) | Implemented locally; recovery and provenance gaps remain |
| Asana dispatcher and review path | 2.7, 3, 4 | [2.7 Work lifecycle and interface](agent-spec.md#27-work-lifecycle-and-interface), [3.1 E-ASANA-1](agent-spec.md#31-evaluation-plan) | Proposed, not implemented |
| External connector or MCP | 2, 4 | [2.3 Actions](agent-spec.md#23-actions--what-the-model-can-request), [2.4 Controls](agent-spec.md#24-controls--which-requests-are-allowed) | No external business-system integration |
| Model provider and LangSmith | 1, 4 | [2.1 Core](agent-spec.md#21-core--what-reasons-and-drives-the-work), [3.3 Monitoring](agent-spec.md#33-monitoring-plan) | Model call and optional tracing implemented |

## 6. Completeness and review checklist

- [ ] Every anatomy function has a project decision and named implementation mechanism in Section 2 of the spec.
- [ ] Every spec function appears in the anatomy view; every box maps to a spec section above.
- [ ] Each proposed or implemented path is labeled accurately; placeholders are not presented as running services.
- [ ] Each control is shown at its actual strength: instruction, program hook, human decision, or environment.
- [ ] Credentials and network routes match the real execution boundary.
- [ ] Every success criterion maps through a function and mechanism to at least one evaluation in the spec.
- [ ] Run flow identifies persistence, cleanup, human review, and failure handling.

## 7. Change log

| Version | Date | Change |
|---|---|---|
| v0.6 | 2026-10-22 | Updated the spec cross-reference for its revised section order. |
| v0.5 | 2026-10-22 | Adapted the four-view architecture template to the current prototype and the five-function anatomy; added spec traceability and current/future labels. |
| v0.4 | 2026-10-15 | Prior project-specific architecture diagram. |
