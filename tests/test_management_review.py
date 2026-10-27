import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evaluations" / "management-review-v1" / "evaluator"))
import grade_management_review as grader
import make_oracle


class ManagementReviewOracleTests(unittest.TestCase):
    def _fixture_bytes(self):
        return {name: (make_oracle.INPUTS / name).read_bytes() for name in
                ("department_actuals.csv", "february_budget.csv", "project_monthly.csv")}

    def test_known_consolidated_and_project_values(self):
        oracle_path = make_oracle.OUT
        oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
        metrics = oracle["metrics"]
        expected = {
            "pnl/consolidated/January 2026/actual/revenue": "230000",
            "pnl/consolidated/January 2026/actual/net_income": "-58500",
            "pnl/consolidated/February 2026/actual/revenue": "258000",
            "pnl/consolidated/February 2026/actual/net_income": "-80300",
            "pnl/consolidated/February 2026/budget/revenue": "267000",
            "pnl/consolidated/February 2026/budget/net_income": "-60000",
            "project/Cedar Market Entry/February 2026/gross_profit": "-3000",
        }
        for key, value in expected.items():
            self.assertEqual(metrics[key]["value"], value, key)

    def _temp_input_copy(self, temp):
        root = Path(temp) / "inputs"
        root.mkdir()
        for name in ("department_actuals.csv", "february_budget.csv", "project_monthly.csv"):
            shutil.copy(make_oracle.INPUTS / name, root / name)
        return root

    def _run_oracle_with_temp_inputs(self, input_dir, temp):
        with patch.object(make_oracle, "INPUTS", input_dir), patch.object(make_oracle, "OUT", Path(temp) / "oracle.json"):
            make_oracle.main()

    def test_duplicate_actual_row_rejected_without_touching_fixture(self):
        frozen = self._fixture_bytes()
        with tempfile.TemporaryDirectory() as temp:
            input_dir = self._temp_input_copy(temp)
            path = input_dir / "department_actuals.csv"
            original = path.read_text(encoding="utf-8")
            with path.open("a", encoding="utf-8") as stream:
                stream.write(original.splitlines()[1] + "\n")
            with self.assertRaisesRegex(ValueError, "Duplicate actual row"):
                self._run_oracle_with_temp_inputs(input_dir, temp)
        self.assertEqual(self._fixture_bytes(), frozen)

    def test_project_tie_error_rejected(self):
        frozen = self._fixture_bytes()
        with tempfile.TemporaryDirectory() as temp:
            input_dir = self._temp_input_copy(temp)
            path = input_dir / "project_monthly.csv"
            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
                fields = list(rows[0])
            rows[0]["Revenue_USD"] = str(int(rows[0]["Revenue_USD"]) + 1)
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "Project tie failed"):
                self._run_oracle_with_temp_inputs(input_dir, temp)
        self.assertEqual(self._fixture_bytes(), frozen)


class ManagementReviewGraderTests(unittest.TestCase):
    def test_decimal_value_parses_positive_and_negative_numbers(self):
        self.assertEqual(grader.decimal_value(8500), Decimal("8500"))
        self.assertEqual(grader.decimal_value(-.023), Decimal("-.023"))

    def _output(self, root, revenue=230000):
        path = Path(root) / "working-paper.xlsx"
        workbook = openpyxl.Workbook()
        workbook.active.title = "Summary"
        workbook.active["A1"] = revenue
        workbook.save(path)
        return path

    def test_valid_single_cell_reference_reads_cached_value(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "output"
            folder.mkdir()
            self._output(folder)
            cell_map_path = Path(temp) / "map.json"
            cell_map_path.write_text(json.dumps({"metrics": {
                "pnl/consolidated/January 2026/actual/revenue": {"sheet": "Summary", "cell": "A1"}
            }}), encoding="utf-8")
            with patch.object(grader, "validate_delivery", return_value={"errors": [], "workbook": "working-paper.xlsx"}):
                report = grader.grade(folder, cell_map_path)
            self.assertEqual(report["checked_metrics"], 1)
            self.assertFalse(any("Numeric value missing" in e for e in report["errors"]))
            self.assertFalse(any("Incorrect pnl/consolidated/January 2026/actual/revenue" in e for e in report["errors"]))

    def test_wrong_single_cell_value_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "output"
            folder.mkdir()
            self._output(folder, revenue=230001)
            cell_map_path = Path(temp) / "map.json"
            cell_map_path.write_text(json.dumps({"metrics": {
                "pnl/consolidated/January 2026/actual/revenue": {"sheet": "Summary", "cell": "A1"}
            }}), encoding="utf-8")
            with patch.object(grader, "validate_delivery", return_value={"errors": [], "workbook": "working-paper.xlsx"}):
                report = grader.grade(folder, cell_map_path)
            self.assertTrue(any("Incorrect pnl/consolidated/January 2026/actual/revenue" in e for e in report["errors"]))

    def test_ranges_are_rejected_as_cell_references(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "output"
            folder.mkdir()
            self._output(folder)
            cell_map_path = Path(temp) / "map.json"
            cell_map_path.write_text(json.dumps({"metrics": {
                "pnl/consolidated/January 2026/actual/revenue": {"sheet": "Summary", "cell": "A1:B2"}
            }}), encoding="utf-8")
            with patch.object(grader, "validate_delivery", return_value={"errors": [], "workbook": "working-paper.xlsx"}):
                report = grader.grade(folder, cell_map_path)
            self.assertTrue(any("one A1 cell" in e for e in report["errors"]))

    def test_malformed_map_and_missing_output_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            malformed = Path(temp) / "map.json"
            malformed.write_text("[]", encoding="utf-8")
            with patch.object(grader, "validate_delivery", return_value={"errors": [], "workbook": "working-paper.xlsx"}):
                report = grader.grade(temp, malformed)
            self.assertTrue(any("top level must be a JSON object" in e for e in report["errors"]))
            missing = grader.grade(Path(temp) / "does-not-exist")
            self.assertTrue(missing["errors"])
            self.assertTrue(any("Exactly one final working-paper.xlsx" in e for e in missing["errors"]))


if __name__ == "__main__":
    unittest.main()
