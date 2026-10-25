# Local operating defaults

These foundations support a local, human-reviewed prototype. The expanded offline
engineering suite passed 58 tests, including real graph execution with fake model
replies. A user-run CSV/JSON smoke task also passed; finance-quality evaluation
and broader live checks remain pending. See
[engineering results](engineering-checks.md) for the distinction and coverage.

## Versioned Excel trial profile

The first build increment adds `excel-benchmark-v1` alongside the existing
`local` profile. Its run safeguards are still under construction; the CLI and
`run_prompt` reject benchmark execution before allocating a sandbox or calling
an API. Direct graph construction is available for later offline checks.

Inspect the selected configuration without a model call, sandbox or API key:

```powershell
uv run --locked finance-agent --profile excel-benchmark-v1 --show-config
```

Use `--show-config` without a profile to inspect the existing local settings.
The command prints explicit settings, dependency versions, selected reference
routes, source/reference hashes and outstanding execution blockers. It excludes
API keys, environment dumps and document contents. It does not verify provider
access or sandbox packages.

| Setting | Excel profile |
|---|---|
| Model / reasoning / API tier | gpt-6-luna / high / Standard (`default` in the API) |
| Tracing | On |
| Delegation | Default general-purpose subagent disabled; no explicit subagents |
| Model/tool counts | 20 / 40 configured ceilings; complete attempt accounting pending |
| Work deadline / per-attempt timeouts | 600 seconds / 180 model / 120 tool; hard deadline enforcement pending |
| Output ceiling | 32,000 tokens; spend-based reduction pending |
| SDK retries | Disabled; the shared five-retry controller is still to build |
| Task network destinations | None intended; provider enforcement pending |

**Configuration precedence**

- The versioned Excel profile wins over model, reasoning, tracing, limit and
  destination settings in the environment or `.env`.
- Credentials, trace project, timezone and snapshot ID still come from the usual
  process environment, then `.env`, then applicable defaults.
- The `local` profile retains its existing defaults and environment behavior.
- Change the profile version when changing the trial baseline. Freeze the actual
  image and effective settings before comparing the three benchmark runs.
- An empty destination tuple is not proof of blocked network access. The benchmark
  execution gate stays closed until its required safeguards are implemented.

**Run evidence**

Each runner invocation stores a secret-free configuration manifest in
`.state/worklog.sqlite`, under the run's `details.configuration`. Once the graph
is built, a `harness_configuration` event records delegation policy, the computed
framework compaction defaults, summary-prompt hash and summarizer model. These
records describe configuration; they do not establish successful execution or
complete API cost accounting. Historical runs keep their original records.

**Benchmark reference scope and owner maintenance**

- `/memories/` maps to `references/excel-benchmark/memory/`, with procedural
  guidance only. The older company profile is not mounted in this scope.
- `/skills/` exposes only `file-delivery-validation` and `csv-analysis` from the
  existing approved skill folders. No duplicate skill implementations are needed.
- Keep business facts in the task inputs. Keep evaluator answers outside all
  agent-readable reference routes and task folders.
- To correct shared guidance, edit the selected Markdown source as the owner,
  review/commit the change, restart the runner and use a fresh benchmark thread.
  Record the new reference hashes and re-evaluate affected behavior.
- To remove guidance, remove its source/route as the owner and start a fresh thread.
  Existing checkpoints and traces may still contain the old content; removing a
  reference does not erase those records. The retention/deletion procedure for
  those records remains BUILD-05 work.

No tests or paid runs have been performed for this increment. Graph tool absence,
reference isolation and configuration recording still need evaluation.

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
