# Foundation checks under the v5 Excel profile

On November 5, 2026, the selected foundation checks were repeated against the current repository and, where applicable, `excel-benchmark-v5`. These complement the already approved [v5 Excel series](excel-v5-results.md). This is synthetic test evidence, not release approval or a claim of general accounting reliability.

| Area | Result | Scope |
|---|---|---|
| Offline engineering | 150/150 pass; zero network attempts | Fake credentials and blocked network; tests include shared runtime, workspace, controls, grader, and two new clarification-grader checks. |
| Offline recovery | 3/3 pass | Scripted model and transport failures, temporary files and SQLite; includes recovery after a lost response and six-attempt retry ceiling. |
| Live context | 7/7 pass | Real model with v5 settings and tracing; synthetic text, virtual backend and in-memory checkpoint, not a full sandbox run. Includes missing-input clarification, corrections, source injection and two real compaction cycles. |
| Live sandbox boundaries | Pass | Synthetic sandbox probe checked changed/missing source protection, recovery after abrupt process exit, same-thread overlap rejection, network namespace restrictions and credential absence. Probe sandbox deletion was confirmed. |
| Live checkpoint | Pass | Synthetic remote file deletion/recreation, host conflict preservation and sandbox deletion were checked. |
| Provenance and review | Pass for three v5 deliveries | Fixture, configuration, source hashes, saved manifests, provider identity, trace IDs and owner approvals match; a disposable stale-approval probe rejects a changed manifest. All three trial and three evaluator sandboxes were subsequently absent according to the API. |
| Seeded workbook defects | 4/4 detected | Evaluator rejects wrong net income, missing sheet, absent formula cache and changed source using a copy of the first v5 delivery. |

## Clarification evaluator correction

The first full context run reported 5/7. In both missing-input cases the agent called `ask_clarification` and paused, but the older grader inspected only a final text answer. That original result is preserved under `.state/context-cases/20261105T191358Z-b1ca313a/`.

The grader now recognizes a clarification only when the question matches an actual pending checkpoint interrupt and the recorded tool call; it still rejects a response that invents a result. Two offline regression checks cover the new handling. Both affected cases passed targeted reruns, followed by a fresh 7/7 full context run in `.state/context-cases/20261105T191650Z-c61db589/`. This is a new run after a grader correction, not a retroactive alteration of the earlier result.

The four live context runs (initial suite, two targeted reruns and final suite) recorded $0.28912525 total conservative model reservation costs; this is not an invoice or total infrastructure cost. Offline runs used no provider calls.

## Limits and evidence

- A later set of [v5 ceiling probes](v5-live-ceiling-probes-2026-11-05.md) exercised 100 real provider attempts and 100 real sandbox tool calls with scripted model decisions. A 101st was blocked in each respective probe; the tool probe required a test-only higher graph recursion limit because the normal graph stopped after 74 one-tool-per-turn calls. The $1 budget ceiling itself was not deliberately exhausted live.
- Recovery probes do not establish the outcome of unknown external financial actions, and synthetic injection cases do not guarantee security against all attacks.
- Evidence is saved in the gitignored `.state/evaluations/foundation-v5-20261105/`, `.state/live-boundaries/05a20ba207bf/`, `.state/live-checkpoint/f7ef0b258233/`, and the context folders above. The v5 series retains the separate exact-manifest owner approvals.
