"""Build a formula-based two-month working paper from supplied files only."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

REQUIRED_COLUMNS = ["Classification", "Category", "January", "February", "Note ID"]
CLASS_ORDER = ["Revenue", "Cost of sales", "Operating expense", "Finance expense", "Tax expense"]
CLASS_KEY = {name.casefold(): name for name in CLASS_ORDER}
MONEY_FMT = '$#,##0.00;[Red]($#,##0.00);$0.00'
PCT_FMT = '0.00%;[Red](0.00%);0.00%'
PP_FMT = '0.00 "pp";[Red](0.00 "pp");0.00 "pp"'


def _text(value):
    return "" if value is None else str(value).strip()


def read_inputs(source_path: Path, notes_path: Path, commentary_path: Path):
    with source_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(f"source.csv columns must be exactly {REQUIRED_COLUMNS}")
        rows = list(reader)
    if not rows:
        raise ValueError("source.csv has no data rows")
    seen = set()
    for row in rows:
        category, classification = _text(row["Category"]), _text(row["Classification"])
        key = category.casefold()
        if not category or key in seen:
            raise ValueError(f"Missing or duplicate source category: {category!r}")
        seen.add(key)
        if classification.casefold() not in CLASS_KEY:
            raise ValueError(f"Unsupported classification {classification!r} for {category!r}; use {CLASS_ORDER}")
        row["Category"], row["Classification"] = category, CLASS_KEY[classification.casefold()]
        for period in ("January", "February"):
            raw = _text(row[period]).replace(",", "").replace("$", "")
            try:
                number = float(raw)
            except ValueError as exc:
                raise ValueError(f"Invalid {period} amount for {category!r}") from exc
            if number < 0 or not number < float("inf"):
                raise ValueError(f"{period} amount must be finite and nonnegative for {category!r}")
            row[period] = number
        row["Note ID"] = _text(row["Note ID"])
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    commentary = json.loads(commentary_path.read_text(encoding="utf-8"))
    if not isinstance(notes, dict) or not isinstance(commentary, dict):
        raise ValueError("notes.json and commentary.json must contain JSON objects")
    company = _text(notes.get("company"))
    currency = _text(notes.get("currency"))
    periods = notes.get("periods")
    if not isinstance(periods, list) or len(periods) != 2 or not all(_text(p) for p in periods):
        raise ValueError("Reporting periods must be explicitly supplied in notes.json")
    if not company or not currency:
        raise ValueError("Company and currency must be explicitly supplied in notes.json")
    comments = commentary.get("categories", commentary)
    if not isinstance(comments, dict):
        raise ValueError("Commentary categories must be an object")
    missing = [r["Category"] for r in rows if not _text(comments.get(r["Category"]))]
    if missing:
        raise ValueError("Missing grounded commentary for source categories: " + ", ".join(missing))
    return rows, notes, comments, company, currency, [_text(p) for p in periods]


def build(source_path: Path, notes_path: Path, commentary_path: Path, output_path: Path):
    rows, notes, comments, company, currency, periods = read_inputs(source_path, notes_path, commentary_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    inputs, stmt, analysis, checks = wb.active, wb.create_sheet(), wb.create_sheet(), wb.create_sheet()
    inputs.title, stmt.title, analysis.title, checks.title = "Inputs", "Income Statements", "Analysis", "Checks"
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"

    navy, blue, pale, gray = "17365D", "1F4E78", "D9EAF7", "E7E6E6"
    white = "FFFFFF"
    thin_blue = Side(style="thin", color="9EADBA")
    title_font = Font(name="Arial", size=16, bold=True, color=white)
    head_font = Font(name="Arial", size=10, bold=True, color=white)
    body_font = Font(name="Arial", size=10, color="202020")
    section_font = Font(name="Arial", size=10, bold=True, color=navy)
    total_font = Font(name="Arial", size=10, bold=True, color=navy)

    def title(ws, value, subtitle):
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ws.max_column or 4)
        c = ws.cell(1, 1, value)
        c.font, c.fill = title_font, PatternFill("solid", fgColor=navy)
        c.alignment = Alignment(vertical="center")
        ws.row_dimensions[1].height = 28
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ws.max_column or 4)
        s = ws.cell(2, 1, subtitle)
        s.font = Font(name="Arial", size=10, italic=True, color="404040")
        s.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[2].height = 24

    def header(ws, row_num, values):
        for col, value in enumerate(values, 1):
            c = ws.cell(row_num, col, value)
            c.fill, c.font = PatternFill("solid", fgColor=blue), head_font
            c.alignment = Alignment(wrap_text=True, vertical="center")
            c.border = Border(bottom=thin_blue)
        ws.row_dimensions[row_num].height = 32

    def common_layout(ws, widths, area):
        for col, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        ws.sheet_view.showGridLines = False
        ws.freeze_panes = "A4"
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.print_area = area
        ws.page_margins.left = ws.page_margins.right = 0.28
        ws.page_margins.top = ws.page_margins.bottom = 0.4
        ws.oddFooter.center.text = "Synthetic financial working paper | Page &P of &N"
        ws.oddFooter.center.size = 9
        ws.oddFooter.center.font = "Arial"

    # Inputs contain supplied business facts and notes only.
    inputs.append(["Synthetic financial working paper"])
    inputs.append([f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data"])
    header(inputs, 4, REQUIRED_COLUMNS)
    input_rows = {}
    for r in rows:
        line = inputs.max_row + 1
        input_rows[r["Category"]] = line
        inputs.append([r["Classification"], r["Category"], r["January"], r["February"], r["Note ID"]])
    notes_line = inputs.max_row + 2
    inputs.cell(notes_line, 1, "Supplied business notes")
    inputs.cell(notes_line, 1).font = section_font
    for nline in _text(notes.get("notes")).splitlines():
        if _text(nline):
            display_note = re.sub(r"\*\*(.*?)\*\*", r"\1", _text(nline))
            inputs.cell(inputs.max_row + 1, 1, display_note)
            inputs.merge_cells(start_row=inputs.max_row, start_column=1, end_row=inputs.max_row, end_column=5)
            inputs.cell(inputs.max_row, 1).alignment = Alignment(wrap_text=True, vertical="top")
            inputs.row_dimensions[inputs.max_row].height = min(120, max(15, 15 * ((len(display_note) + 99) // 100)))
    for row in inputs.iter_rows(min_row=5, max_row=4 + len(rows)):
        for cell in row:
            cell.font = body_font
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column in (1, 2, 5))
        for cell in row[2:4]:
            cell.number_format = MONEY_FMT
    inputs.merge_cells("A1:E1"); inputs.merge_cells("A2:E2")
    title(inputs, "Source inputs", f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data")
    common_layout(inputs, [24, 31, 17, 17, 14], f"A1:E{inputs.max_row}")
    inputs.print_title_rows = "1:2"
    inputs.row_breaks.append(Break(id=notes_line - 1))

    # Statement with source categories grouped by the supplied classification.
    stmt.append(["Income statement"])
    stmt.append([f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data"])
    header(stmt, 4, ["Line item", periods[0], periods[1], "Basis"])
    stmt.merge_cells("A1:D1"); stmt.merge_cells("A2:D2")
    title(stmt, "Income statement", f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data")
    statement_rows = {}
    class_rows = {}
    for cls in CLASS_ORDER:
        members = [r for r in rows if r["Classification"] == cls]
        if not members:
            continue
        group_line = stmt.max_row + 1
        stmt.cell(group_line, 1, f"{cls} details")
        stmt.cell(group_line, 1).font = section_font
        for r in members:
            line = stmt.max_row + 1
            statement_rows[r["Category"]] = line
            source_line = input_rows[r["Category"]]
            stmt.cell(line, 1, r["Category"])
            stmt.cell(line, 2, f"=Inputs!C{source_line}")
            stmt.cell(line, 3, f"=Inputs!D{source_line}")
            stmt.cell(line, 4, "Source-linked amount")
            class_rows.setdefault(cls, []).append(line)
    def total(label, formula_type):
        line = stmt.max_row + 1
        stmt.cell(line, 1, label)
        for col in (2, 3):
            letter = get_column_letter(col)
            if formula_type == "revenue":
                refs = [f"{letter}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == "Revenue"]
                formula = "=" + ("+".join(refs) or "0")
            elif formula_type == "cos":
                refs = [f"{letter}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == "Cost of sales"]
                formula = "=" + ("+".join(refs) or "0")
            elif formula_type == "opex":
                refs = [f"{letter}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == "Operating expense"]
                formula = "=" + ("+".join(refs) or "0")
            elif formula_type == "finance":
                refs = [f"{letter}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == "Finance expense"]
                formula = "=" + ("+".join(refs) or "0")
            elif formula_type == "tax":
                refs = [f"{letter}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == "Tax expense"]
                formula = "=" + ("+".join(refs) or "0")
            elif formula_type == "gross": formula = f"={letter}{statement_rows['__Revenue__']}-{letter}{statement_rows['__Cost of sales__']}"
            elif formula_type == "operating": formula = f"={letter}{statement_rows['__Gross profit__']}-{letter}{statement_rows['__Operating expenses__']}"
            elif formula_type == "pretax": formula = f"={letter}{statement_rows['__Operating profit__']}-{letter}{statement_rows['__Finance expense__']}"
            elif formula_type == "net": formula = f"={letter}{statement_rows['__Pretax profit__']}-{letter}{statement_rows['__Tax expense__']}"
            elif formula_type == "gross_margin": formula = f"=IF({letter}{statement_rows['__Revenue__']}=0,0,{letter}{statement_rows['__Gross profit__']}/{letter}{statement_rows['__Revenue__']})"
            else: formula = f"=IF({letter}{statement_rows['__Revenue__']}=0,0,{letter}{statement_rows['__Net income__']}/{letter}{statement_rows['__Revenue__']})"
            stmt.cell(line, col, formula)
        statement_rows["__" + label + "__"] = line
        stmt.cell(line, 4, "Formula")
        return line
    rev = total("Revenue", "revenue")
    cos = total("Cost of sales", "cos")
    gross = total("Gross profit", "gross")
    opex = total("Operating expenses", "opex")
    op = total("Operating profit", "operating")
    finance = total("Finance expense", "finance")
    pretax = total("Pretax profit", "pretax")
    tax = total("Tax expense", "tax")
    net = total("Net income", "net")
    # Additional statement margins are formulas linked to statement subtotals.
    gm = total("Gross margin", "gross_margin")
    nm = total("Net margin", "net_margin")
    for line in range(5, stmt.max_row + 1):
        for col in range(1, 5):
            c = stmt.cell(line, col)
            c.font = body_font
            c.alignment = Alignment(vertical="top", wrap_text=True)
        for col in (2, 3): stmt.cell(line, col).number_format = PCT_FMT if line in (gm, nm) else MONEY_FMT
    for line in (rev, cos, gross, opex, op, pretax, net, gm, nm):
        for c in stmt[line]: c.font = total_font; c.border = Border(top=thin_blue)
    common_layout(stmt, [33, 20, 20, 24], f"A1:D{stmt.max_row}")

    # Analysis table: margin amount-change cells store pp; relative-change cell carries unit marker.
    analysis.append(["Month-over-month analysis"])
    analysis.append([f"{company} | {periods[0]} to {periods[1]} | {currency} | Synthetic data"])
    header(analysis, 4, ["Measure", periods[0], periods[1], "Amount change", "Relative change / unit"])
    analysis.merge_cells("A1:E1"); analysis.merge_cells("A2:E2")
    title(analysis, "Month-over-month analysis", f"{company} | {periods[0]} to {periods[1]} | {currency} | Synthetic data")
    analysis_rows = {}
    for r in rows:
        line = analysis.max_row + 1
        analysis_rows[r["Category"]] = line
        sr = statement_rows[r["Category"]]
        analysis.cell(line, 1, r["Category"])
        analysis.cell(line, 2, f"='Income Statements'!B{sr}")
        analysis.cell(line, 3, f"='Income Statements'!C{sr}")
        analysis.cell(line, 4, f"=C{line}-B{line}")
        analysis.cell(line, 5, f'=IF(B{line}=0,"N/A",D{line}/B{line})')
    for measure, statement_key in (("Gross margin", "__Gross margin__"), ("Net margin", "__Net margin__")):
        line = analysis.max_row + 1
        analysis_rows[measure] = line
        sr = statement_rows[statement_key]
        analysis.cell(line, 1, measure)
        analysis.cell(line, 2, f"='Income Statements'!B{sr}")
        analysis.cell(line, 3, f"='Income Statements'!C{sr}")
        analysis.cell(line, 4, f"=100*(C{line}-B{line})")
        analysis.cell(line, 5, "percentage points")
    commentary_heading = analysis.max_row + 2
    analysis.merge_cells(start_row=commentary_heading, start_column=1, end_row=commentary_heading, end_column=5)
    analysis.cell(commentary_heading, 1, "Grounded commentary")
    analysis.cell(commentary_heading, 1).font = section_font
    commentary_rows = []
    for r in rows:
        crow = analysis.max_row + 1
        commentary_rows.append(crow)
        analysis.cell(crow, 1, r["Category"])
        analysis.merge_cells(start_row=crow, start_column=2, end_row=crow, end_column=5)
        analysis.cell(crow, 2, _text(comments[r["Category"]]))
        analysis.cell(crow, 1).font = Font(name="Arial", size=10, bold=True, color=navy)
        analysis.cell(crow, 2).font = body_font
        analysis.cell(crow, 1).alignment = Alignment(vertical="top", wrap_text=True)
        analysis.cell(crow, 2).alignment = Alignment(vertical="top", wrap_text=True)
        analysis.row_dimensions[crow].height = min(90, max(30, 15 * ((len(_text(comments[r["Category"]])) + 79) // 80)))
    bridge = analysis.max_row + 2
    analysis.cell(bridge, 1, "Profit change bridge")
    analysis.cell(bridge, 1).font = section_font
    bridge_items = [
        ("Revenue", "Revenue", 1),
        ("Cost of sales", "Cost of sales", -1),
        ("Operating expenses", "Operating expenses", -1),
        ("Finance expense", "Finance expense", -1),
        ("Tax expense", "Tax expense", -1),
    ]
    bridge_lines = {}
    for label, total_label, sign in bridge_items:
        line = analysis.max_row + 1
        bridge_lines[label] = line
        sr = statement_rows["__" + total_label + "__"]
        analysis.cell(line, 1, label)
        analysis.cell(line, 2, f"={sign}*('Income Statements'!C{sr}-'Income Statements'!B{sr})")
        analysis.cell(line, 2).number_format = MONEY_FMT
    analysis.cell(bridge, 2, "=" + "+".join(f"B{bridge_lines[label]}" for label, _, _ in bridge_items))
    analysis.cell(bridge, 2).number_format = MONEY_FMT
    bridge_total = analysis.max_row + 1
    analysis.cell(bridge_total, 1, "Net income change")
    analysis.cell(bridge_total, 2, "=" + "+".join(f"B{bridge_lines[label]}" for label, _, _ in bridge_items))
    analysis.cell(bridge_total, 2).number_format = MONEY_FMT
    for line in range(5, analysis.max_row + 1):
        for col in range(1, 6):
            c = analysis.cell(line, col)
            if c.font == Font(): c.font = body_font
            c.alignment = Alignment(vertical="top", wrap_text=(col in (1, 5) or (line in commentary_rows and col >= 2)))
        for col in (2, 3): analysis.cell(line, col).number_format = PCT_FMT if line in (analysis_rows["Gross margin"], analysis_rows["Net margin"]) else MONEY_FMT
        analysis.cell(line, 4).number_format = PP_FMT if line in (analysis_rows["Gross margin"], analysis_rows["Net margin"]) else MONEY_FMT
        if line not in (analysis_rows["Gross margin"], analysis_rows["Net margin"]):
            analysis.cell(line, 5).number_format = PCT_FMT
        if line in analysis_rows.values():
            analysis.row_dimensions[line].height = 24
        elif line in commentary_rows:
            length = len(_text(analysis.cell(line, 2).value))
            analysis.row_dimensions[line].height = max(42, 15 * ((length + 64) // 65))
        elif line != commentary_heading:
            analysis.row_dimensions[line].height = 22
    for line in (analysis_rows["Gross margin"], analysis_rows["Net margin"], bridge_total):
        for c in analysis[line]: c.font = total_font; c.border = Border(top=thin_blue)
    common_layout(analysis, [29, 15, 15, 17, 23], f"A1:E{analysis.max_row}")
    analysis.page_setup.fitToHeight = 0
    analysis.print_title_rows = "1:2"
    # Start commentary and bridge sections on fresh pages; repeat only title and period.
    analysis.row_breaks.append(Break(id=commentary_heading - 1))
    analysis.row_breaks.append(Break(id=bridge - 1))

    # Formula-driven reconciliation checks, with auditable differences and PASS/FAIL status.
    checks.append(["Reconciliation checks"])
    checks.append([f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data"])
    header(checks, 4, ["Check", "January difference", "February difference", "Status"])
    checks.merge_cells("A1:D1"); checks.merge_cells("A2:D2")
    title(checks, "Reconciliation checks", f"{company} | {periods[0]} and {periods[1]} | {currency} | Synthetic data")
    check_specs = [
        ("Revenue category sum", "Revenue", "Revenue"),
        ("Cost of sales category sum", "Cost of sales", "Cost of sales"),
        ("Gross profit equation", "Gross profit", "Gross profit"),
        ("Operating expense category sum", "Operating expenses", "Operating expenses"),
        ("Operating profit equation", "Operating profit", "Operating profit"),
        ("Net income equation", "Net income", "Net income"),
    ]
    for name, label, kind in check_specs:
        line = checks.max_row + 1
        checks.cell(line, 1, name)
        stmtrow = statement_rows["__" + label + "__"]
        for col, period_col in ((2, "B"), (3, "C")):
            if kind in ("Revenue", "Cost of sales", "Operating expenses"):
                cls = {"Revenue": "Revenue", "Cost of sales": "Cost of sales", "Operating expenses": "Operating expense"}[kind]
                category_refs = [f"'Income Statements'!{period_col}{statement_rows[r['Category']]}" for r in rows if r["Classification"] == cls]
                actual = "+".join(category_refs) or "0"
                checks.cell(line, col, f"='Income Statements'!{period_col}{stmtrow}-({actual})")
            elif kind == "Gross profit":
                checks.cell(line, col, f"='Income Statements'!{period_col}{stmtrow}-('Income Statements'!{period_col}{statement_rows['__Revenue__']}-'Income Statements'!{period_col}{statement_rows['__Cost of sales__']})")
            elif kind == "Operating profit":
                checks.cell(line, col, f"='Income Statements'!{period_col}{stmtrow}-('Income Statements'!{period_col}{statement_rows['__Gross profit__']}-'Income Statements'!{period_col}{statement_rows['__Operating expenses__']})")
            else:
                checks.cell(line, col, f"='Income Statements'!{period_col}{stmtrow}-('Income Statements'!{period_col}{statement_rows['__Pretax profit__']}-'Income Statements'!{period_col}{statement_rows['__Tax expense__']})")
            checks.cell(line, col).number_format = MONEY_FMT
        checks.cell(line, 4, f'=IF(AND(ABS(B{line})<0.005,ABS(C{line})<0.005),"PASS","FAIL")')
    line = checks.max_row + 1
    checks.cell(line, 1, "Profit bridge to net income movement")
    checks.cell(line, 2, f"='Analysis'!B{bridge_total}-('Income Statements'!C{statement_rows['__Net income__']}-'Income Statements'!B{statement_rows['__Net income__']})")
    checks.cell(line, 2).number_format = MONEY_FMT
    checks.cell(line, 4, f'=IF(ABS(B{line})<0.005,"PASS","FAIL")')
    for rnum in range(5, checks.max_row + 1):
        for c in checks[rnum]: c.font = body_font; c.alignment = Alignment(vertical="top", wrap_text=True)
    common_layout(checks, [39, 20, 20, 16], f"A1:D{checks.max_row}")

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None and cell.font.sz and cell.font.sz < 10:
                    cell.font = Font(name="Arial", size=10, bold=cell.font.bold, italic=cell.font.italic,
                                     color=cell.font.color.rgb if cell.font.color and cell.font.color.type == "rgb" else "202020")
    wb.save(output_path)
    wb.close()
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("notes_json", type=Path)
    parser.add_argument("commentary_json", type=Path)
    parser.add_argument("staging_output", type=Path)
    args = parser.parse_args()
    print(build(args.source_csv, args.notes_json, args.commentary_json, args.staging_output))


if __name__ == "__main__":
    main()
