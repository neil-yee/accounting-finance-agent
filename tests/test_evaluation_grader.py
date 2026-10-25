"""Offline audit regressions for the Excel benchmark's independent grader.

These tests build in-memory workbook views so they neither invoke LibreOffice nor
make model/network calls. Correct cached values are paired with formulas that
reference populated inputs; each negative case mutates only the formula or value
under test.
"""
from decimal import Decimal
import json
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import grade_excel_benchmark  # noqa: E402


class ExcelGraderAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.folder = self.root / "delivery"
        shutil.copytree(ROOT / "evaluations/excel-v1/agent-inputs", self.assets / "agent-inputs")
        (self.assets / "evaluator").mkdir()
        shutil.copy(ROOT / "evaluations/excel-v1/evaluator/oracle.json", self.assets / "evaluator/oracle.json")
        self.folder.mkdir()
        for path in (self.assets / "agent-inputs").iterdir():
            shutil.copy(path, self.folder / path.name)
        (self.folder / "working-paper.xlsx").touch()
        self.formulas = openpyxl.Workbook()
        self.values = openpyxl.Workbook()
        for wb in (self.formulas, self.values):
            wb.active.title = "Inputs"
            wb.create_sheet("Income Statements")
            wb.create_sheet("Analysis")
            wb.create_sheet("Checks")
        oracle = json.loads((self.assets / "evaluator/oracle.json").read_text())
        with (self.assets / "agent-inputs/source.csv").open(newline="") as source:
            source_rows = list(csv.DictReader(source))
        source_categories = {row["Category"] for row in source_rows}
        self.input_row = {row["Category"]: index for index, row in enumerate(source_rows, start=2)}
        self.input_row["Revenue"] = None
        self.input_row["Cost of sales"] = None
        self.input_row["Gross profit"] = None
        self.input_row["Operating expenses"] = None
        self.input_row["Operating profit"] = None
        self.input_row["Pretax profit"] = None
        self.input_row["Net income"] = None
        self.input_row["Gross margin"] = None
        self.input_row["Net margin"] = None
        self.values["Inputs"].append(["Classification", "Category", "January", "February", "Note ID"])
        self.formulas["Inputs"].append(["Classification", "Category", "January", "February", "Note ID"])
        for row in source_rows:
            target_row = self.input_row[row["Category"]]
            rendered = [row["Classification"], row["Category"], int(row["January"]), int(row["February"]), row["Note ID"]]
            self.values["Inputs"].append(rendered)
            self.formulas["Inputs"].append(rendered)

        statement_labels = list(oracle["January"])
        self.statement_row = {label: index for index, label in enumerate(statement_labels, start=1)}
        for row_number, label in enumerate(statement_labels, start=1):
            jan, feb = Decimal(oracle["January"][label]), Decimal(oracle["February"][label])
            if label in source_categories:
                input_row = self.input_row[label]
                jan_formula, feb_formula = f"=Inputs!C{input_row}", f"=Inputs!D{input_row}"
            else:
                jan_formula = self._statement_formula(label, "C")
                feb_formula = self._statement_formula(label, "D")
            self._pair("Income Statements", row_number, label, jan, feb, jan_formula, feb_formula)

        categories = [row["Category"] for row in source_rows]
        self.analysis_row = {}
        for row_number, label in enumerate(categories + ["Gross margin", "Net margin"], start=1):
            self.analysis_row[label] = row_number
            jan = Decimal(oracle["January"][label])
            feb = Decimal(oracle["February"][label])
            change = feb - jan
            pct = "N/A" if jan == 0 else change / jan
            self._analysis_row(row_number, label, jan, feb, change, pct)
        self.values["Analysis"].cell(40, 1, "Profit change bridge")
        self.values["Analysis"].cell(40, 2, 4970)
        self.formulas["Analysis"].cell(40, 1, "Profit change bridge")
        net_income_row = self.statement_row["Net income"]
        self.formulas["Analysis"].cell(40, 2, f"='Income Statements'!C{net_income_row}-'Income Statements'!B{net_income_row}")
        self.values["Checks"]["A1"] = 1
        self.formulas["Checks"]["A1"] = "=Inputs!C2"

    @staticmethod
    def _number(value):
        return float(value) if isinstance(value, Decimal) else value

    def _statement_formula(self, label, month_col):
        formulas = {
            "Revenue": f"=SUM(Inputs!{month_col}2:{month_col}3)",
            "Cost of sales": f"=SUM(Inputs!{month_col}4:{month_col}5)",
            "Gross profit": f"=B{self.statement_row['Revenue']}-B{self.statement_row['Cost of sales']}" if month_col == "C" else f"=C{self.statement_row['Revenue']}-C{self.statement_row['Cost of sales']}",
            "Operating expenses": f"=SUM(Inputs!{month_col}6:{month_col}12)",
        }
        col = "B" if month_col == "C" else "C"
        formulas.update({
            "Operating profit": f"={col}{self.statement_row['Gross profit']}-{col}{self.statement_row['Operating expenses']}",
            "Pretax profit": f"={col}{self.statement_row['Operating profit']}-Inputs!{month_col}{self.input_row['Interest']}",
            "Net income": f"={col}{self.statement_row['Pretax profit']}-Inputs!{month_col}{self.input_row['Income tax']}",
            "Gross margin": f"={col}{self.statement_row['Gross profit']}/{col}{self.statement_row['Revenue']}",
            "Net margin": f"={col}{self.statement_row['Net income']}/{col}{self.statement_row['Revenue']}",
        })
        return formulas[label]

    def _analysis_row(self, row_number, label, jan, feb, change, pct):
        self.values["Analysis"].cell(row_number, 1, label)
        self.formulas["Analysis"].cell(row_number, 1, label)
        statement_row = self.statement_row[label]
        formulas = [f"='Income Statements'!B{statement_row}",
                    f"='Income Statements'!C{statement_row}",
                    f"=C{row_number}-B{row_number}"]
        actuals = [jan, feb, change]
        if "margin" not in label.lower():
            formulas.append("N/A" if pct == "N/A" else f"=D{row_number}/B{row_number}")
            actuals.append(pct)
        for col, (formula, value) in enumerate(zip(formulas, actuals), start=2):
            self.formulas["Analysis"].cell(row_number, col, formula)
            self.values["Analysis"].cell(row_number, col, self._number(value))

    def tearDown(self):
        self.temp.cleanup()

    def _pair(self, sheet, row, label, jan, feb, jan_formula, feb_formula):
        self.values[sheet].cell(row, 1, label)
        self.formulas[sheet].cell(row, 1, label)
        for col, amount, formula in ((2, jan, jan_formula), (3, feb, feb_formula)):
            self.values[sheet].cell(row, col, float(amount))
            self.formulas[sheet].cell(row, col, formula)

    def _grade(self):
        with patch.object(grade_excel_benchmark, "validate_delivery", return_value={"errors": [], "workbook": "working-paper.xlsx"}), \
             patch.object(grade_excel_benchmark.openpyxl, "load_workbook", side_effect=lambda _path, data_only=False: self.values if data_only else self.formulas):
            return grade_excel_benchmark.grade(self.folder, self.assets)

    def test_arbitrary_formula_expressions_with_correct_caches_are_rejected(self):
        """An amount formula must refer to inputs, even when its cache is right."""
        self.formulas["Income Statements"]["B1"] = "=1"
        result = self._grade()
        self.assertFalse(result.get("numeric_pass", False))
        self.assertEqual(self.values["Income Statements"]["B1"].value, 50000)

    def test_hardcoded_profit_bridge_is_rejected_when_cache_is_correct(self):
        """A hardcoded bridge total must fail while its expected cache is correct."""
        self.formulas["Analysis"]["B40"] = 4970
        result = self._grade()
        self.assertFalse(result.get("numeric_pass", False))
        self.assertEqual(self.values["Analysis"]["B40"].value, 4970)

    def test_inputs_sheet_values_are_reconciled_to_frozen_source(self):
        """The grader currently never inspects workbook Inputs cell values."""
        self.values["Inputs"]["C2"] = -999
        result = self._grade()
        self.assertFalse(result.get("numeric_pass", False))

    def test_boolean_numeric_cache_is_rejected_without_crashing(self):
        """Boolean caches should be reported as invalid numeric results."""
        self.values["Income Statements"]["B1"] = True
        try:
            result = self._grade()
        except Exception as exc:  # turn a grader crash into an explicit failure
            self.fail(f"grader crashed instead of reporting an invalid numeric cell: {exc!r}")
        self.assertFalse(result.get("numeric_pass", False))

    def test_incorrect_analysis_change_is_rejected(self):
        """The analysis change field is independently compared to the oracle."""
        self.values["Analysis"]["D1"] = -1
        result = self._grade()
        self.assertFalse(result["numeric_pass"])
        self.assertTrue(any("Incorrect analysis value" in error for error in result["errors"]))

    def test_repeated_category_label_outside_table_does_not_break_valid_analysis(self):
        """A narrative mention must not be treated as another financial data row."""
        self.values["Analysis"]["A50"] = "Interest"
        self.values["Analysis"]["B50"] = -20
        self.values["Analysis"]["C50"] = "Decrease after scheduled repayment"
        self.formulas["Analysis"]["A50"] = "Interest"
        self.formulas["Analysis"]["B50"] = -20
        self.formulas["Analysis"]["C50"] = "Decrease after scheduled repayment"

        result = self._grade()

        self.assertTrue(result["numeric_pass"], result["errors"])

    def test_bridge_heading_and_result_on_following_row_are_accepted(self):
        """A bridge section heading with a labeled result row is a valid layout."""
        self.values["Analysis"]["A33"] = "Profit change bridge"
        self.formulas["Analysis"]["A33"] = "Profit change bridge"
        self.values["Analysis"]["A34"] = "Net income change"
        self.formulas["Analysis"]["A34"] = "Net income change"
        self.values["Analysis"]["B34"] = 4970
        self.formulas["Analysis"]["B34"] = (
            f"='Income Statements'!C{self.statement_row['Net income']}"
            f"-'Income Statements'!B{self.statement_row['Net income']}"
        )

        result = self._grade()

        self.assertTrue(result["numeric_pass"], result["errors"])

    def test_explicit_checks_fail_cell_is_reported_with_coordinate(self):
        """An explicit failed reconciliation must block a numeric pass."""
        self.values["Checks"]["F6"] = "FAIL"
        self.formulas["Checks"]["F6"] = "FAIL"

        result = self._grade()

        self.assertFalse(result["numeric_pass"])
        self.assertIn("Explicit FAIL cell: Checks!F6", result["errors"])


if __name__ == "__main__":
    unittest.main()
