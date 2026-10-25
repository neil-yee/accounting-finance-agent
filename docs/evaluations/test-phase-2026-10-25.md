# Test phase — October 25, 2026

**Result: the first formal series does not pass.** Three fresh-thread Excel trials
were collected with identical agent inputs, settings, references and source
configuration. No reference answers, corrections or replacement runs were given
to the agent during collection. All outcomes are retained.

## 1. Scope and evaluation method

| Dimension | This evaluation |
|---|---|
| What | Shared context/tools/state/controls, a two-month Excel working paper, source identity, calculations, reconciliation checks, presentation and evidence. |
| Who | Independent code graders; GPT-6 Luna/high subagents for separate audits; Codex assistant for formula/content/visual review. Owner review remains separate and pending. |
| When | Offline synthetic cases; real model/sandbox services for the three trials and bounded live probes. |
| Why | Capability, initial consistency, defect discovery and regression coverage. |

The selected agent was `gpt-6-luna`, high reasoning, Standard/default tier, tracing
on, delegation disabled, profile `excel-benchmark-v3`. Each run had 40 OpenAI
requests, 40 tool attempts, 1,800 seconds of work and a US$1 conservative API
reservation budget, plus separate bounded cleanup. The frozen sandbox was
`3dce6ed0-f050-432a-bc9a-79a7b960972f`.

Only [agent inputs](../../evaluations/excel-v1/agent-inputs/) entered the task
workspace. The Decimal oracle and evaluator stayed outside it. After each run,
the evaluator copied the submitted workbook into a separate sandbox and ran the
repository's fixed LibreOffice helper. It ran no agent-generated Python. The
original artifact was not changed by this second calculation.

## 2. Three-run results

| Trial | Agent work time | Requests / tools | Inference tokens | Stop reason | Corrected independent evaluation |
|---|---:|---:|---:|---|---|
| 1 | 382 s | 29 / 33 | 731,981 | Next request could not fit remaining API reservation budget. | Checked numbers pass before and after independent recalculation. Presentation and stale-default-file findings remain. |
| 2 | 370 s | 28 / 33 | 648,597 | Next request could not fit remaining API reservation budget. | Three composition checks explicitly FAIL (`Checks!E6:E8`); main statement figures agree. Presentation also needs revision. |
| 3 | 390 s | 33 / 40 | 788,186 | Tool-attempt ceiling reached. | Checked numbers and reconciliation checks pass before and after independent recalculation. Presentation needs revision. |

**End-to-end pass: 0/3.** All three stopped as `limited`, before an accepted final
response. Correct numerical output alone does not satisfy completion, delivery,
presentation and review requirements. The 30-minute deadline was not reached.

Total recorded inference usage was **2,168,764 tokens**. Conservative ledger
amounts were $0.6892, $0.6355 and $0.7219; these are upper-bound accounting values,
not invoices. The next request is reserved in advance, so a run can stop before
the ledger reaches $1. Requests include image-token preflights as well as model
attempts. Sandbox/evaluator resources are separate from the model API budget.

All 13 workbook input rows matched the source in each trial. Source files and
saved output manifests matched their recorded hashes. All six trial/evaluator
sandboxes were confirmed absent through the API. All three traces were exported
with zero unfinished records. No real output was approved.

## 3. Findings and repairs

| Finding | Response and evidence |
|---|---|
| Deleting/recreating an output dropped its last-known remote digest, so an untouched host copy appeared to be a conflicting local edit. | Added `advance_baseline()` and connected checkpoint updates to it. Offline regression and a live v1 → delete → v2 probe pass; prior version retained, no false conflict. Genuine host edits still win and incoming versions enter `.conflicts`. |
| Grader treated repeated category words in narrative/bridge sections, and an empty bridge heading, as numeric data rows. | Restricted matching to data-shaped rows and actual bridge results; added regressions. Regraded **every unchanged original workbook and evaluator-recalculated copy**, retaining the original false-failure reports. |
| Grader ignored workbook Inputs contents, literal-only formulas and explicit FAIL statuses; boolean values could crash numeric comparison. | Added selected-fixture source matching, reference-token requirements, FAIL detection and finite numeric type checks. Formula meaning still needs review. |
| Defect seeder could mutate a staging workbook while the grader inspected the final deliverable. | Seeder now resolves the actual delivery. A regression covers staging plus final files. Wrong-net-income mutation now changes only its designated formula/cache. |
| Preserved hidden copies could be mistaken for current deliverables. | Delivery selection excludes hidden version/conflict history, matching workspace policy. Regression added. |
| Probe could lose cleanup coverage if its child failed before the normal recovery block. | Recorded owned resource identity before launch and added timeout/nonzero recovery-or-retain paths, with offline tests. |

The frozen collection was completed **before** product/evaluator repairs were
applied. Original runtime failures remain failures. The new source baseline has
not had a new three-run series; no clean-pass claim is made for it.

