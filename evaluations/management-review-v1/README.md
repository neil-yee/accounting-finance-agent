# Management review — fictional multi-source case

Northstar Consulting Group, January/February 2026, USD. Three departments and six
projects; monthly actual P&L, February budget, project contribution and explanatory
notes. Inputs are synthetic and are not accounting/tax evidence for a real entity.

## Agent inputs

Copy only `agent-inputs/` into a fresh thread workspace. `required-metrics.json`
contains metric names, not expected numbers. The task asks for formula-driven
Excel, a separate professional PDF, recalculation/rendering evidence and a cell
map linking required metrics to workbook cells. Negative/zero comparison bases
use N/A for percentage change; widening losses are described in absolute terms.
Project contribution excludes unallocated internal payroll and overhead.

## Independent evaluation

Keep `evaluator/` on the host, outside the agent-readable routes/workspace.
Generate answers independently with Decimal arithmetic:

```sh
uv run --locked python evaluations/management-review-v1/evaluator/make_oracle.py
uv run --locked python scripts/grade_management_review.py WORKSPACE WORKSPACE/final/cell-map.json
```

The generator validates source completeness/uniqueness and project-to-department
ties. The grader reads cached workbook cells and formula markers independently;
it does not trust numbers reported in the agent's cell map. Keep source hashes
and separately compare the source files after execution. Grader success covers
numeric checks and required coverage, not narrative accuracy or presentation.
Review the PDF, grounded explanations, zero/negative-base handling and formula
meaning using `evaluator/review-rubric.md`.

This case extends the simpler Excel fixture. One demonstration does not replace
the selected three-run benchmark or authorize deployment/business use.
