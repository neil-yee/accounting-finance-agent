# Fictional management-review demonstration

October 25, 2026. Northstar Consulting Group, January/February 2026, USD.
This is an assisted demonstration, separate from the selected three-run benchmark.
It does not change Test or Release completion status.

## Case and independent checks

- Three departments, six projects, two months of actuals and a February budget.
- Inputs include four business notes, with some movements deliberately unexplained.
- Deliverables: formula-based Excel working paper and a separate three-page PDF.
- [Frozen source fixture and evaluator](../../evaluations/management-review-v1/README.md).
- The agent received source files and required metric names. Expected values and
  evaluator code stayed outside its workspace.
- GPT-6 Luna/high subagents prepared and independently audited the sources,
  evaluator and subsequent spreadsheet repairs. The accounting agent used the
  same model/reasoning with tracing enabled in the frozen sandbox.

## Attempt history

| Attempt | Profile | Outcome |
|---|---|---|
| Initial task | v1, 20 requests | Created files, then reached the request ceiling. Numeric review found 47 sign-convention/mapping discrepancies and a self-comparing bridge residual formula. |
| Same-thread revision | v1, 20 requests | Saved changes, then stopped because the next context/output reservation could not fit the remaining US$1 budget. It did not reach the request ceiling or execute the revised builder. |
| Fresh-thread execution | v1, 20 requests | Completed with `needs_review`; 292/316 required metrics matched. The monthly department bridge used stale budget row mappings. |
| Reviewed builder execution | v2, 40 requests | A reviewer repaired the generated builder's monthly row map; the accounting agent rebuilt and recalculated it in a fresh sandbox. All 316 required metrics matched independently. |

These are assisted continuations and repairs, not four independent clean passes.
The separate PDF was carried forward after its numbers, text and all three
rendered pages were reviewed. The final execution did not regenerate that report.
Earlier outputs and traces remain available locally and Git-ignored.

## Reviewed package

- Required sheets: Inputs, Income Statements, Analysis, Checks.
- All 316 numeric/coverage checks pass against an independent Decimal oracle;
  derived metrics reference formula cells with recalculated cached values.
- All original source-file hashes are unchanged.
- The corrected bridge residual compares distinct cells (`=C172-C171`) and is zero.
  This replaces the original tautology; the workbook's own PASS flags alone were
  insufficient to detect the earlier defect.
- Workbook self-checks show 294 PASS, zero FAIL, separately from host grading.
- January net loss: $58,500. February net loss: $80,300, versus $60,000 budgeted.
- February revenue: $258,000; gross profit: $108,000. Cedar's February project
  contribution is negative $3,000, before unallocated payroll/overhead.
- PDF figures agree with the workbook. The report identifies supplied explanations
  and leaves the software-cost increase unexplained. Its three rendered pages
  are legible; the longer working-paper printout is supporting material.

The package still requires owner review. Numeric coverage and visual inspection
are evidence for this case, not proof of general financial reliability.

## Request control change

The owner requested more room after the first attempt reached 20 requests.
`excel-benchmark-v2` raises the ceiling to 40. Image-token preflights, retries and
compaction count; the US$1 reservation policy, 600-second work deadline and
40-tool-attempt ceiling are unchanged. The second attempt illustrates why raising
one ceiling cannot prevent stopping at another. New comparisons must use one
fixed baseline. See the [operating guide](../operating-guide.md#versioned-excel-trial-profile).

## Engineering checks

The full offline suite passes **94 tests with zero network attempts**: the prior
85, eight fixture/grader checks, and one profile/request-boundary check. Private
run IDs, detailed tokens/cost reservations, outputs and exported LangSmith traces
are retained in the ignored local records. No owner approval is inferred.
