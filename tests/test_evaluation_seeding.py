"""Ensure defect injection targets the delivered workbook, not its staging copy."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from seed_excel_defects import seed
from accounting_finance_agent.spreadsheets import validate_delivery


class DefectTargetChecks(unittest.TestCase):
    def test_delivery_selection_ignores_preserved_hidden_versions(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ['final','.versions/run/final','.conflicts/run/final']:
                folder=root/name;folder.mkdir(parents=True)
                wb=openpyxl.Workbook();wb.active.title='Inputs'
                for sheet in ['Income Statements','Analysis','Checks']:wb.create_sheet(sheet)
                wb.save(folder/'working-paper.xlsx');wb.close()
                (folder/'recalculation.json').write_text('{"formula_caches":"present"}')
            report=validate_delivery(root)
            self.assertEqual(report['workbook'],'final/working-paper.xlsx')
            self.assertNotIn('Exactly one final working-paper.xlsx is required.',report['errors'])

    def test_final_workbook_is_mutated_when_staging_copy_also_exists(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';source.mkdir()
            (source/'source.csv').write_text('source input\n')
            for name in ['staging','final']:
                folder=source/name;folder.mkdir()
                wb=openpyxl.Workbook();wb.active.title='Inputs'
                for sheet in ['Income Statements','Analysis','Checks']:wb.create_sheet(sheet)
                wb['Income Statements'].append(['Net income',8300,13270])
                wb.save(folder/'working-paper.xlsx');wb.close()
            (source/'final/recalculation.json').write_text(json.dumps({'formula_caches':'present'}))
            seed(source,root/'mutated')
            missing=openpyxl.load_workbook(root/'mutated/missing-sheet/final/working-paper.xlsx')
            stage=openpyxl.load_workbook(root/'mutated/missing-sheet/staging/working-paper.xlsx')
            wrong=openpyxl.load_workbook(root/'mutated/wrong-net-income/final/working-paper.xlsx',data_only=True)
            self.assertNotIn('Checks',missing.sheetnames)
            self.assertIn('Checks',stage.sheetnames)
            self.assertEqual(wrong['Income Statements']['B1'].value,999999)
            for wb in [missing,stage,wrong]:wb.close()
