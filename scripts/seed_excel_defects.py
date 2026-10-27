"""Create deliberately defective copies for exercising the independent grader."""
import argparse
from pathlib import Path
import shutil
import openpyxl
import posixpath
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from accounting_finance_agent.spreadsheets import validate_delivery


def seed(source,destination):
    source,destination=Path(source),Path(destination)
    for name in ('wrong-net-income','missing-sheet','no-formula-cache','altered-input'):
        target=destination/name
        shutil.copytree(source,target)
        delivery=validate_delivery(target)
        if not delivery.get('workbook'):
            raise ValueError('Seed source must have one identifiable final working-paper.xlsx.')
        workbook=target/delivery['workbook']
        if name=='altered-input':
            with (target/'source.csv').open('a') as f:f.write('\nunauthorized input change\n')
            continue
        wb=openpyxl.load_workbook(workbook)
        if name=='missing-sheet':del wb['Checks']
        if name=='wrong-net-income':
            address=None
            for row in wb['Income Statements']:
                for cell in row:
                    if cell.value=='Net income':address=wb['Income Statements'].cell(cell.row,cell.column+1).coordinate
            wb.close()
            if address is None:raise ValueError('Net income label missing in seed control.')
            # Change only the target formula/cache; keep other caches intact so
            # the numerical defect cannot hide behind a missing-cache failure.
            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            with ZipFile(workbook) as archive:
                contents={info.filename:(info,archive.read(info.filename)) for info in archive.infolist()}
            book=ET.fromstring(contents['xl/workbook.xml'][1])
            sheet=next(s for s in book.find('s:sheets',ns) if s.get('name')=='Income Statements')
            rid=sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            relations=ET.fromstring(contents['xl/_rels/workbook.xml.rels'][1])
            target=next(r.get('Target') for r in relations if r.get('Id')==rid)
            part=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
            document=ET.fromstring(contents[part][1])
            node=next(c for c in document.iter('{'+ns['s']+'}c') if c.get('r')==address)
            node.attrib.pop('t',None)
            for tag in ['f','v']:
                child=node.find('s:'+tag,ns)
                if child is None:
                    child=ET.Element('{'+ns['s']+'}'+tag)
                    if tag=='f':node.insert(0,child)
                    else:node.append(child)
                child.text='999999'
            contents[part]=(contents[part][0],ET.tostring(document,encoding='utf-8',xml_declaration=True))
            temporary=workbook.with_suffix('.seed-tmp')
            with ZipFile(temporary,'w') as archive:
                for info,data in contents.values():archive.writestr(info,data)
            temporary.replace(workbook)
            continue
        # Saving also intentionally clears cached formulas for the cache defect.
        wb.save(workbook);wb.close()
    return destination

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args();print(seed(a.source,a.destination))
