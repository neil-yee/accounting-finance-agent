---
name: financial-working-paper
description: Build a formula-based, two-month financial working paper from supplied CSV facts and grounded commentary, then recalculate and validate the XLSX.
---

# Two-month financial working paper

Use this procedure for a supplied two-period source table and business notes when the deliverable is a formula-based XLSX working paper. This skill does not contain example-company answers or evaluator data.

## Inputs and boundaries

Read the task, `source.csv`, and `notes.json` before building. Keep those source files unchanged. `source.csv` must have columns `Classification,Category,January,February,Note ID`. Classifications follow the supplied statement contract: Revenue, Cost of sales, Operating expense, Finance expense, or Tax expense. The builder uses category labels and values from the file; it contains no company, period, category, or amount fixture. Revenue and expense inputs are nonnegative; costs and expenses are subtracted in statement calculations.

Write `commentary.json` as an object whose `categories` property maps every exact source Category to concise, agent-written analysis. Every statement must be grounded in the supplied values or notes. Explain observed movement, identify relevant Note IDs when available, and state what cannot be attributed or quantified when the source does not support it. Describe unchanged values. Do not invent drivers, allocations, rates, balances, or operational facts. The builder refuses missing or blank category commentary. Inputs contains only supplied business facts and notes; derived analysis belongs in Analysis. If source columns or classifications do not match the contract, preserve the source and ask the user to clarify or provide a corrected source; do not edit business data to make the builder accept it.

## Keep observations separate from source events

A note that an event occurred does not establish that it caused the whole observed
movement. For every category with a Note ID, quote the relevant supplied note
verbatim in the commentary after the numerical observation. State the supplied
limits on attribution explicitly. Do not replace a note about an event with a
claim that the note attributes or explains the measured change. In particular,
an unquantified price change or new contract does not establish its share of a
revenue movement. For categories without a note, describe only the observed
movement and the absence of a supplied cause. Avoid causal paraphrases; use the
source quotation to carry any relationship the source actually states.

## Build once

Create a staging directory. Run the builder once with the three inputs and a staging output path:

```sh
python /workspace/approved-tools/financial-working-paper/build.py source.csv notes.json commentary.json staging/working-paper.xlsx
```

It creates exactly four sheets in order: Inputs, Income Statements, Analysis, Checks. Inputs preserves source rows. Statements use the source classifications and exact category labels, then calculate Revenue, Cost of sales, Gross profit, Operating expenses, Operating profit, Pretax profit, Net income, Gross margin, and Net margin with formulas. Analysis includes each source category, both margins, month amounts, amount changes, relative changes, grounded commentary, and a net-income change bridge. A zero January base produces N/A for relative change. For margin rows, the amount-change value is a percentage-point amount stored as `100 × (February margin − January margin)` and formatted `0.00 pp`; the adjacent field says `percentage points`. Month margin values remain fractional ratios displayed as percentages. Checks reconcile statement equations and bridge movement with formula-driven PASS/FAIL results.

Do not manually rewrite formulas or make repeated styled builds. If the builder reports malformed or unsupported source data, preserve the original and ask the user for clarification. If it reports missing commentary, complete the agent-written commentary JSON from supplied facts and notes before the one build.

## Recalculate and review

Recalculate only through the approved separate-copy helper, which also renders print-layout evidence. Never save the recalculated file back through openpyxl. For example:

```sh
python /workspace/approved-tools/file-delivery-validation/recalculate.py staging/working-paper.xlsx final/
```

Run the generic validator on the recalculated XLSX:

```sh
python /workspace/approved-tools/financial-working-paper/validate.py final/working-paper.xlsx
```

Analysis keeps numeric columns compact and places grounded narrative in a separate wrapped commentary block. Inputs begins its supplied notes on a deliberate new printed page. Inspect at most two rendered page previews: one statement page and one Analysis page. Check title fit, readable body text (at least 10 pt), wrapping, visible pp units, no clipped content or `####`, and that notes or the bridge heading are not orphaned. The workbook is set to one page wide and paginates vertically. Do not repeatedly render or tune styling.

Keep the final XLSX, supporting commentary, validation result, and rendered evidence in the approved delivery location. The generic validator checks structure, formula caches, formula errors, font sizes, and reconciliation status; it is not a replacement for the independent host evaluator or human review of formula meaning, grounding, and page readability.
