"""Independent numerical grader. Human narrative/layout review is separately required."""
from decimal import Decimal
import csv
import json
import math
from pathlib import Path
import openpyxl
from accounting_finance_agent.spreadsheets import validate_delivery
from accounting_finance_agent.config import PROJECT_ROOT


def is_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def has_reference(cell):
    """Reject literal-only formulas; dependency meaning still requires review."""
    if cell.data_type != 'f':
        return False
    try:
        return any(token.type == 'OPERAND' and token.subtype == 'RANGE'
                   for token in openpyxl.formula.Tokenizer(cell.value).items)
    except (TypeError, ValueError):
        return False


def grade(folder, assets=None):
    assets=Path(assets or PROJECT_ROOT/'evaluations/excel-v1')
    folder=Path(folder)
    report=validate_delivery(folder)
    errors=report['errors']
    for source in (assets/'agent-inputs').iterdir():
        if not (folder/source.name).is_file() or (folder/source.name).read_bytes()!=source.read_bytes():
            errors.append('Source changed or missing: '+source.name)
    if not report.get('workbook'):
        return report
    oracle=json.loads((assets/'evaluator/oracle.json').read_text())
    contract_path=assets/'evaluator/contract.json'
    contract=json.loads(contract_path.read_text()) if contract_path.is_file() else {}
    path=folder/report['workbook']
    wb=openpyxl.load_workbook(path,data_only=True)
    formulas=openpyxl.load_workbook(path,data_only=False)
    if 'Income Statements' not in wb:
        return report
    found={}
    for row in wb['Income Statements']:
        for cell in row:
            label=str(cell.value).strip()
            if label not in oracle['January']: continue
            if label in found:
                errors.append('Ambiguous repeated statement label: '+label)
            after=[c for c in row if c.column>cell.column and is_number(c.value)]
            if len(after)<2:
                errors.append('Two monthly values missing: '+label);continue
            found[label]=True
            for month,value in zip(['January','February'],after[:2]):
                tolerance=Decimal('0.000001') if 'margin' in label.lower() else Decimal('.01')
                if abs(Decimal(str(value.value))-Decimal(oracle[month][label]))>tolerance:
                    errors.append(month+' incorrect: '+label)
                f=formulas['Income Statements'][value.coordinate]
                if not has_reference(f): errors.append('Required reference-based formula missing: '+label)
    for label in oracle['January']:
        if label not in found: errors.append('Statement category/total missing: '+label)
    analysis=' '.join(str(c.value or '') for row in wb['Analysis'] for c in row) if 'Analysis' in wb else ''
    with (assets/'agent-inputs/source.csv').open(newline='') as source:
        source_rows = list(csv.DictReader(source))
    for row in source_rows:
        if row['Category'].lower() not in analysis.lower():
            errors.append('Analysis coverage missing: '+row['Category'])
    # Reconcile workbook inputs to the selected row-oriented source fixture.
    if 'Inputs' not in wb:
        errors.append('Workbook Inputs sheet missing for source reconciliation.')
    else:
        for source_row in source_rows:
            label=source_row['Category']
            matches=[]
            for row in wb['Inputs']:
                for cell in row:
                    if cell.value == label:
                        jan=wb['Inputs'].cell(row=cell.row,column=cell.column+1).value
                        feb=wb['Inputs'].cell(row=cell.row,column=cell.column+2).value
                        matches.append((jan,feb))
            if len(matches)!=1:
                errors.append('Workbook Inputs category missing or ambiguous: '+label)
                continue
            jan,feb=matches[0]
            if (not is_number(jan) or not is_number(feb) or
                abs(Decimal(str(jan))-Decimal(source_row['January']))>Decimal('.01') or
                abs(Decimal(str(feb))-Decimal(source_row['February']))>Decimal('.01')):
                errors.append('Workbook Inputs values missing, unsupported, or incorrect: '+label)
    if 'Analysis' in wb:
        expected_labels=[row['Category'] for row in source_rows]+['Gross margin','Net margin']
        seen=set()
        for row in wb['Analysis']:
            for cell in row:
                label=str(cell.value).strip()
                if label=='Profit change bridge':
                    actual=wb['Analysis'].cell(cell.row,cell.column+1).value
                    bridge_row=cell.row
                    # Some valid workbooks use a section title row followed by
                    # a labeled result row; do not grade the blank title cell.
                    if not is_number(actual) and bridge_row<wb['Analysis'].max_row:
                        result_label=wb['Analysis'].cell(bridge_row+1,cell.column).value
                        result_value=wb['Analysis'].cell(bridge_row+1,cell.column+1).value
                        if result_label is not None and is_number(result_value):
                            bridge_row+=1
                            actual=result_value
                    if not is_number(actual):
                        continue
                    expected_bridge=Decimal(oracle['February']['Net income'])-Decimal(oracle['January']['Net income'])
                    if abs(Decimal(str(actual))-expected_bridge)>Decimal('.01'):
                        errors.append('Incorrect profit-change bridge.')
                    if not has_reference(formulas['Analysis'].cell(bridge_row,cell.column+1)):
                        errors.append('Reference-based profit-change bridge formula missing.')
                    seen.add(label)
                if label not in expected_labels: continue
                jan_cell=wb['Analysis'].cell(cell.row,cell.column+1)
                feb_cell=wb['Analysis'].cell(cell.row,cell.column+2)
                if (not is_number(jan_cell.value) or not is_number(feb_cell.value) or
                    not has_reference(formulas['Analysis'].cell(cell.row,cell.column+1)) or
                    not has_reference(formulas['Analysis'].cell(cell.row,cell.column+2))):
                    continue
                if label in seen:
                    errors.append('Ambiguous repeated analysis measure: '+label)
                seen.add(label)
                jan=Decimal(oracle['January'][label]);feb=Decimal(oracle['February'][label])
                expected=[jan,feb,feb-jan,None if jan==0 else (feb-jan)/jan]
                if 'margin' in label.lower():
                    expected=expected[:3]
                    if contract.get('margin_change_unit')=='percentage_points':
                        expected[2]*=100
                        unit=wb['Analysis'].cell(cell.row,cell.column+4).value
                        if str(unit).strip().lower() not in {'pp','percentage points'}:
                            errors.append('Margin change unit missing: '+label)
                for offset,expected_value in enumerate(expected,1):
                    value=wb['Analysis'].cell(cell.row,cell.column+offset).value
                    if expected_value is None:
                        if str(value).strip().upper()!='N/A':errors.append('Zero-base rule incorrect: '+label)
                    elif not is_number(value) or abs(Decimal(str(value))-expected_value)>(Decimal('0.000001') if offset==4 or 'margin' in label.lower() else Decimal('.01')):
                        errors.append('Incorrect analysis value: '+label+' field '+str(offset))
                    f=formulas['Analysis'].cell(cell.row,cell.column+offset)
                    if not has_reference(f) and expected_value is not None:
                        errors.append('Analysis reference-based formula missing: '+label)
        for label in expected_labels+['Profit change bridge']:
            if label not in seen: errors.append('Analysis measure missing: '+label)
    if 'Checks' in wb:
        if not any(cell.data_type=='f' for row in formulas['Checks'] for cell in row):
            errors.append('Checks sheet has no reconciliation formulas.')
        for row in wb['Checks']:
            for cell in row:
                if cell.value == 'FAIL':
                    errors.append('Explicit FAIL cell: Checks!'+cell.coordinate)
    if contract.get('body_font_minimum'):
        for sheet in formulas:
            for row in sheet:
                for cell in row:
                    if cell.value is not None and cell.font.sz and cell.font.sz < contract['body_font_minimum']:
                        errors.append('Font below minimum: '+sheet.title+'!'+cell.coordinate)
    report['numeric_pass']=not errors
    report['human_review']='pending; grounding, formula dependency meaning, variance/margin presentation and rendered layout'
    wb.close();formulas.close()
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    p.add_argument('--assets',type=Path)
    a=p.parse_args();r=grade(a.folder,a.assets);print(json.dumps(r,indent=2));raise SystemExit(bool(r['errors']))
