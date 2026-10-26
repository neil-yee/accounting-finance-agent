"""Approved code staging is versioned, scoped and excludes evaluation answers."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from accounting_finance_agent.config import Settings,EXCEL_PROFILE
from accounting_finance_agent.staging import stage_approved_helpers,HELPERS


class ApprovedStagingTests(unittest.TestCase):
    def test_stages_only_approved_code_and_is_idempotent(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);skills=root/'skills';work=root/'work'
            for name in HELPERS:
                p=skills/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# approved helper\n')
            (skills/'oracle.json').write_text('{"hidden_answer":999}')
            settings=replace(Settings('gpt-6-luna','high',True,'offline'),profile=EXCEL_PROFILE)
            with patch('accounting_finance_agent.staging.SKILLS_ROOT',skills):
                first=stage_approved_helpers(settings,work)
                self.assertEqual(first,stage_approved_helpers(settings,work))
                self.assertEqual(set(first),{'approved-tools/'+name for name in HELPERS})
                self.assertFalse((work/'oracle.json').exists())
                (work/'approved-tools'/HELPERS[0]).write_text('tampered')
                with self.assertRaisesRegex(ValueError,'differs from approved'):
                    stage_approved_helpers(settings,work)

    def test_local_profile_does_not_stage_helpers(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(stage_approved_helpers(Settings('model','high',False,'offline'),Path(tmp)),{})
