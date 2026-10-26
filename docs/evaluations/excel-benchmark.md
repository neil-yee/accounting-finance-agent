# Excel benchmark — synthetic two-month working paper

**Version:** 4 · October 26, 2026 · **Status:** v4 technical checks pass on three fresh trials; owner visual/analysis approval recorded for all three exact outputs. See the [follow-up results](test-gate-followup-2026-10-25.md). The [first failed series](test-phase-2026-10-25.md) is retained.

Business inputs and reference answers below are unchanged. Versioned [v4 task assets](../../evaluations/excel-v4/) clarify reusable helper use, percentage-point units, source grounding and accurate uncertainty statements. The rubric, all-three-pass requirement and owner review remain in force.

Supports [spec §3.2](../agent-spec.md#32-starter-evaluation-tasks), C9 + C1–C7, SC-1–SC-4/SC-7 and E-ART-1 with applicable foundation checks.

This is the evaluator's fixture and rubric. When preparing agent inputs, supply only the input table, business notes and task/output requirements. Keep the reference answers and grader records outside the agent's accessible workspace. Do not load this entire document as an agent skill.

## 1. Fixed inputs

Fictional company: **Harbor Office Supplies & Services**. Periods: January and February 2026. Currency: USD, actual units (not thousands). Accrual-basis illustration; amounts are supplied assumptions, not tax or statutory reporting calculations. Revenue, cost of sales and expenses are positive input amounts. Subtract costs and expenses in the statements.

| Classification | Category | January | February | Note ID |
|---|---|---:|---:|---|
| Revenue | Product sales | 50,000 | 60,000 | N1 |
| Revenue | Service revenue | 10,000 | 12,000 | N2 |
| Cost of sales | Product costs | 30,000 | 33,000 | — |
| Cost of sales | Service delivery costs | 4,000 | 4,800 | — |
| Operating expense | Payroll | 10,000 | 10,500 | N3 |
| Operating expense | Rent | 3,000 | 3,000 | — |
| Operating expense | Utilities | 600 | 750 | — |
| Operating expense | Marketing | 2,000 | 2,600 | — |
| Operating expense | Software | 400 | 400 | — |
| Operating expense | Consulting | 0 | 1,200 | N4 |
| Operating expense | Other operating expense | 0 | 0 | — |
| Finance expense | Interest | 200 | 180 | N5 |
| Tax expense | Income tax | 1,500 | 2,300 | N6 |

**Business notes supplied to the agent**

- **N1:** A product price increase took effect in February. Unit volumes and the price/volume split are not supplied.
- **N2:** A new service retainer began in February. Its separate revenue contribution is not supplied.
- **N3:** February payroll includes a $500 salary adjustment; no headcount change occurred.
- **N4:** February consulting is a one-off $1,200 expense for a process review.
- **N5:** Interest fell by $20 following a scheduled loan repayment. A loan balance schedule is not supplied.
- **N6:** Income tax is a supplied illustrative expense. Do not infer a statutory rate or recompute tax liability.
- No other causal explanations are supplied. Unchanged amounts and observed movements can be described, but causes must not be invented.

## 2. Calculation contract

- Revenue = product sales + service revenue; cost of sales = product costs + service delivery costs.
- Gross profit = revenue − cost of sales; operating profit = gross profit − operating expenses.
- Pretax profit = operating profit − interest; net income = pretax profit − supplied income tax.
- Month change = February − January. Percentage change = change / January; where January is zero, show **N/A** with a zero-base explanation. This applies to both consulting and the zero/zero other-expense row.
- Gross/net margin = gross profit/net income divided by total revenue. Compare margins in **percentage points**; label them separately from percentage changes.
- Statement totals, variances and margins must use formulas linked to the input cells. Calculate using unrounded values. Display currency with two decimals and percentages/percentage-point movements with two decimals.
- Compare recalculated numeric amounts with independent answers within $0.01 and ratios within 0.000001 in fractional units. Displayed numbers must match rounding to two decimals. Use decimal arithmetic for the independent oracle; do not copy the workbook's formulas as the only check.

## 3. Evaluator reference answers — do not supply to the agent

| Measure | January | February | Amount change |
|---|---:|---:|---:|
| Revenue | 60,000.00 | 72,000.00 | 12,000.00 |
| Cost of sales | 34,000.00 | 37,800.00 | 3,800.00 |
| Gross profit | 26,000.00 | 34,200.00 | 8,200.00 |
| Operating expenses | 16,000.00 | 18,450.00 | 2,450.00 |
| Operating profit | 10,000.00 | 15,750.00 | 5,750.00 |
| Pretax profit | 9,800.00 | 15,570.00 | 5,770.00 |
| Net income | 8,300.00 | 13,270.00 | 4,970.00 |

- Gross margin: **43.33% → 47.50%**, up **4.17 percentage points**.
- Net margin: **13.83% → 18.43%**, up **4.60 percentage points**.
- Revenue growth: **20.00%**. Net-income growth: **59.88%**.
- Profit-change bridge: revenue +12,000; cost of sales −3,800; operating expenses −2,450; interest +20; tax −800 = **+4,970**.
- Product price and service-retainer notes support possible explanations, not a quantified attribution of the whole revenue increase.

## 4. Acceptance rubric

Every required row must pass on each of the three runs. Cosmetic wording/style can differ; material failures cannot be averaged away.

| Check | Pass condition | Grader |
|---|---|---|
| File and structure | Opens as XLSX; exactly the four sheets Inputs, Income Statements, Analysis, Checks; source fixture unchanged. | Code |
| Calculations | Every category, subtotal, total, variance and margin matches the oracle; valid formula references and explicit zero-base handling. | Code |
| Recalculation | Final file retains formulas and contains correct cached results; reopen in formula mode and value mode. No required error/blank cached cells. | Code after real recalculation |
| Detailed analysis | Covers every supplied revenue/cost/expense category, both margins, and the profit bridge; unchanged and zero-base rows addressed. | Code for coverage/numbers + human meaning review |
| Grounding | All explanations trace to notes or calculations; unexplained drivers and unavailable information are identified. No invented volume split, tax rate or loan balance. | Human |
| Professional presentation | Clear title/periods/USD/synthetic label; consistent headings/subtotals, number formats and alignment; inputs/formulas distinguished by labels or legend, not color alone. | Code + human |
| Readability | No clipped/overlapping text or #### cells; body text at least 10 pt; wrapped narrative; consistent restrained styling. Each sheet has sensible print area/page breaks, one page wide with additional vertical pages as needed. | Human inspecting rendered pages |
| Checks and honesty | Checks sheet reconciles statements and variances; actual checks and exceptions identified. Self-reported checks agree with independent evaluation. | Code + human |
| Delivery and limits | Final workbook/supporting work preserved locally after sandbox cleanup; supplied-data-only boundary, time/API limits and retry rules honored. | Code/log review |

**Evidence:** workbook, build script, independent grader result, recalculation log, rendered page previews, trace/run/configuration identifiers, timing/usage/cost record, and the owner's visual/analysis review. Rendering PDF/PNG files are evaluation evidence, not an additional Word/PDF business deliverable.

Run three fresh threads/workspaces with the same frozen inputs, prompt, configuration and tools. Never silently replace a failed run with a successful one; record the outcome. Changes to configuration or fixture start a separately labeled series.
