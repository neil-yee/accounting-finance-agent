# Offline engineering checks

**Latest result:** 58 tests passed; 0 failures; 0 errors; 0 network connection
attempts. These are engineering results, not financial-quality evaluation scores.

## Run again

After installing the locked project dependencies, from the repository root:

```powershell
uv run --locked python scripts/check_engineering.py
```

Add `--verbose` for individual test names. The runner saves the full latest report
to ignored `.state/engineering-checks-latest.txt`. It substitutes dummy environment
credentials, disables tracing and local .env loading, blocks outbound socket
connections, and treats any attempted connection as failure even if a test catches
the exception. Tests use temporary folders/databases and fake model/sandbox clients.
No paid model or sandbox service calls are made. Initial dependency installation
is separate and may require network access.

## What passed

| Area | Evidence exercised offline |
| --- | --- |
| Workspace transfers | New/changed files, byte integrity, prior versions, conflicts, local deletion protection, path traversal and hidden-file exclusions. |
| Sandbox lifecycle | Cleanup on success, error, Ctrl+C, create/wait/upload failures; retention on download failure; delayed deletion confirmation. |
| Snapshot/network/timeout settings | Selected snapshot and allowlist forwarded to the mocked SDK; execute timeout capped before tool validation and at the backend. A real compiled-graph regression covers a model requesting 120000 seconds. |
| Runtime context | Toronto time/weekday refreshed for requests without mutating the original system message. |
| Operating budgets | Limits block the next call; concurrent tool attempts share the budget; deadline blocks new work. |
| Parent/subagent integration | The real compiled Deep Agents graph, using fake model replies, shares the same middleware budget with its built-in general-purpose subagent. |
| Persistence | Conversation checkpoints restore after closing/reopening temporary SQLite; another thread has a separate conversation. |
| Task workspaces and locks | Separate thread folders, scope restoration after failure, legacy-file preservation, overlapping-run denial and lock release. |
| Memory/skills | Fixture guidance and discovered skills reach the fake model's system message; approved-file routes reject mutations. |
| Binary filename adapter | Source filenames recovered from metadata/tool history; original messages and existing filenames preserved. |
| Work log and review | Records persist after reopening; approvals require successful runs and exact hashes; changes show stale review; failed/other-thread runs cannot be approved. |
| Structural checks | Valid/invalid CSV/JSON, Office package parts and formula-cache limitations. |
| Runner orchestration | Uses run context/policy, records outcomes, blocks malformed-output success and does not automatically replay failed work. |

## Fixes made during this pass

- The review backend now rejects decision labels other than `approved` and
  `rejected`, preventing malformed review events from being recorded.
- WorkLog accepts an optional database path, so tests do not touch the real work
  log. The existing exit test also mocks local setup rather than creating live state.
- The reusable test runner adds the project root to its import path so local
  helper-script imports work when launched as a script.
- New assertions use the installed backend's ReadResult and inspect the fake
  model's actual prompt for memory/skills, because those state fields are omitted
  from public graph output in the pinned framework version.
- The live smoke run exposed two rejected execute calls requesting 120000 seconds.
  The timeout cap previously ran only after tool validation. Both synchronous and
  asynchronous middleware paths now cap integer timeout requests before validation;
  the backend cap remains in place. Runtime instructions explicitly state seconds.
  Regression checks cover the compiled synchronous tool path and argument copying.

## First live smoke result

User-run task `4b5fa1d2-5cda-4ce2-9af9-34cb75f008cf`, thread
`8771addf-d819-4990-aee2-dd66b9b999d2`, completed successfully after two rejected
timeout arguments and a successful third execute call. The checkpointed messages
and work log were inspected locally. Independent inspection of the preserved CSV
and JSON confirmed three data rows and an exact Decimal total of `14.24`.

The run used the configured snapshot, reported Toronto date/weekday correctly,
loaded skills, preserved both files without conflicts and recorded `needs_review`.
State inspection showed no pending nodes. A subsequent read-only API check confirmed
deletion of `finance-abff96ace8a0`. No model/sandbox run was repeated to assess or
fix this issue; the fix was checked offline and takes effect after restarting the app.

## What this does not establish

The smoke task demonstrates basic provider access, restored-snapshot execution,
file export and cleanup for one run. Allowlist enforcement, third-party library
behavior, recovery against the live API, and GitHub Actions still need live checks.
Fake model replies establish plumbing, not the real model's
ability to select tools, follow skills, or perform accounting correctly.

Bank-reconciliation arithmetic, matching decisions, financial conclusions, Excel
recalculation and rendered document layout still require independent task-quality
evaluations. The next step is a review/revision check, then representative finance
cases with known answers. No finance-quality evaluation was run during these checks.

## October 25 build extension

The expanded suite passes 75 offline tests with zero network attempts. New checks
exercise HTTP-level reservations/retries, deadline interruption, reference scope,
missing formula caches, consistent backups, retention eligibility, namespace
wrapping and four seeded grader defects. Run `uv run --locked python
scripts/check_engineering.py` to reproduce. The ignored current report is in
`.state/engineering-checks-latest.txt`.

Separate live sandbox build checks captured LibreOffice in an immutable snapshot,
blocked DNS/direct IP and network-namespace re-entry, and recalculated/rendered a
small workbook inside that boundary. See [build evidence](build-evidence.json) and
[task progress](task-list.md#11-build-progress). These checks made no model calls
and do not substitute for the three financial benchmark runs or human review.

## Fictional income-statement demonstration

An ad hoc January/February income-statement + analysis workbook and separate
two-page PDF were produced in the frozen sandbox with tracing enabled. This
is separate from the fixed financial benchmark. Two earlier attempts exposed
a repeated-checkpoint filename collision and an unsupported-image request; both
were corrected before the continuation completed with `needs_review` status.

Version preservation now keeps distinct content-addressed prior copies within
one run, and checkpoint exports are serialized. Text-only model requests replace
unsupported media with an explicit limitation while preserving original tool
results for the reviewer. The expanded offline suite passes **80 tests with zero
network attempts**. New regression cases cover repeated checkpoints and media
adaptation without modifying stored messages. Main income-statement arithmetic
and formula caches were independently checked; the PDF pages were inspected.
This demonstration does not establish the formal three-run benchmark or release
readiness. Private outputs, run records and traces remain Git-ignored.

## Image-input extension

The owner enabled image input. Five additional offline checks cover image
pass-through, cached token preflight, invalid/unaffordable counts, remote URL
rejection and preservation of original tool messages. The full suite passes
**85 tests with zero network attempts**. A separate live sandbox run used
`read_file` on a report-preview image, correctly identified its title and monthly
net income, and reported layout observations. No spreadsheet/text extraction was
requested for that check. Provider preflight/image usage is recorded in the work
log; tracing remained enabled. This is a capability check rather than the formal
three-run benchmark or human approval.

## Multi-source case and request ceiling

The full offline suite passes **94 tests with zero network attempts**. Eight new
checks exercise fixture completeness/ties, Decimal answers, and valid/invalid
cell maps including deliberately wrong values. A ninth verifies profile v2 allows
40 request reservations and rejects the 41st without incrementing the counter.

A separate paid management-review demonstration produced Excel/PDF deliverables.
Independent grading exposed errors in generated formulas despite workbook PASS
flags; reviewed repairs now match all 316 required metrics. This is assisted case
evidence, not a formal release pass. See the [assessment](evaluations/management-review.md).
