"""Additional selected-fixture checks; narrative and presentation remain review tasks."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.utils.cell import range_boundaries


def review(path, source):
    path, source = Path(path), Path(source)
    wb = openpyxl.load_workbook(path, data_only=False)
    values = openpyxl.load_workbook(path, data_only=True)
    with source.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    findings = []
    input_checks = []
    for expected in rows:
        label = expected['Category']; matches = []
        for row in values['Inputs']:
            for cell in row:
                if str(cell.value).strip() == label:
                    numeric = [c.value for c in row if c.column > cell.column and type(c.value) in (int, float)]
                    if len(numeric) >= 2:
                        matches.append(numeric[:2])
        correct = len(matches) == 1 and all(abs(Decimal(str(v))-Decimal(expected[m])) <= Decimal('.01') for v, m in zip(matches[0], ['January', 'February']))
        input_checks.append({'category': label, 'matches_source': correct})
        if not correct: findings.append('Inputs/source row requires review: ' + label)

    memo = {}
    def reaches_inputs(sheet, address, visiting):
        key = (sheet, address)
        if key in memo: return memo[key]
        if key in visiting: return False
        cell = wb[sheet][address]
        if sheet == 'Inputs' and cell.value is not None: return True
        if cell.data_type != 'f': return False
        result = False
        for token in Tokenizer(cell.value).items:
            if token.type != 'OPERAND' or token.subtype != 'RANGE': continue
            ref = token.value
            target, sep, coord = ref.rpartition('!')
            target = target.strip("'").replace("''", "'") if sep else sheet
            coord = (coord if sep else ref).replace('$', '')
            if target not in wb or not re.fullmatch(r'[A-Za-z]{1,3}[1-9][0-9]*(?::[A-Za-z]{1,3}[1-9][0-9]*)?', coord):
                findings.append('Unsupported dependency requires review: '+ref);continue
            a,b,c,d = range_boundaries(coord)
            if (c-a+1)*(d-b+1) > 10000:
                findings.append('Large dependency requires review: '+ref);continue
            for row in wb[target].iter_rows(min_row=b,max_row=d,min_col=a,max_col=c):
                result = result or any(reaches_inputs(target, child.coordinate, visiting | {key}) for child in row)
        memo[key] = result
        return result

    for name in ['Income Statements','Analysis']:
        if name not in wb: continue
        for row in wb[name]:
            for cell in row:
                if cell.data_type == 'f' and not reaches_inputs(name, cell.coordinate, set()):
                    findings.append('Formula does not demonstrably reach Inputs: '+name+'!'+cell.coordinate)
    errors = [s.title+'!'+c.coordinate+': '+str(c.value) for s in values for row in s for c in row if c.data_type == 'e']
    small = [s.title+'!'+c.coordinate for s in wb for row in s for c in row if c.value is not None and c.font.sz and c.font.sz < 10]
    result = {'input_rows': input_checks, 'findings': sorted(set(findings)), 'formula_errors': errors,
              'cells_below_10pt': small, 'limitations': 'Source matching assumes row-oriented January/February values. Dependency reachability does not prove each formula has the correct meaning. Small text can include headings/footnotes; inspect body text visually.'}
    wb.close();values.close();return result


if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('workbook',type=Path);p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.write_text(json.dumps(review(a.workbook,a.source),indent=2));print(a.output)
