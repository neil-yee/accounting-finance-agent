# Test gate follow-up — October 25–26, 2026

**Result:** all technical checks pass for the selected synthetic Excel scope. The owner approved all three exact final output manifests on October 26, 2026; the **selected foundation Test gate is met**. This is not a release approval or evidence of general accounting reliability.

This continues the [first Test report](test-phase-2026-10-25.md). Failed trials and exploratory evidence are retained. The [machine-readable summary](test-gate-followup-2026-10-25.json) records the frozen configuration, asset identities, run IDs and results.

## 1. What changed and why

| Finding | Change | Verification |
|---|---|---|
| Rewriting spreadsheet code consumed the request/tool/dollar budgets. | Added a reusable [financial working-paper skill](../../skills/financial-working-paper/SKILL.md) with generic build/validation helpers. The host stages approved helpers before the run. | Helpers operate on supplied category/classification rows and metadata. No company values or evaluator answers are embedded. Three frozen trials finish inside the unchanged limits. |
| Margin differences and narrative layout needed clearer handling. | Numeric percentage-point deltas, explicit units, minimum 10 pt body text, wrapped commentary and deliberate page breaks. | Independent recalculation, 133 formula caches per workbook, numeric/format graders and rendered-page review. |
| A correct number could still have an unsupported explanation. | Separate observed movements from causal attribution; quote supplied notes and identify unquantified contributions. | v2 Trial 1 failed grounding; a separately frozen v3 series passed, but another v3 repetition exposed an inaccurate uncertainty claim. v4 clarifies that disclosed amounts must be acknowledged, with no generic caveat on every row. |
| Summarization could multiply the HTTP retry policy. | The strict profile's pinned summarizer uses the budgeted model directly; BudgetClient owns retries. | Integrated failure test observes one summary invocation and six HTTP attempts: initial attempt plus five retries. |
| Nonempty partial Responses output could appear complete. | Reject any explicit response status other than `completed`; preserve artifacts and record failure/recovery. | Parameterized offline cases cover incomplete/output-limit, failed, cancelled, queued and in-progress responses. The final frozen series uses this fix. |
| Context and uncertain-write recovery had evaluation gaps. | Added live context cases and offline integrated runner/checkpoint recovery cases. | Seven context cases pass, including two actual compactions; three recovery cases pass. Scope and rubric corrections are below. |

Approved helper copies are hashed with the inputs and protected during sandbox export. Existing copies must match the approved version; after a helper change, use a fresh thread. The model supplies source-grounded commentary and invokes the helpers; it is not expected to regenerate their code. Other task types still need suitable procedures and evaluations.

## 2. Evaluation sequence — keep the failures

| Series | Outcome | Interpretation |
|---|---|---|
| v1 `ab515f41-3fe6-419a-85fc-1d9a9fb1196b` | **0/3 complete passes** | Two conservative API reservation stops and one tool ceiling. See the original report. |
| v2 pilot `47a26ca9-8cf1-43f7-9c42-28dc676b9566` | Completed; numeric checks pass | Separate pilot, not one of the three scored trials. 17 requests, 20 tools, 159,275 tokens, $0.143737 conservative model cost. |
| v2 `143f6902-aec5-4176-9473-a5d550d76a63` | Numeric **3/3**; grounding **2/3** | Trial 1 said the price note “attributes the change” to the price increase. The supplied note does not establish that attribution. This series is not an overall pass. |
| v3 before response-status hardening `75cbbd42-9797-4689-ace4-be40e3d97bad` | Numeric **3/3**; assistant grounding and visual review **3/3** | Owner review remains required by the acceptance rubric. No failed trial was replaced inside a series. |
| v3 after response-status hardening `bc92b582-d10f-4846-b56a-4d46b79336a6` | Numeric **3/3**; grounding **2/3** | Trial 1 falsely described a disclosed payroll adjustment as unquantified. Retained as a grounding failure. |
| v4 `df3feccd-26d4-44e0-8c7c-5ae0adfd1edb` | Numeric **3/3**; assistant grounding and visual review **3/3** | Same runtime/helpers/limits; task clarifies that uncertainty statements must also be supported. Owner approval recorded for the three exact manifests. |

v2/v3/v4 retain the original business values, notes and independent numerical answers. Versioned task requirements clarify helper use, percentage-point representation, readable formatting and grounding. This comparison tests the combined changes; it does not isolate the contribution of each change.

### Frozen v4 conditions

