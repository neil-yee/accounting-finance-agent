

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
