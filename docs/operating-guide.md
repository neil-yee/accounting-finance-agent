# Local operating defaults

These foundations support a local, human-reviewed prototype. The expanded offline
engineering suite passed 58 tests, including real graph execution with fake model
replies. A user-run CSV/JSON smoke task also passed; finance-quality evaluation
and broader live checks remain pending. See
[engineering results](engineering-checks.md) for the distinction and coverage.

## Versioned Excel trial profile

`excel-benchmark-v1` configures the first trial. Its strict runner requires a
POSIX host (Linux/macOS) and a sandbox supporting unprivileged network namespaces.
The current cloud host and frozen snapshot passed the build checks. The existing
`local` profile retains its earlier behavior and limitations.

```powershell
uv run --locked finance-agent --profile excel-benchmark-v1 --show-config
uv run --locked finance-agent --profile excel-benchmark-v1 --sandbox
```

The first command prints settings, dependency/source/reference hashes and snapshot
identity without model calls. The second starts an interactive session. The
benchmark profile overrides model, reasoning, tracing, limits and snapshot values
in `.env`; credentials, trace project and timezone use the normal environment.
Do not change settings during a three-run series.

| Setting | Excel profile |
|---|---|
| Model/reasoning/API tier | gpt-6-luna / high / Standard (`default`) |
| Tracing/delegation | Tracing on; delegation disabled |
| Requests/tools | At most 20 provider attempts including compaction/retries; 40 tool attempts |
| Time | 600-second work deadline; shared 60-second preservation/cleanup phase |
| API budget | US$1, conservative preflight reservations; unknown usage keeps its reservation |
| Output | At most 32,000 tokens, reduced to fit remaining spend |
| Retry policy | Up to five eligible retries; SDK retries disabled; read-only tool retries only |
| Sandbox | `3dce6ed0-f050-432a-bc9a-79a7b960972f`; openpyxl, LibreOffice, Poppler/fonts |
| Transfer | 10 MiB/file and 50 MiB per transfer; cumulative checkpoint export ceiling 50 MiB |

The rate card in `config/model-pricing.json` records published pricing and higher
reservation rates covering documented cache writes, long context and regional
premiums. Cache discounts are ignored conservatively; the ledger is an upper-bound
estimate, not a provider invoice. Raw usage is retained for reconciliation.
Binary provider inputs and hidden server-side history are rejected; inspect Excel
through sandbox libraries. Only the synchronous benchmark runner is metered.

**Network and files.** Organization-level egress overrides the provider's requested
deny rule. The benchmark therefore runs every execution command in a fresh Linux
user/network namespace with no external interfaces. Live checks blocked DNS,
direct-IP connection and namespace re-entry. Failure to create the namespace fails
the command. The host still reaches model, tracing and sandbox-control APIs.
Source CSV/notes/task files are checked against hashes and never replaced on export.
The same per-thread file scope, read-only approved routes and credential boundary
apply throughout. Export checkpoints run after successful tool operations and at
exit; abrupt remote loss can lose changes since the last confirmed export.

**Artifacts and evaluation.** Read the approved `recalculate.py` helper through the
file tool and copy it to the sandbox. Build in a staging directory and convert in a
separate invocation to a final directory. The helper saves recalculated XLSX,
PDF/page previews and a check record; never resave the final XLSX through openpyxl.
The runner blocks missing workbooks, missing formula caches and missing rendered
evidence. Human narrative/layout approval is still required.

```powershell
uv run --locked python scripts/run_excel_series.py --run
uv run --locked python scripts/grade_excel_benchmark.py workspace/threads/THREAD_ID
uv run --locked python scripts/seed_excel_defects.py PATH_TO_CANDIDATE PATH_TO_MUTANTS
```

The series command is explicitly paid: three fresh threads, fixed agent-only
inputs, independent graders and a saved outcome for every attempt. It does not
approve outputs automatically. Evaluator answers stay outside agent references
and workspaces. Code graders check the specified labels/layout contract; human
review covers meaning, grounding, formula dependency interpretation and appearance.

**Evidence, backup and monitoring.** Work-log run details contain a secret-free
configuration manifest; events contain compaction settings, provider attempts,
reservations/usage, transfers, sandbox inventory and checks. After each benchmark
run, consistent SQLite backups and task files are copied to the owner-only
`accounting-finance-agent-archives` folder beside the repository. Back up that
folder separately for device-loss protection. Failed backup prevents completion.

```powershell
uv run --locked python scripts/monitor_runs.py
uv run --locked python scripts/manage_retention.py --close THREAD_ID
uv run --locked python scripts/manage_retention.py
uv run --locked python scripts/manage_retention.py --apply --hosted
```

Review every result and the three-run series; investigate financial errors, missing
outputs, unauthorized effects and budget failures before using results. Review
recurring defects/cost and retention weekly. Stop with Ctrl+C, inspect `:state`,
`:runs` and files, and reconcile effects before retrying. Approved outputs are bound
to exact file hashes; changed versions require new review.

