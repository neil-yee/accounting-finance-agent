import csv
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest

from openpyxl import load_workbook

BUILD_MODULE = Path(__file__).resolve().parents[1] / "skills" / "financial-working-paper" / "build.py"
SPEC = importlib.util.spec_from_file_location("financial_working_paper_build", BUILD_MODULE)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
build, read_inputs = BUILDER.build, BUILDER.read_inputs


class FinancialWorkingPaperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source.csv"
        self.notes = self.root / "notes.json"
        self.commentary = self.root / "commentary.json"
        self.output = self.root / "staging" / "paper.xlsx"
        with self.source.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Classification", "Category", "January", "February", "Note ID"])
            writer.writerow(["Revenue", "Custom sales", 1234, 1500, "R1"])
            writer.writerow(["Cost of sales", "Custom materials", 321, 345, ""])
            writer.writerow(["Operating expense", "Custom support", 42, 42, "R2"])
            writer.writerow(["Finance expense", "Custom interest", 9, 8, ""])
            writer.writerow(["Tax expense", "Custom levy", 13, 16, ""])
        self.notes.write_text(json.dumps({"company": "Test entity", "currency": "CAD", "periods": ["P1", "P2"], "notes": "R1 explains a supplied change."}), encoding="utf-8")
        self.commentary.write_text(json.dumps({"categories": {
            "Custom sales": "R1 gives context for the observed change; no amount attribution is supplied.",
            "Custom materials": "The supplied amount changed; no cause is stated.",
            "Custom support": "The supplied amount is unchanged.",
            "Custom interest": "The supplied amount decreased; no cause is stated.",
            "Custom levy": "The supplied amount increased; no rate is inferred.",
        }}), encoding="utf-8")

    def test_dynamic_build_has_formula_linked_sheets_and_pp_unit(self):
        build(self.source, self.notes, self.commentary, self.output)
        formulas = load_workbook(self.output, data_only=False)
        self.addCleanup(formulas.close)
        self.assertEqual(formulas.sheetnames, ["Inputs", "Income Statements", "Analysis", "Checks"])
        self.assertEqual(formulas["Inputs"]["B5"].value, "Custom sales")
        stmt = formulas["Income Statements"]
        statement_text = [cell.value for row in stmt.iter_rows() for cell in row]
        self.assertIn("Custom materials", statement_text)
        self.assertEqual(statement_text.count("Revenue"), 1)
        self.assertTrue(any(cell.data_type == "f" and "Inputs!" in str(cell.value) for row in stmt.iter_rows() for cell in row))
        analysis = formulas["Analysis"]
        labels = [analysis.cell(row, 1).value for row in range(1, analysis.max_row + 1)]
        self.assertIn("Custom support", labels)
        self.assertIn("Gross margin", labels)
        margin_row = labels.index("Gross margin") + 1
        self.assertIn("100*", analysis.cell(margin_row, 4).value)
        self.assertEqual(analysis.cell(margin_row, 5).value, "percentage points")
        self.assertEqual(analysis.cell(margin_row, 4).number_format, '0.00 "pp";[Red](0.00 "pp");0.00 "pp"')
        self.assertIn("Profit change bridge", labels)
        self.assertTrue(str(analysis.cell(labels.index("Profit change bridge") + 1, 2).value).startswith("="))
        check_formulas = [cell.value for row in formulas["Checks"].iter_rows() for cell in row if cell.data_type == "f"]
        self.assertTrue(any(str(formula).startswith("='Analysis'!B") for formula in check_formulas))
        self.assertTrue(any(cell.data_type == "f" for row in formulas["Checks"].iter_rows() for cell in row))
        self.assertEqual(analysis.max_column, 5)
        self.assertIn("Grounded commentary", [analysis.cell(row, 1).value for row in range(1, analysis.max_row + 1)])
        self.assertTrue(all(cell.font.sz is None or cell.font.sz >= 10 for ws in formulas for row in ws.iter_rows() for cell in row if cell.value is not None))

    def test_refuses_missing_category_commentary(self):
        self.commentary.write_text(json.dumps({"Custom sales": "Context."}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing grounded commentary"):
            read_inputs(self.source, self.notes, self.commentary)

    def test_refuses_unrecognized_classification(self):
        text = self.source.read_text(encoding="utf-8").replace("Finance expense,Custom interest", "Other,Custom interest")
        self.source.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsupported classification"):
            read_inputs(self.source, self.notes, self.commentary)


if __name__ == "__main__":
    unittest.main()
