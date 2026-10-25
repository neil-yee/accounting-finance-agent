"""Independent numerical grader. Human narrative/layout review is separately required."""
from decimal import Decimal
import csv
import json
from pathlib import Path
import openpyxl
from accounting_finance_agent.spreadsheets import validate_delivery
from accounting_finance_agent.config import PROJECT_ROOT


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
            after=[c for c in row if c.column>cell.column and isinstance(c.value,(float,int))]
            if len(after)<2:
                errors.append('Two monthly values missing: '+label);continue
            found[label]=True
            for month,value in zip(['January','February'],after[:2]):
                tolerance=Decimal('0.000001') if 'margin' in label.lower() else Decimal('.01')
                if abs(Decimal(str(value.value))-Decimal(oracle[month][label]))>tolerance:
                    errors.append(month+' incorrect: '+label)
                f=formulas['Income Statements'][value.coordinate]
                if f.data_type!='f': errors.append('Required formula missing: '+label)
    for label in oracle['January']:
        if label not in found: errors.append('Statement category/total missing: '+label)
    analysis=' '.join(str(c.value or '') for row in wb['Analysis'] for c in row) if 'Analysis' in wb else ''
    for row in csv.DictReader((assets/'agent-inputs/source.csv').open()):
        if row['Category'].lower() not in analysis.lower():
            errors.append('Analysis coverage missing: '+row['Category'])
    if 'Analysis' in wb:
        expected_labels=[row['Category'] for row in csv.DictReader((assets/'agent-inputs/source.csv').open())]+['Gross margin','Net margin']
        seen=set()
        for row in wb['Analysis']:
            for cell in row:
                label=str(cell.value).strip()
                if label=='Profit change bridge':
                    actual=wb['Analysis'].cell(cell.row,cell.column+1).value
                    if not isinstance(actual,(float,int)) or abs(Decimal(str(actual))-Decimal('4970'))>Decimal('.01'):
                        errors.append('Incorrect profit-change bridge.')
                    seen.add(label)
                if label not in expected_labels: continue
                seen.add(label)
                jan=Decimal(oracle['January'][label]);feb=Decimal(oracle['February'][label])
                expected=[jan,feb,feb-jan,None if jan==0 else (feb-jan)/jan]
                if 'margin' in label.lower(): expected=expected[:3]
                for offset,expected_value in enumerate(expected,1):
                    value=wb['Analysis'].cell(cell.row,cell.column+offset).value
                    if expected_value is None:
                        if str(value).strip().upper()!='N/A':errors.append('Zero-base rule incorrect: '+label)
                    elif not isinstance(value,(int,float)) or abs(Decimal(str(value))-expected_value)>(Decimal('0.000001') if offset==4 or 'margin' in label.lower() else Decimal('.01')):
                        errors.append('Incorrect analysis value: '+label+' field '+str(offset))
                    f=formulas['Analysis'].cell(cell.row,cell.column+offset)
                    if f.data_type!='f' and expected_value is not None:
                        errors.append('Analysis formula missing: '+label)
        for label in expected_labels+['Profit change bridge']:
            if label not in seen: errors.append('Analysis measure missing: '+label)
    if 'Checks' in wb and not any(cell.data_type=='f' for row in formulas['Checks'] for cell in row):
        errors.append('Checks sheet has no reconciliation formulas.')
    report['numeric_pass']=not errors
    report['human_review']='pending; grounding, formula dependency meaning, variance/margin presentation and rendered layout'
    wb.close();formulas.close()
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    a=p.parse_args();r=grade(a.folder);print(json.dumps(r,indent=2));raise SystemExit(bool(r['errors']))
