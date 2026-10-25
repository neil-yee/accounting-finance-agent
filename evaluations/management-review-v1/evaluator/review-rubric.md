# Management review human review rubric

Numerical grading is separate. Review the workbook and its sibling PDF for:

- Clear January/February actuals and February budget, in USD, with a stated budget variance sign convention.
- Consolidated results and all three departments; all six projects, with project profit equal to revenue less direct cost.
- Gross and net margins shown as percentages; zero revenue bases shown as N/A. Keep percentage-point changes distinct from dollar changes.
- A readable month-over-month and actual-versus-budget bridge that reconciles to net income changes.
- Notes N1–N4 used accurately: Cedar's moved acceptance milestone and loss, Strategy payroll additions, the one-time Data & Analytics consulting review, and the unexplained software increase. Do not invent explanations for other movements.
- Conclusions distinguish observed facts from interpretations and name material management follow-ups.
- PDF tables, labels, numbers, and page breaks are legible and agree with the workbook. Confirm the rendered page images show the same content.

## Cell map

The host grader accepts `OUTPUT_FOLDER [CELL_MAP.json]`. The map has a `metrics` object keyed by IDs copied from `required-metrics.json`, for example:

```json
{
  "metrics": {
    "pnl/consolidated/January 2026/actual/revenue": {
      "sheet": "Income Statements",
      "cell": "B5"
    },
    "pnl/consolidated/January 2026/actual/gross_margin": {
      "sheet": "Income Statements",
      "cell": "B7",
      "ratio_format": "fraction"
    }
  }
}
```

Metric keys use `pnl/<scope>/<period>/<actual|budget>/<metric>`, `bridge/<month|budget>/<scope>/<measure>`, and `project/<project>/<period>/<metric>`. Scope is `consolidated` or `department:<exact department name>`. Expense bridge keys mean signed impact on net income: reverse the ordinary expense-variance sign; revenue retains its sign. Margin bridge keys are percentage-point movements expressed as fractional ratios. Oracle ratios are fractions; use `ratio_format: "fraction"` when the cached cell stores 0.42 for 42%, or `"percentage_points"` when it stores 42. Zero-base margins must be `N/A` (either accepted text capitalization or an em dash). Omit `ratio_format` for USD values. All required keys must be mapped; derived oracle metrics must point to formula cells.