- Model: **GPT-6 Luna, high reasoning**, Responses API, Standard/default tier.
- Limits: **40 API requests, 40 tool attempts, 30 minutes work, $1 conservative model API reservation per run**. Separate 60-second preservation/cleanup allowance.
- Tracing enabled; agent delegation disabled. Luna/high subagents assisted implementation and independent review outside the evaluated agent.
- Frozen sandbox snapshot: `3dce6ed0-f050-432a-bc9a-79a7b960972f`; openpyxl 3.1.5 and LibreOffice Calc 26.2.6.3.
- Three fresh threads with identical supplied inputs, prompt, source/configuration identities and tool assets. No intervention during the series.
- Configuration SHA-256: `eb81bdfa86106d9cc268b4ac25972058583d615dbbe2ec6f7abbf4c230764e87`.

The runtime profile is named `excel-benchmark-v3`; the final **task fixture** is v4. The series runner's default fixture was changed to v4 **after** collection. The saved evaluator hash identifies the script actually used; all three collected trials explicitly selected v4. These revisions do not rewrite an earlier baseline. The last v3 series and first v4 trial overlapped in separate processes/threads; their source, approved skills and evaluators stayed unchanged throughout both collections. Only a new fixture directory was added.

### Final trial results

| Trial | Run / trace ID | Duration | Requests / tools | Input / output tokens | Conservative model USD | Technical result |
|---|---|---:|---:|---:|---:|---|
| 1 | `17455321-fd3e-4706-b8e6-537ea3bc2833` | 151.6 s | 15 / 23 | 157,323 / 8,703 | 0.161507 | Pass |
| 2 | `fe735bcd-37f1-404d-a5c2-5f18d0e5617a` | 128.9 s | 17 / 21 | 166,753 / 5,531 | 0.152720 | Pass |
| 3 | `09777156-f80b-4f4a-a54b-dad6c684b3ad` | 155.8 s | 16 / 23 | 173,461 / 9,489 | 0.177541 | Pass |

Total: **521,260 tokens** (497,537 input + 23,723 output); **$0.491768 conservative model cost** across these three runs. Cost uses the host budget ledger and ignores cache discounts; it is not an invoice or total infrastructure/development cost. Request starts include image-token preflights, so they exceed completed inference calls.

### What the output checks established

- Each original XLSX has the required four sheets, unchanged sources, formula links and all 133 required formula caches. No required error/blank cached results.
- Independent LibreOffice recalculation of a **copy** passes the decimal-based reference answers; original delivery hashes remain unchanged.
- Revenue, costs, profits, variances, zero-base handling, margins and the profit bridge agree with independent expectations. Margin movements display **4.17 pp** and **4.60 pp**.
- All 13 categories are covered. Notes N1–N6 are quoted correctly; commentary identifies unquantified sales contributions and avoids invented volume splits, tax rates and loan balances.
- All 24 original rendered pages were reviewed by an assistant. Body text meets the minimum and no material clipping, overlap or `####` was found. Minor layout limitations remain: sparse continuation pages and an isolated bridge section without the larger sheet banner. These remain visible for owner judgment.
- An earlier v3 assistant visual review incorrectly reported missing Trial 3 labels. Full-resolution reinspection and identical page hashes across trials disproved those claims. The original review and corrective addendum are retained locally; this report uses the corrected finding.
- All three source/configuration/provider/snapshot/output/backup/trace walks agree. Exported traces contain 239, 253 and 250 records respectively, with **zero unfinished records**. Sandbox cleanup was requested and API absence was checked separately.
- Four deliberately defective copies are rejected for the intended errors: wrong net income, missing sheet, missing formula cache and changed source. The passing control is a real v4 delivery.

The agent inspected at most two representative previews per task, as directed, and disclosed that limitation. The independent review covered all pages. Assistant reviews are separate from owner approval. After receiving the review pack, the owner explicitly replied “Approve all three outputs” in chat. `WorkLog.review` accepted each unchanged output manifest; all three current review statuses are `approved`. The immutable collection record retains its earlier `pending` field; the subsequent approval record and final summary supply the current status.

## 3. Foundation checks

### Context — TEST-01 / TEST-04

Seven live synthetic cases pass:

- Two missing-input requests: ask for the unavailable data instead of inventing results.
- Two authoritative source corrections: use revised count 13, February 2026 and USD rather than the obsolete draft.
- Two instructions embedded in source text: no requested unauthorized tool effects; approved references unchanged.
- Two successive real compaction cycles within one case: preserve case identity, corrected count, period, currency and work scope. The second cycle does not reintroduce the original fact message.

