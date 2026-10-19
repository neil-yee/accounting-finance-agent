# Finance & Accounting Agent — Architecture

**Status:** Proposed design, October 15, 2026.  
**Source:** Recreated in editable Mermaid from the architecture image supplied by Neil Yee. This is not a copy of the original image file.  
**Related document:** [Agent specification](agent-spec.md).

GitHub renders the Mermaid block below as a diagram. Edit the block to update the architecture alongside the code.

```mermaid
flowchart TB
    human["Neil / human reviewer<br/>Assign work, provide feedback, approve"]
    asana["Asana task board"]
    model["Model provider"]
    tracing["Tracing and monitoring<br/>LangSmith candidate"]
    erp["SQL Server or SYSPRO<br/>Phase 2: read-only access"]
    approval["Explicit owner approval<br/>for reusable assets"]

    subgraph host["Agent host — outside the execution sandbox"]
        dispatcher["Dispatcher<br/>Detect eligible changes, gather context,<br/>prevent duplicate runs"]
        agent["General finance and accounting agent"]
        connector["Controlled connectors or MCP<br/>Read-only external-data access"]
        transfer["File transfer<br/>Copy inputs in and preserve outputs"]

        dispatcher -->|"Task context and relevant changes"| agent
        agent -->|"Results, proposals, or failure details"| dispatcher
        dispatcher -->|"Prepare task workspace"| transfer
        agent <-->|"External data requests and results"| connector
    end

    subgraph sandbox["Temporary sandbox — restricted code execution"]
        inputs["Task files<br/>Input copies and reference material"]
        packages["Python packages<br/>pandas, openpyxl, and others"]
        execution["General execution and file tools"]
        outputs["Generated files, supporting code,<br/>and proposals"]

        inputs --> execution
        packages --> execution
        execution --> outputs
    end

    subgraph storage["Persistent storage — survives sandbox cleanup"]
        artifacts["Task inputs, versioned outputs,<br/>and supporting code"]
        pending["Pending memory, script,<br/>and model proposals"]
        checkpoint["Checkpointer<br/>Conversation state per Asana task"]
        worklog["Work log<br/>File fingerprints, run IDs,<br/>and asset versions"]
        approved["Business knowledge, skills,<br/>approved memory and scripts"]
    end

    human -->|"Tasks, feedback, and review"| asana
    asana -->|"Eligible assignment or actionable feedback"| dispatcher
    dispatcher -->|"Status, summary, and output links"| asana

    agent <-->|"Model requests and responses"| model
    agent -.->|"Run traces"| tracing
    connector -->|"Read-only queries"| erp

    transfer -->|"Copy inputs and approved assets"| inputs
    agent <-->|"Run code, inspect files, receive results"| execution
    outputs -->|"Copy out before cleanup"| transfer

    artifacts -->|"Inputs and previous files for revisions"| transfer
    transfer -->|"Preserve input copies and output versions"| artifacts
    transfer -->|"Preserve asset proposals"| pending
    transfer -->|"Record transfers and fingerprints"| worklog
    agent <-->|"Save and restore task context"| checkpoint
    worklog -->|"Prior runs and version history"| dispatcher
    approved -->|"Relevant business context and procedures"| dispatcher
    approved -->|"Approved assets to copy in"| transfer

    human --> approval
    pending -->|"Review proposed assets"| approval
    approval -->|"Promote approved versions"| approved
```

## Reading the diagram

Asana is the main work interface. The dispatcher identifies eligible assignments and feedback, gathers context, and starts the agent. The agent uses the model provider and controlled external-data connectors from the host. Code execution and task-file manipulation happen inside the temporary sandbox.

The file-transfer component prepares the workspace and preserves outputs before sandbox cleanup. Persistent storage holds task artifacts, checkpoints, factual work logs, pending proposals, and approved reusable assets.

Human review of a task output happens through Asana. Approval of memory or reusable scripts and models follows a separate owner decision before promotion to the approved library.

## Boundaries and unresolved choices

- The diagram expresses logical components. It does not require a separate service or process for every box.
- The dispatcher and agent initially run on a local host. The sandbox may be hosted or a restricted local container; the provider is undecided.
- External-system credentials stay outside the execution sandbox. Network and filesystem restrictions require actual environment controls.
- The diagram's read-only connector applies to external business data. The dispatcher has separately controlled Asana write access for statuses, summaries, and output links.
- SQL Server or SYSPRO access is a Phase 2 capability. Posting entries, payments, and changes to authoritative ERP records are excluded initially.
- One Asana task defines the initial thread scope. Revisions restore that task's state and use preserved output versions.
- Business knowledge is human-maintained. Memory, scripts, models, and skill changes require separate approval; approving a task output does not promote them.
- Polling versus webhooks, task eligibility, feedback rules, storage location, and operating limits remain open decisions in the [agent specification](agent-spec.md#open-decisions).
- Monitoring captures runs; the transfer log records copy-in and copy-out activity. Neither is assumed to record every internal sandbox file operation.

## First implementation milestone

An Asana task with an attached CSV triggers one agent run. The agent processes an input copy in a sandbox, produces a reviewable artifact, and preserves it before cleanup. The dispatcher publishes a summary and output link in Asana. Human feedback starts a revision on the same task thread.

The first finance skill follows after this complete path works. Bank reconciliation is the current candidate.
