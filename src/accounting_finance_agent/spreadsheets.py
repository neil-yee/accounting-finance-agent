"""Independent structural/value checks, without running generated workbook code."""
import json
from zipfile import ZipFile
from pathlib import Path
import openpyxl


def validate_delivery(folder):
    folder = Path(folder)
    errors = []
    workbooks = list(folder.rglob('working-paper.xlsx'))
    finals = [p for p in workbooks if (p.parent / 'recalculation.json').is_file()]
    candidates = finals or workbooks
    if len(candidates) != 1:
        return {'errors':['Exactly one final working-paper.xlsx is required.']}
    path = candidates[0]
    with ZipFile(path) as archive:
        if sum(item.file_size for item in archive.infolist()) > 200 * 1024**2:
            return {'errors':['Workbook expansion exceeds the 200 MiB inspection limit.']}
    formulas = openpyxl.load_workbook(path, data_only=False, keep_links=False)
    values = openpyxl.load_workbook(path, data_only=True, keep_links=False)
    if formulas.sheetnames != ['Inputs','Income Statements','Analysis','Checks']:
        errors.append('Required four sheets/order not present.')
    count = 0
    for sheet in formulas:
        for row in sheet:
            for cell in row:
                if cell.data_type == 'f':
                    count += 1
                    value = values[sheet.title][cell.coordinate]
                    if value.value is None or value.data_type == 'e':
                        errors.append(f'Missing/error cache: {sheet.title}!{cell.coordinate}')
                    if '[' in cell.value or 'http' in cell.value.lower():
                        errors.append('External formula references are unsupported.')
    if not count:
        errors.append('No formulas found.')
    if not list(path.parent.glob('page-*.png')) or not path.with_suffix('.pdf').is_file():
        errors.append('Rendered evidence missing.')
    try:
        report = json.loads((path.parent/'recalculation.json').read_text())
        if report.get('formula_caches') != 'present':
            errors.append('Recalculation was not confirmed.')
    except (OSError, ValueError):
        errors.append('Recalculation record missing/invalid.')
    formulas.close(); values.close()
    return {'errors':errors, 'workbook':str(path.relative_to(folder)), 'formulas':count,
            'human_review':'required: grounded analysis and visual quality'}
