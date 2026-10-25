"""Host-side independent numerical grader for management-review-v1."""
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

import openpyxl

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from accounting_finance_agent.spreadsheets import validate_delivery  # noqa: E402

EVALUATOR = REPO / "evaluations" / "management-review-v1" / "evaluator"


def decimal_value(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("$", "").strip())
    except (InvalidOperation, ValueError):
        return None


def valid_a1_cell(value):
    """Accept one bounded Excel A1 coordinate, never a range or whole row/column."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z]{1,3}[1-9][0-9]*", value):
        return False
    try:
        from openpyxl.utils.cell import coordinate_to_tuple, column_index_from_string
        row, column = coordinate_to_tuple(value.upper())
        return row <= 1_048_576 and column <= 16_384 and column_index_from_string(re.match(r"[A-Za-z]+", value).group()) == column
    except (TypeError, ValueError):
        return False


def grade(folder, cell_map_path=None):
    folder = Path(folder)
    oracle = json.loads((EVALUATOR / "oracle.json").read_text(encoding="utf-8"))
    errors = []
    try:
        delivery = validate_delivery(folder)
    except Exception as exc:
        delivery = {"errors": [f"Output folder could not be inspected: {type(exc).__name__}: {exc}"]}
    errors.extend(delivery.get("errors", []))
    result = {"errors": errors, "missing_coverage": [], "numeric_pass": False,
              "human_review": "pending: narrative grounding, management usefulness, PDF and rendered layout"}
    if not delivery.get("workbook"):
        return result
    path = folder / delivery["workbook"]
    if not cell_map_path:
        result["missing_coverage"] = sorted(oracle["metrics"])
        result["errors"].append("Cell map not supplied; no oracle metrics were evaluated.")
        return result
    try:
        cell_map = json.loads(Path(cell_map_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        result["errors"].append(f"Invalid cell map: {exc}")
        return result
    if not isinstance(cell_map, dict):
        result["errors"].append("Invalid cell map: top level must be a JSON object.")
        return result
    refs = cell_map.get("metrics")
    if not isinstance(refs, dict):
        result["errors"].append("Cell map must contain a metrics object.")
        return result

    required = set(oracle["metrics"])
    result["missing_coverage"] = sorted(required - set(refs))
    unknown = sorted(set(refs) - required)
    if result["missing_coverage"]:
        errors.append(f"Cell map misses {len(result['missing_coverage'])} required oracle metrics.")
    if unknown:
        errors.append(f"Cell map contains {len(unknown)} unknown metric keys.")
    try:
        values = openpyxl.load_workbook(path, data_only=True, read_only=False, keep_links=False)
        formulas = openpyxl.load_workbook(path, data_only=False, read_only=False, keep_links=False)
    except Exception as exc:
        errors.append(f"Workbook could not be opened: {type(exc).__name__}: {exc}")
        return result
    seen_cells = {}
    checked = 0
    try:
        for key, metric in oracle["metrics"].items():
            ref = refs.get(key)
            if ref is None:
                continue
            if (not isinstance(ref, dict) or not isinstance(ref.get("sheet"), str) or
                    not valid_a1_cell(ref.get("cell"))):
                errors.append(f"Invalid cell reference for {key}; expected a sheet and one A1 cell (for example B12).")
                continue
            if set(ref) - {"sheet", "cell", "ratio_format"}:
                errors.append(f"Invalid cell-map fields for {key}; allowed fields are sheet, cell, and ratio_format.")
                continue
            if ref.get("ratio_format", "fraction") not in {"fraction", "percentage_points"}:
                errors.append(f"Unknown ratio_format for {key}; use fraction or percentage_points.")
                continue
            sheet, address = ref["sheet"], ref["cell"]
            if sheet not in values.sheetnames:
                errors.append(f"Missing sheet for {key}: {sheet}")
                continue
            try:
                cached_cell = values[sheet][address]
                formula_cell = formulas[sheet][address]
            except Exception as exc:
                errors.append(f"Invalid cell for {key}: {sheet}!{address} ({exc})")
                continue
            label = f"{sheet}!{address}"
            if label in seen_cells:
                errors.append(f"Cell-map collision: {key} and {seen_cells[label]} both use {label}.")
            seen_cells[label] = key
            checked += 1
            if metric["formula_required"] and formula_cell.data_type != "f":
                errors.append(f"Derived metric must be a formula: {key} at {label}.")
            expected_text = metric["value"]
            actual = cached_cell.value
            if expected_text == "N/A":
                if not (isinstance(actual, str) and actual.strip().upper() in {"N/A", "NA", "—", "-"}):
                    errors.append(f"Zero-base/undefined metric must display N/A: {key} at {label}; got {actual!r}.")
                continue
            actual_number = decimal_value(actual)
            if actual_number is None:
                errors.append(f"Numeric value missing: {key} at {label}; got {actual!r}.")
                continue
            expected = Decimal(expected_text)
            if metric["unit"] == "ratio":
                fmt = ref.get("ratio_format", "fraction")
                if fmt == "percentage_points":
                    expected *= Decimal(100)
                    tolerance = Decimal("0.0001")
                elif fmt == "fraction":
                    tolerance = Decimal("0.000001")
                else:
                    errors.append(f"Unknown ratio_format {fmt!r} for {key}; use fraction or percentage_points.")
                    continue
            else:
                tolerance = Decimal("0.01")
            if abs(actual_number - expected) > tolerance:
                errors.append(f"Incorrect {key} at {label}: expected {expected}, got {actual_number} (tolerance {tolerance}).")
    finally:
        values.close()
        formulas.close()
    result["errors"] = errors
    result["checked_metrics"] = checked
    result["numeric_pass"] = not errors and not result["missing_coverage"]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_folder", type=Path)
    parser.add_argument("cell_map", nargs="?", type=Path, help="JSON {metrics: {oracle-key: {sheet, cell, ratio_format?}}}")
    args = parser.parse_args()
    report = grade(args.output_folder, args.cell_map)
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report["errors"]))