A numerically passing delivery copy served as a positive control for four seeded
mutations: wrong net income, missing sheet, missing caches and changed source.
All four are rejected for their intended error classes. Initial seeder checks
that mutated the wrong copy are retained as failed harness evidence. The
missing-sheet mutation also clears caches; its sheet error is asserted separately.

## 4. Presentation and meaning review

- Trial 1: all seven pages reviewed. Grounded notes, correct zero-base handling
  and valid bridge signs; 9pt body narrative, awkward continuation pages and
  percentage signs beside percentage-point wording need correction. The latest
  remote revision was retained as a conflict; the original default artifact was
  evaluated, not silently replaced.
- Trial 2: pages 1, 3, 5, 7 and 9 reviewed, plus full extracted text and workbook
  content. Clipped statement title, orphaned margin rows, 9pt body cells and
  unrelated repeated headers need correction. Three failed checks are visible.
- Trial 3: all seven pages reviewed. Source facts, supplied notes, zero bases and
  bridge agree; a note is orphaned onto a mostly empty page, Analysis text is
  dense, and bridge commentary is confined to narrow columns.
- All trials avoid inventing a price/volume split, separate retainer amount, tax
  rate or loan balance. Margin differences are numerically correct; unit display
  remains awkward. The fixture's fractional-value versus percentage-point display
  convention should be clarified before a new series.

These are assistant assessments, not calibrated human ratings or owner approval.

## 5. Foundation evidence and remaining work

**128 offline tests pass**, with zero failures, errors, expected failures or
network attempts. Compared with the prior 94, 34 added checks cover context,
selected-profile overrides, disabled delegation, compaction plumbing, transfer
boundaries, grader behavior, independent recalculation and live-probe failure
handling. Two pinned middleware compaction cycles use scripted summaries; they
establish framework wiring, not live summary quality.

Live probes additionally established selected network-namespace DNS/direct-IP
failure, denied re-entry to the original network namespace, absence of host API
keys inside the sandbox, protected-source detection, known-output recovery after
abrupt local exit and same-thread overlap rejection. Probe-owned resources were
deleted and their absence confirmed. Two probe startup mistakes were corrected;
the failed allocations and cleanup evidence were retained.

| Task | Assessment | Evidence / remaining work |
|---|---|---|
| TEST-01 | Partial | Skills/todos, profile overrides, disabled delegation, correction persistence and two forced fake-summary cycles pass. Live missing/conflicting-input and correction retention through repeated compaction still need evaluation. |
| TEST-02 | Partial | Three runs, independent recalculation, seeded defects and assistant review recorded. Zero complete passes; a new fixed-baseline series and owner review remain. |
| TEST-03 | Meets completion criterion for selected file/recovery contract | Real temporary-file adversarial checks, transfer/conflict/exclusion/failure cases, checkpoint reopen, overlap rejection, live abrupt-exit recovery and fixed live delete/recreate case. Evidence mixes offline and live cases; it does not establish recovery of unknown external business effects. |
| TEST-04 | Partial | Selected profile, actual provider/tier, shared limits, reference routes, network namespace and sandbox credential absence checked. A complete model-dependent injected/conflicting-instruction case set remains. |
| TEST-05 | Meets completion criterion for selected provenance/review contract | All three input → settings/provider/image → output/hash/backup → trace walks match. Stale approvals rejected in disposable test records. Real owner approval remains absent; reusable-asset promotion is deferred. |
| TEST-06 | Partial | Startup/export/cleanup/incomplete-response/summarizer failure paths exercised offline; live budget/tool stops and known-write recovery recorded. Integrated lost-provider-response recovery and retry behavior across summarizer and transport layers remain. |

## 6. Next experiment

1. Define a short spreadsheet-delivery skill/task procedure with one build,
   recalculation, bounded validation and a small number of visual inspections.
2. Clarify percentage-point display and minimum body text requirements in the
   agent-facing contract. Version the fixture if those requirements change.
3. Verify that the agent can complete within the existing limits, then freeze
   the candidate and collect a new three-run series. Keep all earlier outcomes.
4. Finish context/adversarial/recovery gaps and owner review before considering
   the release gate. No deployment or business-use approval was granted here.

## Reproduce

```sh
uv run --locked python scripts/check_engineering.py
uv run --locked python scripts/run_excel_series.py --run
uv run --locked python scripts/probe_evaluation_boundaries.py
uv run --locked python scripts/probe_evaluation_checkpoint.py
```

The series command makes three paid model/sandbox trials; the probe commands
allocate live sandboxes but make no model calls. `.state/evaluations/` contains
complete series, original grades, corrected regrades, independent calculations,
source/configuration/evaluator hashes, assistant review and provenance records.
`traces/` and task workspaces remain Git-ignored. The public report summarizes
that evidence without committing generated task files.