These are context-only harness probes with an in-memory checkpointer and virtual backend, not full sandbox artifact runs. A test-only 80,000-token input profile forces the real default summarizer trigger; production context settings and summarization prompt are unchanged.

The final probe's initial lexical grade was 6/7 because “superseding” was not recognized as rejection of the obsolete draft. The corrected rubric regraded **all seven unchanged outputs**, with no new API calls, to 7/7. Earlier lexical false failures and original reports remain. Regression tests cover the correction. This is a small selected adversarial set, not a prompt-injection security guarantee.

### Recovery — TEST-06

Three integrated offline cases pass:

1. A compiled agent writes a real local file, loses the tool response and fails honestly. The actual runner's output manifest preserves the file; closing/reopening SQLite and explicitly reconciling resumes without replaying the write.
2. Nonempty partial text with incomplete/output-limit, failed, cancelled, queued or in-progress Responses status records a failed run, preserved earlier output and an accurate recovery boundary. Missing status metadata remains compatible; explicit `completed` is accepted.
3. A real pinned summarization middleware invocation encounters mocked HTTP 503 responses and stops at six total attempts, without a second framework retry layer.

The tests use scripted model responses, local temporary files/SQLite and an HTTP mock. They complement the earlier live budget/tool/abrupt-exit boundary probes; they do not claim fault injection against a live external financial system. One exploratory transport diagnostic accidentally reached the model before isolation was corrected; it is excluded from scored recovery evidence. The final recovery runner and full offline suite report no network attempts.

### Regression and provenance — TEST-03 / TEST-05

- **142 offline tests pass**, zero failures/errors/expected failures and zero network attempts in the engineering runner.
- Existing isolation, transfer, source protection, overlap, exclusion and recovery checks remain passing.
- The current v4 evidence walkthrough passes. A disposable synthetic review rejects changed output hashes; no synthetic approval is applied to a real run.

## 4. Current gate and next stage

| Task | Current assessment |
|---|---|
| TEST-01: context/configuration | Meets completion criterion for selected scope |
| TEST-02: repeated Excel delivery | Meets completion criterion; owner approval recorded |
| TEST-03: files and persistence | Meets completion criterion for selected scope |
| TEST-04: controls and boundaries | Meets completion criterion for selected scope |
| TEST-05: provenance and review | Meets completion criterion for selected scope |
| TEST-06: recovery | Meets completion criterion for selected scope |

The [benchmark acceptance rubric](excel-benchmark.md#4-acceptance-rubric) requires owner visual/analysis review. The owner approved all three outputs in chat on October 26, 2026; exact-hash approval was recorded at `2026-10-26T00:19:28Z`. Rechecking each complete current workspace manifest reports `approved`. Any later artifact revision invalidates that approval and requires relevant rechecks.

Three successful synthetic runs are initial consistency evidence. Broader workflows, unfamiliar source structures and real business use need additional cases. Release planning, stop/recovery rehearsal and release authorization remain separate tasks.

## 5. Reproduction and evidence locations

```bash
# Offline, no model or sandbox calls
uv run --locked python scripts/check_engineering.py
uv run --locked python scripts/evaluate_recovery_cases.py

# Paid model context probes / three paid sandbox trials
uv run --locked python scripts/evaluate_context_cases.py
uv run --locked python scripts/run_excel_series.py --run --assets evaluations/excel-v4

# Download an existing trace, without rerunning its task
uv run --locked python scripts/export_traces.py --trace 17455321-fd3e-4706-b8e6-537ea3bc2833
```

Local evidence (gitignored): `.state/evaluations/excel-df3feccd-26d4-44e0-8c7c-5ae0adfd1edb.json`, `v4-provenance.json` (before approval), `v4-provenance-approved.json`, `v4-owner-approval.json`, `v4-seeded-results.json`, `followup-cleanup.json`, `.state/context-cases/20261025T234417Z-25227111/`, `.state/evaluations/test-recovery-cases.json`, `.state/engineering-checks-latest.txt`, `.state/v4-grounding-review.md`, `.state/v4-visual-review.md` (earlier reviews and corrective addenda also retained). Raw trace exports are under `traces/`; outputs are under `workspace/threads/<thread>/final/`; independent recalculations and backups remain separate.

| Trial | Thread ID |
|---|---|
| 1 | `854cda07-bdcf-4611-8f37-84858692e046` |
| 2 | `78f7ede6-fc20-49d8-a62c-ef3e5326c1a6` |
| 3 | `6789cd43-31d9-45e0-9f06-264c5aaa1884` |
