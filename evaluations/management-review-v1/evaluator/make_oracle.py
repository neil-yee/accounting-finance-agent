"""Build the independent management review oracle from the frozen CSV inputs."""
from collections import defaultdict
import csv
import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "agent-inputs"
OUT = Path(__file__).resolve().parent / "oracle.json"
DEPARTMENTS = ["Strategy Advisory", "Implementation Services", "Data & Analytics"]
MONTHS = ["January 2026", "February 2026"]
CATEGORIES = ["Revenue", "Direct costs", "Payroll", "Marketing", "Software", "Consulting", "Interest", "Income tax"]
CAT_KEYS = {
    "Revenue": "revenue", "Direct costs": "direct_costs", "Payroll": "payroll",
    "Marketing": "marketing", "Software": "software", "Consulting": "consulting",
    "Interest": "interest", "Income tax": "income_tax",
}


def dec(value):
    return Decimal(value.strip())


def csv_rows(name):
    with (INPUTS / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def add_metric(metrics, key, value, *, formula=False, unit="USD"):
    metrics[key] = {"value": "N/A" if value is None else str(value), "formula_required": formula, "unit": unit}


def main():
    actual_rows = csv_rows("department_actuals.csv")
    budget_rows = csv_rows("february_budget.csv")
    project_rows = csv_rows("project_monthly.csv")
    actual, budget, projects = {}, {}, {}
    for row in actual_rows:
        key = (row["Month"], row["Department"], row["Category"])
        if key in actual:
            raise ValueError(f"Duplicate actual row: {key}")
        actual[key] = dec(row["Amount_USD"])
    for row in budget_rows:
        key = (row["Budget_Month"], row["Department"], row["Category"])
        if key in budget:
            raise ValueError(f"Duplicate budget row: {key}")
        budget[key] = dec(row["Amount_USD"])
    for row in project_rows:
        key = (row["Month"], row["Department"], row["Project"])
        if key in projects:
            raise ValueError(f"Duplicate project row: {key}")
        projects[key] = (dec(row["Revenue_USD"]), dec(row["Direct_Cost_USD"]))

    expected_actual = {(m, d, c) for m in MONTHS for d in DEPARTMENTS for c in CATEGORIES}
    expected_budget = {(MONTHS[1], d, c) for d in DEPARTMENTS for c in CATEGORIES}
    if set(actual) != expected_actual:
        raise ValueError(f"Actual input incomplete or unexpected; missing={sorted(expected_actual-set(actual))}; extra={sorted(set(actual)-expected_actual)}")
    if set(budget) != expected_budget:
        raise ValueError(f"Budget input incomplete or unexpected; missing={sorted(expected_budget-set(budget))}; extra={sorted(set(budget)-expected_budget)}")
    project_names = sorted({p for _, _, p in projects})
    if len(project_names) != 6:
        raise ValueError(f"Expected six projects, found {len(project_names)}")
    project_dept = {}
    for month, department, project in projects:
        old = project_dept.setdefault(project, department)
        if old != department:
            raise ValueError(f"Project assigned to multiple departments: {project}")
    expected_project_keys = {(month, department, project) for project, department in project_dept.items() for month in MONTHS}
    if set(projects) != expected_project_keys:
        raise ValueError(f"Project input incomplete or unexpected; missing={sorted(expected_project_keys-set(projects))}; extra={sorted(set(projects)-expected_project_keys)}")
    for month in MONTHS:
        for department in DEPARTMENTS:
            entries = [(p, values) for (m, d, p), values in projects.items() if m == month and d == department]
            if len(entries) != 2:
                raise ValueError(f"Expected two projects for {department}, {month}; found {len(entries)}")
            for category, idx in (("Revenue", 0), ("Direct costs", 1)):
                total = sum((vals[idx] for _, vals in entries), Decimal(0))
                if total != actual[(month, department, category)]:
                    raise ValueError(f"Project tie failed: {month}/{department}/{category}: {total} != {actual[(month, department, category)]}")

    metrics = {}
    scopes = [("consolidated", None)] + [(f"department:{d}", d) for d in DEPARTMENTS]
    periods = [(m, "actual") for m in MONTHS] + [("February 2026", "budget")]

    def raw(scope_dept, period, category):
        source = budget if period == "budget" else actual
        month = "February 2026" if period == "budget" else period
        return sum((source[(month, d, category)] for d in (DEPARTMENTS if scope_dept is None else [scope_dept])), Decimal(0))

    def pnl(scope_dept, period):
        rev = raw(scope_dept, period, "Revenue")
        direct = raw(scope_dept, period, "Direct costs")
        gross = rev - direct
        opex = sum((raw(scope_dept, period, c) for c in ("Payroll", "Marketing", "Software", "Consulting")), Decimal(0))
        operating = gross - opex
        interest = raw(scope_dept, period, "Interest")
        pretax = operating - interest
        tax = raw(scope_dept, period, "Income tax")
        net = pretax - tax
        result = {"revenue": rev, "direct_costs": direct, "gross_profit": gross,
                  "payroll": raw(scope_dept, period, "Payroll"), "marketing": raw(scope_dept, period, "Marketing"),
                  "software": raw(scope_dept, period, "Software"), "consulting": raw(scope_dept, period, "Consulting"),
                  "total_operating_expenses": opex, "operating_income": operating, "interest": interest,
                  "pretax_income": pretax, "income_tax": tax, "net_income": net,
                  "gross_margin": gross / rev if rev else None, "net_margin": net / rev if rev else None}
        return result

    pnl_values = {}
    for scope, dept in scopes:
        for period, kind in periods:
            values = pnl(dept, "budget" if kind == "budget" else period)
            pnl_values[(scope, period, kind)] = values
            for metric, value in values.items():
                add_metric(metrics, f"pnl/{scope}/{period}/{kind}/{metric}", value,
                           formula=metric not in CAT_KEYS.values(), unit="ratio" if metric.endswith("margin") else "USD")

        jan = pnl_values[(scope, "January 2026", "actual")]
        feb = pnl_values[(scope, "February 2026", "actual")]
        bud = pnl_values[(scope, "February 2026", "budget")]
        bridge_items = [("revenue", "revenue", 1), ("direct_costs", "direct_costs", -1),
                        ("payroll", "payroll", -1), ("marketing", "marketing", -1),
                        ("software", "software", -1), ("consulting", "consulting", -1),
                        ("interest", "interest", -1), ("income_tax", "income_tax", -1)]
        for label, actual_key, sign in bridge_items:
            add_metric(metrics, f"bridge/month/{scope}/{label}", (feb[actual_key] - jan[actual_key]) * sign, formula=True)
            add_metric(metrics, f"bridge/budget/{scope}/{label}", (feb[actual_key] - bud[actual_key]) * sign, formula=True)
        add_metric(metrics, f"bridge/month/{scope}/net_income_change", feb["net_income"]-jan["net_income"], formula=True)
        add_metric(metrics, f"bridge/budget/{scope}/net_income_variance", feb["net_income"]-bud["net_income"], formula=True)
        for bridge_key, lhs, rhs in (("month/gross_margin_change", feb, jan), ("month/net_margin_change", feb, jan),
                                     ("budget/gross_margin_variance", feb, bud), ("budget/net_margin_variance", feb, bud)):
            margin = "gross_margin" if "gross" in bridge_key else "net_margin"
            value = None if lhs[margin] is None or rhs[margin] is None else lhs[margin]-rhs[margin]
            add_metric(metrics, f"bridge/{bridge_key.split('/')[0]}/{scope}/{bridge_key.split('/')[1]}", value,
                       formula=True, unit="ratio")

    project_counts = defaultdict(int)
    for (month, department, project), (revenue, direct) in sorted(projects.items()):
        profit = revenue - direct
        project_counts[project] += 1
        for metric, value, formula in (("revenue", revenue, False), ("direct_costs", direct, False),
                                       ("gross_profit", profit, True),
                                       ("gross_margin", profit / revenue if revenue else None, True)):
            add_metric(metrics, f"project/{project}/{month}/{metric}", value, formula=formula,
                       unit="ratio" if metric.endswith("margin") else "USD")

    oracle = {"version": 1, "currency": "USD", "departments": DEPARTMENTS, "months": MONTHS,
              "categories": CATEGORIES, "projects": project_names,
              "bridge_sign_convention": "positive values increase net income; expense increases are negative",
              "metrics": metrics}
    OUT.write_text(json.dumps(oracle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    required = {"version": 1, "key_grammar": "pnl/<consolidated|department:NAME>/<period>/<actual|budget>/<metric>; bridge/<month|budget>/<scope>/<measure>; project/<PROJECT>/<period>/<metric>",
                "ratio_convention": "Oracle ratios are fractions; cell maps may specify ratio_format=percentage_points to compare percent or percentage-point display values.",
                "keys": sorted(metrics)}
    (OUT.parent / "required-metrics.json").write_text(json.dumps(required, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(metrics)} metrics to {OUT}")


if __name__ == "__main__":
    main()
