"""Create deliberately defective copies for exercising the independent grader."""
import argparse
from pathlib import Path
import shutil
import openpyxl


def seed(source,destination):
    source,destination=Path(source),Path(destination)
    for name in ('wrong-net-income','missing-sheet','no-formula-cache','altered-input'):
        target=destination/name
        shutil.copytree(source,target)
        workbook=next(target.rglob('working-paper.xlsx'))
        if name=='altered-input':
            with (target/'source.csv').open('a') as f:f.write('\nunauthorized input change\n')
            continue
        wb=openpyxl.load_workbook(workbook)
        if name=='missing-sheet':del wb['Checks']
        if name=='wrong-net-income':
            for row in wb['Income Statements']:
                for cell in row:
                    if cell.value=='Net income':wb['Income Statements'].cell(cell.row,cell.column+1,999999)
        # Saving also intentionally clears cached formulas for the cache defect.
        wb.save(workbook);wb.close()
    return destination

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();print(seed(a.source,a.destination))