Closure starts the 30-day raw-state retention clock. Retention defaults to a plan;
`--apply` archives final files/inputs/supporting code and removes eligible raw state
and scratch data, including closed-thread checkpoints in backups. `--hosted` also
queues deletion of exact recorded root trace IDs and later verifies absence.
Provider deletion is asynchronous; closure markers remain until verified. No
retention deletion was executed during this build. Final deliverables, reference
fixtures, reviews and configuration records remain until owner deletion.

**Reference maintenance.** Benchmark memory comes from
`references/excel-benchmark/memory/AGENTS.md`, with only `csv-analysis` and
`file-delivery-validation` skills. The legacy company profile is outside these
routes. The owner corrects/removes guidance in its source file, reviews/commits the
change, restarts and uses a fresh thread. Existing checkpoints/traces can retain
old content until their own retention/deletion process completes.

Build evidence is recorded in [the task list](task-list.md#11-build-progress).
Build completion does not establish benchmark quality or authorize business use.

## Local trace copies

Sync this repository's **accounting-finance-agent** LangSmith project into `traces/`:

```powershell
uv run --locked python scripts/export_traces.py --sync
```

Running without arguments does the same sync. It queries every root trace in the
date window, follows all child-run pages, downloads new traces and refreshes
changed ones. Unchanged exports retain their existing files and timestamps.
The final summary reports new, updated, unchanged and failed exports; failures
return a nonzero exit code. Repeat the command to pick up later runs or delayed
trace ingestion. Local files are retained if the cloud record is absent or older
than the date window.

Download one completed trace (the app's `Run:` UUID is its root-run ID):

```powershell
uv run --locked python scripts/export_traces.py --trace 4b5fa1d2-5cda-4ce2-9af9-34cb75f008cf
```

Or download just the ten most recent traces from this project:

```powershell
uv run --locked python scripts/export_traces.py --latest 10
```

The script uses `LANGSMITH_API_KEY` and the optional endpoint/workspace environment
settings through the installed SDK. Its project defaults explicitly to
`accounting-finance-agent`, independent of another shell's `LANGSMITH_PROJECT`.
`--project NAME` is available as an explicit override.
Queries cover the last 30 days; use `--days N` to extend this up to 400 days.
It performs read-only API queries, without starting an agent or sandbox.

Each `traces/trace-<uuid>.json` contains a flat list of root/child run records,
including inputs, outputs, timing, errors and available token/cost metadata.
Parent IDs preserve the hierarchy. Separate binary attachments are excluded.
Incomplete runs are flagged; repeat the command after ingestion completes to
refresh the same file. Synchronization runs when you invoke the command; no
background service or automatic download after agent runs is installed.
The entire folder is Git-ignored because traces can contain private task data.

## Workspace transition

Each conversation now uses `workspace/threads/<thread-id>/`, mapped to `/workspace`
in its temporary sandbox. There are no required input/output subfolders inside it.
Use `:workspace` to locate the current folder. `:new` creates a new conversation
and a separate empty folder; returning to a thread restores its folder.

Existing files directly under `workspace/` remain untouched and are not uploaded
automatically. Copy the files you want into the selected thread folder. Earlier
messages can still refer to older shared files; a fresh thread is preferable for
the first run with these new defaults and newly registered skills.

## Runtime context and limits

| Setting | Default | Scope |
| --- | --- | --- |
| AGENT_TIMEZONE | America/Toronto | Date, weekday, and current time refreshed per model request; tzdata supports Windows. |
| AGENT_MAX_MODEL_CALLS | 40 | Intercepted agent model requests shared by parent and default general-purpose subagent. |
| AGENT_MAX_TOOL_CALLS | 120 | Tool attempts, including delegation and subagent tools, shared across the run. |
| AGENT_RUN_SECONDS | 900 | Refuse new model/tool calls after this elapsed time. |
| AGENT_MODEL_TIMEOUT_SECONDS | 120 | Provider request timeout, including its configured transport behavior. |
| AGENT_TOOL_TIMEOUT_SECONDS | 120 | Maximum timeout requested through sandbox execute; preparation/export use their own timeouts. |
| AGENT_MAX_OUTPUT_TOKENS | 16000 | Per model response; provider interpretation includes its reasoning/output accounting. |

Context also carries a run UUID, thread ID, workspace, trigger name, and optional
task ID. The terminal trigger leaves task ID unset; Asana mapping is still deferred.
Current time is not the accounting reporting period.

The elapsed deadline is an admission check, not a process kill at precisely 15
minutes. In-flight requests, SDK retries, transfers, and cleanup can finish later.
The model SDK permits at most two transient transport retries; task tools and whole
runs are never automatically replayed. Compaction's internal provider calls and
provider retry attempts are not separately counted by the middleware. These are
operating bounds, not a guaranteed dollar cap. Model calls made outside this local
runner do not automatically receive its controls.

The filesystem middleware slot carries both filename repair and shared run hooks
so the pinned Deep Agents default subagent inherits the same controls. Its normal
filesystem/offloading behavior remains in place. If changing the harness version,
recheck this slot-inheritance behavior.

## Network destinations

The runner sends `proxy_config.access_control.allow_list` with PyPI's package hosts
and SEC data hosts, restricted to port 443. Configure `SANDBOX_ALLOWED_HOSTS` as a
comma-separated list to add owner-approved sources. A different website, git
dependency, or package download host can require another entry.

This configuration has not been checked against live egress. LangSmith documents
the controls at the sandbox host; its organization-level restricted-egress policy
can replace caller-supplied rules. Do not claim that this local configuration has
proved isolation or that adding a host grants access beyond the provider policy.
The separate environment builder does not use the task runner's destination list.

[Provider egress documentation](https://docs.langchain.com/langsmith/sandbox-auth-proxy)

## Inspecting work

| Command | Meaning |
| --- | --- |
| :state | Checkpoint keys, message count, pending nodes, and todo status; no model call. |
| :workspace | Current local working folder; no sandbox allocation. |
| :runs / :review | Last 20 runs for the current thread, execution outcome and review status. |
| :approve RUN_ID | In sandbox mode, record human approval only if a successful run's entire eligible file manifest still matches. |
| :reject RUN_ID reason | Record rejection of that run's output version. Send the revision request as the next normal prompt. |

Tool names and completion statuses are printed during execution, including default
subagent activity. Raw tool arguments, document bodies, and binary attachments are
not dumped into the terminal by these progress hooks. Tracing has its own content
capture settings and may include them.

Approval records include the local OS username and file SHA-256 hashes. Later file
changes make the prior review display stale. This is a local reviewer record, not
authenticated enterprise approval or permission to post ERP transactions. No
memory, skill, or script is automatically promoted. The check and approval record
are not an OS lock against a person editing a file concurrently.

## Work logs and recovery

`.state/worklog.sqlite` stores run status, run/thread IDs, selected snapshot, input
and output file hashes, tool names/counts, transfer manifests, structure-check
findings, and review events. It does not store prompts or full tool payloads.
Conversation content remains in checkpoints/traces. Back up `.state` and task
workspaces separately; do not publish these private files.

The local per-thread lock prevents two runner processes from executing one thread
at the same time. After a hard crash, a run may remain marked running and its lock
may remain. Inspect the lock's recorded PID and actual process before removing a
stale lock. There is no distributed lease service or exactly-once action guarantee.

On ordinary errors the runner records failure and returns to the terminal. Inspect
the checkpoint and files before giving the next instruction. Download failure keeps
the sandbox available under its existing idle/deletion timers. To explicitly retry
export using recorded upload hashes, without replaying the task:

```powershell
uv run --locked python scripts/recover_sandbox.py RUN_ID --delete-after-copy
```

This can wake the sandbox and incur compute usage. Recovery only works while it
still exists, and uses the same conflict-preserving merge. It records the recovery,
but does not turn a failed task into an approved result. Deletion is a request;
the existing deletion-check script can confirm absence.

## Output checks and evaluation

Changed XLSX/DOCX/PPTX/CSV/JSON outputs receive limited host structural checks after
export; failures block normal completion/approval. Results go in the work log.
The checker never executes generated scripts/macros and does not evaluate Excel
formulas. ZIP inspection is capped at 200 MiB uncompressed and may report a skipped
check. Unsupported types are not validated. These checks do not establish financial
accuracy, visual quality, or successful recalculation.

The CSV and file-delivery skills define calculation/source/reopening procedures.
Actual performance still needs task-specific evaluation. See
[draft evaluation cases](../evaluations/README.md). Evaluation trials and the manual
GitHub snapshot workflow are opt-in; neither was run during this implementation.

## Provisional finance workflow and company context

`skills/bank-reconciliation/SKILL.md` defines the first finance workflow: inspect
bank and cash-ledger inputs, control their balances and row coverage, match unique
transactions, explain reconciling items, build the balance bridge, and prepare an
Excel workbook plus Word memo and proposed entries for human review. It is a
procedure, not an executed or evaluated reconciliation result.

`memory/company-profile.md` supplies explicitly fictional defaults for Maple
Harbour Services Ltd.: Ontario/Toronto, CAD, December year-end, monthly accrual-based
management reporting, one operating bank account, exact-amount matching with a
three-calendar-day date window, and zero unexplained residual. Every unmatched or
ambiguous item is reported; no materiality threshold, automatic write-off, posting,
or approval is inferred. Transaction files and balances must come from the task.

These are provisional demonstration assumptions authorized for this prototype.
They do not establish real-company facts, tax policy, or statutory accounting
compliance. The agent must label their use and respect different source/task facts.
Real-company policies, source-system mappings and accounting conclusions still
require that entity's context.

Edit the company profile to change business conventions and the skill file to
change the procedure. Both are available through existing read-only file routes;
no new backend, model prompt module, or sandbox snapshot is needed. Restart and use
`:new` after edits to avoid previously cached guidance. Company context is referenced
from the small always-loaded AGENTS.md and read on demand, rather than putting the
whole profile into every conversation's initial prompt.

API/Studio hosting, Asana, production deployment, and the final verified finance
demonstration remain future work.
