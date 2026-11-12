# Setup and technical guide

[Project overview](../README.md) · [Documentation index](README.md) · [Script catalog](../scripts/README.md)

This guide covers installation, terminal commands, configuration, and file handling. For profile-specific limits, benchmark execution, output review, and recovery, use the [operating guide](operating-guide.md). Build status is tracked in the [task list](task-list.md); current published test evidence is in the [v5 results](evaluations/excel-v5-results.md) and [foundation report](evaluations/foundation-v5-2026-11-05.md).

[Setup](#setup) · [Run and threads](#run) · [Configuration and skills](#agent-configuration) · [Sandbox and files](#sandbox-execution) · [Engineering checks](#transfer-and-lifecycle-checks) · [Code map](#project-structure)

## Setup

Use Python 3.13 and [uv](https://docs.astral.sh/uv/). From the repository root:

**macOS/Linux**

```sh
uv sync --locked
test -f .env || cp .env.example .env
```

**Windows PowerShell**

```powershell
uv sync --locked
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` and enter your own credentials:

```dotenv
OPENAI_API_KEY=your-openai-key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=accounting-finance-agent
```

Both API keys are required. The example keeps tracing enabled; the local profile can disable uploads with `LANGSMITH_TRACING=false`, but still needs the LangSmith key for sandbox access. The Excel benchmark profile requires tracing. [`.env.example`](../.env.example) documents the local model and reasoning settings.

The default `local` profile and the fixed `excel-benchmark-v5` profile have different controls. The benchmark requires a POSIX host and access to its configured sandbox snapshot; see the [profile instructions](operating-guide.md#versioned-excel-trial-profile) before reproducing the evaluated configuration.

`.env`, the virtual environment, and local caches are ignored by Git. Keep real credentials out of tracked files. When tracing is enabled, prompts, model outputs, and tool data may be sent to LangSmith; use synthetic data for this prototype.

## Run

Start the terminal interface:

```powershell
uv run --locked finance-agent
```

Enter a prompt, read the response, and type `exit` to quit. Follow-up prompts continue the displayed thread. For example: "Explain the purpose of a bank reconciliation in three sentences."

### Persistent conversations

Conversation checkpoints and the thread directory are saved in `.state/checkpoints.sqlite`, outside `workspace/` and outside the sandbox. This private folder is ignored by Git and is not uploaded to the sandbox. On startup, the application resumes the last selected sandbox thread, or creates one if none exists. The terminal prints its ID.

| Command | Purpose |
| --- | --- |
| `:new` | Start a fresh conversation with a new thread ID. |
| `:threads` | List saved sandbox thread IDs and their first-prompt titles. |
| `:thread` | Show the current thread ID. |
| `:thread ID` | Switch to an existing saved conversation. |
| `:workspace` | Show the current thread's local working folder. |
| `:state` | Inspect saved state keys, message count, pending nodes, and todos. |
| `:pending` | Show pending clarification requests and their IDs. |
| `:answer ID response` | Answer a pending clarification and resume its checkpoint in a new sandbox run. |
| `:runs` / `:review` | List recent runs and human review status in this thread. |
| `:recovery [RUN_ID]` | Inspect recorded failure, workspace, transfer and cleanup information; without an ID, show the latest failed, limited or running run. |
| `:approve RUN_ID` | Record approval of a successful run's unchanged file manifest. |
| `:reject RUN_ID reason` | Record rejection; submit requested revisions as the next normal prompt. |
| `:help` | Show terminal commands. |
| `exit` | Close the session and its database connection. |

To select a saved sandbox conversation when launching:

```powershell
uv run --locked finance-agent --thread YOUR_SAVED_THREAD_ID
```

Existing virtual-mode thread data remains in the checkpoint database, but the terminal selects only sandbox threads; it does not migrate virtual files or histories. Thread IDs must already exist to resume them; use `:new` to create another. Switching threads makes no model or sandbox calls.

For missing information, the agent can call `ask_clarification` to pause. The
question is checkpointed and the sandbox workspace is preserved before cleanup.
Use `:pending` and `:answer ID response` in the same thread; this starts a new
run and sandbox and resumes the checkpoint. A paused run is not a completed or
approved deliverable. Questions and answers may appear in checkpoints and traces.
The request format is independent of the terminal, but no Asana adapter exists.

Only the new user message is submitted on each turn. The checkpointer restores previous graph state for that thread, including conversation messages and the harness's context-management state. This is thread memory, not a cross-thread long-term memory store. The integration uses [LangGraph checkpointers](https://docs.langchain.com/oss/python/langgraph/persistence) and [SqliteSaver](https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver).

**Files are separate by thread:** each sandbox conversation uses `workspace/threads/<thread-id>/`, mapped to `/workspace`. Use `:workspace` to locate it. Existing shared files at the root remain untouched; copy needed inputs into the selected thread folder. `:new` creates a separate empty folder. Per-thread local locks prevent overlapping runner executions; external exactly-once recovery is not guaranteed.

To try conversation persistence, start `uv run --locked finance-agent`, say "For this task, the project code is MAPLE-42. Remember it in this conversation," then exit. Start the same command again and ask "What is the project code?" The displayed thread ID should be unchanged. Use `:new` to check that the next conversation starts separately. Each prompt starts a sandbox and makes model calls; starting the app or selecting a thread alone does neither.

These commands make model API calls. Local Python execution does not mean that the model runs locally.

Alternatively, activate the environment and use the Python module:

```powershell
.\.venv\Scripts\Activate.ps1
python -m accounting_finance_agent
```

VS Code is configured to use `.venv`. If an interpreter was previously selected for the workspace, choose this project's environment through **Python: Select Interpreter**.

## Agent configuration

The terminal uses the built-in Deep Agents harness with a SQLite checkpointer, a routed filesystem, and a temporary `LangSmithSandbox` for each prompt. Ordinary working files are stored in the sandbox and preserved in the selected thread’s host workspace. Approved memory and skill routes expose their local folders to file tools. Each prompt starts another run within the selected conversation thread.

The agent explicitly adds [LangChain's to-do middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in#to-do-list). Its `write_todos` tool lets the agent keep a plan with `pending`, `in_progress`, and `completed` items. The list lives in graph state and is persisted with the selected thread. The model decides when a plan is useful; simple questions may not produce a todo list. Inspect `write_todos` calls in LangSmith to observe planning and progress. These internal todos are separate from the future Asana task board.

### Experimental dynamic subagents

For the local profile, set `AGENT_DYNAMIC_SUBAGENTS=true` before launching the agent to add the beta QuickJS interpreter. The agent can call `eval` with JavaScript that dispatches configured subagents through `task()`. Each `eval` starts with a fresh interpreter, and up to four subagent calls run concurrently. Programmatic access to other tools is disabled. The Excel benchmark profile does not enable this option.

Interpreter dispatches use the parent run's shared model-call controls, but the `task()` bridge calls do not pass through the parent tool middleware: each dispatch is not individually counted against the normal tool-call limit or separately subject to parent-level tool approval. The interpreter's concurrency setting is not a total dispatch limit. This option is exploratory; its use changes the local runtime and should be evaluated for the intended workload.

### Experimental reviewer messaging

`finance-agent --profile peer-collaboration-v1` adds two named reviewers that can exchange addressed messages during one run. The reviewers' `send_peer_message` and `receive_peer_messages` tools use a bounded, in-memory mailbox; messages are not durable across runs and do not wake a reviewer that has finished. Tool calls and message contents may appear in traces. The two reviewers have separate conversation contexts and access to the same sandbox-backed workspace. They share the parent run's model and tool limits. The main agent must delegate them concurrently when the work requires real-time communication. Each reviewer name has one inbox per run: multiple simultaneous invocations of the same reviewer would share that inbox, so use one invocation of each role in this prototype. This profile is experimental; it does not add external messaging, background agents, or stateful subagent sessions.

The pinned Deep Agents version omits filenames from some binary `read_file` content blocks. A small filesystem middleware adapter supplies the source basename before model requests, including restored thread history. Existing filenames are preserved; inline attachments without a known source path receive a MIME-based attachment name. This avoids LangChain's `LC_AUTOGENERATED` warning without suppressing warnings globally. The adapter retains the built-in filesystem behavior and is inherited by the default general-purpose subagent through its filesystem middleware slot.

## Approved memory and skills

The following describes the local profile. Benchmark reference routes and staged helpers are described in the [operating guide](operating-guide.md#versioned-excel-trial-profile).

```text
memory/
  AGENTS.md               # Short owner-approved guidance shared across conversations
skills/
  README.md               # How to add skills; this is not itself a skill
  csv-analysis/
    SKILL.md              # CSV inspection and decimal-based summaries
  file-delivery-validation/
    SKILL.md              # Source, structure, calculation, and presentation checks
  financial-working-paper/
    SKILL.md              # Bounded spreadsheet procedure and reusable helpers
  bank-reconciliation/
    SKILL.md              # First finance workflow; execution/evaluation pending
```

These folders are on the local host, outside the temporary sandbox and thread working folders. A `CompositeBackend` provides the following routes:

| Agent path | Storage | Access |
| --- | --- | --- |
| `/memories/` | Local `memory/` | Read-only to agent file tools |
| `/skills/` | Local `skills/` | Read-only to agent file tools |
| Other working paths | Remote sandbox; eligible `/workspace` changes copied back | Working-file tools and execution |

`MemoryMiddleware` loads `/memories/AGENTS.md` into the main agent's system context. A custom memory prompt describes these files as owner-maintained and read-only. `SkillsMiddleware` is registered through `skills=["/skills/"]`; it supplies skill names and descriptions, and the agent reads matching procedures through file tools. Starter CSV analysis and file-delivery validation skills are bundled; company-specific finance skills remain future work. See [memory](https://docs.langchain.com/oss/python/deepagents/memory) and [skills](https://docs.langchain.com/oss/python/deepagents/skills).

The routed backends reject write, edit, delete, and upload operations against approved files. The owner edits these files directly. Memory/skill change proposals and automatic learning are outside the current implementation.

These are virtual file-tool routes, not sandbox mounts. Use `read_file` for `/memories/...` and `/skills/...`; `execute` runs remotely and cannot open those local files. A script stored with a skill must be read and copied into the remote working directory before execution. The application does not automatically install libraries referenced by a skill or copy these folders into the sandbox.

The middleware caches loaded memory and skill metadata in thread state. After changing the approved files, restart the agent and use `:new` to observe a fresh load. You can always inspect a reference file explicitly through file tools. These folders are intended as public project content: keep secrets and private business data out of them. A separate LangGraph Store is not required for this file-based setup.

## Sandbox execution

This section describes the shared lifecycle and local-profile defaults. The benchmark adds source protection, export checkpoints, network isolation, and stricter deadlines; see the [operating guide](operating-guide.md).

Start the agent with:

```powershell
uv run --locked finance-agent
```

The agent requires a LangSmith account with sandbox access enabled and `LANGSMITH_API_KEY` in `.env`, even when tracing is disabled. The SDK uses `LANGSMITH_ENDPOINT` if your account needs another region's API endpoint.

Try this prompt:

```text
Use the execute tool to run python3 --version and then python3 -c "print(2 + 2)". Report the actual command outputs.
```

The terminal loop waits for input before creating a sandbox. Each submitted prompt creates one temporary sandbox, uploads local input copies, gives the agent execution and file tools, downloads outputs, and deletes the sandbox before displaying the final answer. The agent and model client run on your computer; the generated commands run in the remote sandbox. The application does not copy the local `.env` or inject its API keys into that sandbox.

### Versioned sandbox environment

Build and select a reusable snapshot independently of agent runs:

```powershell
uv run --locked python scripts/build_sandbox_snapshot.py --activate
```

The recipe in `environments/finance/` adds LibreOffice Calc, Poppler, and fonts to
the pinned base snapshot. The script uses one temporary builder with
1 vCPU and 2 GiB RAM, records package versions and the resolved base snapshot ID,
captures the release, and confirms builder deletion. Snapshot storage persists
separately. It does not upload task files or make model calls.

`--activate` selects the returned immutable ID in local `.env` as
`SANDBOX_SNAPSHOT_ID`; restart the agent to load it. Blank selects LangSmith's
default. Sandbox allocation and workspace preservation continue as before.
Additional Python packages go in the environment's pinned requirements file;
system packages are configured in `snapshot.json`. Changes require a new build.
See the
[environment release guide](../environments/finance/README.md) for updates, rollback,
base pinning, and deployment configuration. A manual GitHub Actions workflow is defined; configure its repository secret after pushing the project. It has not been run.

### Local workspace

```text
workspace/
  threads/
    <thread-id>/
      sales.csv
      analysis.xlsx
      summary.txt
      scripts/             # The agent can organize working files as needed
      .versions/           # Previous file versions, created when needed
      .conflicts/          # Remote revisions that conflict with local edits
```

At the start of every sandbox run, ordinary files in the selected local `workspace/threads/<thread-id>/` folder are copied to the same relative paths under `/workspace` in the sandbox. There are no required input or output subfolders. Hidden files and folders, `__pycache__`, and the reserved `transfer-tests` folder are excluded. Linked files and directories are rejected. Project files outside `workspace/`, including the project's `.env`, are not uploaded.

The agent reads, creates, revises, and organizes files under `/workspace`. Before cleanup, file hashes identify new or changed remote files, which are downloaded back into the same paths inside the selected thread folder. Unchanged remote files are not downloaded. Binary files and subfolders are supported. These local files stay after the sandbox is deleted and are uploaded on the next run. Workspace data is ignored by Git; only the root folder placeholder is tracked.

Before replacing a working file, the application preserves its previous local bytes under `.versions/<sandbox-name>/<relative-path>`. If a local file also differs from the uploaded version when the merge checks it, the local version is kept and the remote version is saved under `.conflicts/<sandbox-name>/<relative-path>` for review. Both internal folders are excluded from transfers. Sandbox deletions are not applied locally; a remote rename or move can therefore leave both old and new local paths. This is a working-copy merge, not a fully bidirectional filesystem sync.

For example, use `:workspace`, place `sales.csv` directly in that thread folder, and ask:

```text
Read /workspace/sales.csv and summarize its contents in /workspace/summary.txt. Save any supporting script in /workspace/scripts too.
```

This is a copy at the start and end of a run, not a live mount or continuous sync. All eligible working files are uploaded to each fresh sandbox; only new or changed remote files are downloaded. The agent can reuse previous results directly from the same workspace on its next run. Files outside `/workspace` and excluded internal files are not downloaded. Empty folders are not synchronized.

If downloading outputs fails, the application reports the sandbox name and leaves it available for recovery rather than deliberately deleting the only remote copy. The idle-stop and automatic deletion timers still apply, so recover files promptly; local downloads may be incomplete and sandbox usage can continue until it stops. Input-upload failures trigger cleanup before the agent starts.

The request explicitly asks for **1 vCPU and 2 GiB RAM**, with storage determined by the service's default runtime image. The terminal reports the allocation returned by the service. These settings are in `src/accounting_finance_agent/sandbox.py`; they are not presented as the provider's minimum.

Normal completion, ordinary agent failures, and Ctrl+C during agent work trigger output download followed by explicit deletion. A failed download retains the sandbox for recovery, as described above. As a fallback, the request sets a **300-second idle stop** and deletion **600 seconds after stopping**. Idle activity resets the idle timer; this is not a hard run-duration or spending limit. Forcefully terminating the process can bypass its cleanup code. See the [SDK lifecycle documentation](https://docs.langchain.com/langsmith/sandbox-sdk#sandbox-lifetime-and-retention).

Submitted prompts incur model and sandbox usage. Waiting for the next terminal prompt keeps no sandbox open. The selected snapshot supplies the libraries; the runner does not install extra packages automatically. Network enforcement and operating limits differ by profile; consult the [recorded boundaries](operating-guide.md#network-destinations) before relying on them.

**Current boundary:** only eligible files under `/workspace` are preserved in the selected thread folder. Files and conversation state survive restarts. Inspect tool progress in the terminal, run/review metadata through `:runs`, and generated commands in LangSmith when tracing is enabled.

The integration follows the [Deep Agents LangSmith sandbox backend](https://docs.langchain.com/oss/python/deepagents/sandboxes).

## Transfer and lifecycle checks

For a **live file-transfer check without the LLM**, run:

```powershell
uv run --locked python scripts/check_workspace_transfer.py
```

This creates one real sandbox with the same allocation and lifecycle as the agent, so it incurs sandbox usage. It generates small synthetic text, XLSX, and binary fixtures directly in an isolated shared `workspace/transfer-tests/<test-id>` folder, without input/output subfolders. It checks upload hashes, new-file download, in-place revision, previous-version preservation, concurrent local-edit protection, and the policy of keeping local files when remote files are deleted. It then queries the API to confirm deletion. Test artifacts remain locally for inspection; old test runs are excluded from normal agent uploads. No model calls or package installations are made. A failure exits with an error; a download failure retains the sandbox under the normal recovery policy.

The application prints `Sandbox deletion requested` when the delete API call succeeds. The live check then polls for up to 60 seconds for the status API to report the resource is absent; one immediate lookup can still return a record. A stopped record alone does not pass deletion verification. To recheck a previous run without allocating another sandbox:

```powershell
uv run --locked python scripts/check_workspace_transfer.py --check-deletion finance-REPLACE_WITH_NAME
```

The following lifecycle checks are offline:

```powershell
uv run --locked python -m unittest discover -s tests -v
```

These checks mock the cloud client and exercise deletion on success, execution failure, interrupted work, and provisioning failure. They also check that cleanup failures are visible and that exiting without a prompt allocates no sandbox. They make no model or sandbox API calls.

For the full engineering suite with an explicit network guard, fake credentials,
and a saved result report, use:

```powershell
uv run --locked python scripts/check_engineering.py
```

The November 5, 2026 run recorded 150 passing offline checks; see the
[foundation results and limitations](evaluations/foundation-v5-2026-11-05.md).
The [earlier engineering report](history/engineering-checks.md) explains selected checks
and fixes. Financial quality requires separate task evaluations.

## Project structure

```text
docs/
  README.md             # Documentation index and repository map
  technical-guide.md     # Setup, terminal commands, configuration, and files
  operating-guide.md     # Profiles, review, recovery, and benchmark instructions
  agent-spec.md          # Specification and design: Build, Test, Deploy, Monitor
  task-list.md           # ADLC checklist with current project statuses and gates
  evaluations/          # Published benchmark contract and result reports
  history/              # Earlier assessments, build notes, and test reports
  mental-model/
    00-overview.md       # Map of the anatomy and ADLC models
    01-anatomy.md        # Agent functions and implementation mechanisms
    02-adlc.md           # Build, test, deploy, and monitor lifecycle
environments/finance/
  snapshot.json          # Snapshot name/tag and base environment
  requirements.txt       # Optional additional remote Python packages
  README.md              # Build, select, update, and roll back environments
scripts/
  README.md             # Script catalog grouped by purpose and side effects
  build_sandbox_snapshot.py  # Prepare and capture a reusable cloud environment
src/accounting_finance_agent/
  __init__.py
  __main__.py            # Minimal terminal input/output loop
  agent.py               # Agent construction, model, and backend routing
  file_metadata.py       # Filename compatibility adapter for binary file reads
  knowledge.py           # Persistent read-only memory/skills routes
  config.py              # Environment loading and validation
  persistence.py         # SQLite checkpoints, thread directory, and active thread
  sandbox.py             # Temporary sandbox creation, preparation, and cleanup
  workspace.py           # Thread workspace transfer, versions, and conflicts
  runtime.py             # Current-time context and shared call/deadline controls
  worklog.py             # Run events, local leases, and artifact review records
  validation.py          # Limited structural checks on generated files
memory/
  AGENTS.md              # Approved shared guidance
  company-profile.md     # Provisional fictional company conventions
skills/
  README.md              # Skill authoring layout; procedures added separately
workspace/
  .gitkeep
  threads/<thread-id>/   # Task working files; data is ignored by Git
.state/
  checkpoints.sqlite     # Private conversation database, ignored by Git
  worklog.sqlite         # Run provenance, transfer events, and human reviews
tests/
  test_sandbox.py         # Offline lifecycle and entry-point checks
.env.example             # Configuration template without credentials
pyproject.toml           # Dependencies and finance-agent command
uv.lock                  # Locked dependency versions
```

This is a selected code map. For architecture and planned work, see the [specification and design](agent-spec.md) and [task list](task-list.md).

