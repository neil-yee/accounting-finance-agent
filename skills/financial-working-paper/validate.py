"""Validate workbook structure, formula caches, checks, and font sizes without an oracle."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from openpyxl import load_workbook

SHEETS = ["Inputs", "Income Statements", "Analysis", "Checks"]


def validate(path: Path):
    path = Path(path)
    errors = []
    formulas = load_workbook(path, data_only=False, read_only=False)
    values = load_workbook(path, data_only=True, read_only=False)
    if formulas.sheetnames != SHEETS:
        errors.append(f"Expected sheets in order {SHEETS}; found {formulas.sheetnames}")
    formula_count = 0
    for ws in formulas.worksheets:
        value_ws = values[ws.title]
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None and cell.font.sz is not None and cell.font.sz < 10:
                    errors.append(f"Font below 10 pt at {ws.title}!{cell.coordinate}")
                if cell.data_type != "f":
                    continue
                formula_count += 1
                cached = value_ws[cell.coordinate]
                if cached.value is None:
                    errors.append(f"Missing formula cache at {ws.title}!{cell.coordinate}")
                elif cached.data_type == "e" or (isinstance(cached.value, float) and not math.isfinite(cached.value)):
                    errors.append(f"Formula error cache at {ws.title}!{cell.coordinate}: {cached.value}")
    if formula_count == 0:
        errors.append("Workbook contains no formulas")
    if "Checks" in formulas:
        status_cells = [values["Checks"][f"D{row}"].value for row in range(5, formulas["Checks"].max_row + 1)]
        if not status_cells or any(status != "PASS" for status in status_cells):
            errors.append("Checks sheet contains a missing or non-PASS reconciliation status")
    report = {"file": path.name, "formula_count": formula_count, "status": "PASS" if not errors else "FAIL", "errors": errors}
    formulas.close()
    values.close()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Recalculated final XLSX")
    args = parser.parse_args()
    report = validate(args.workbook)
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["errors"]))


if __name__ == "__main__":
    main()
