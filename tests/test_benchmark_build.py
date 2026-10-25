"""Exercise budget/retry and acceptance boundaries without spending API credits."""
from contextlib import redirect_stdout
from dataclasses import replace
from decimal import Decimal
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import httpx
import openpyxl
from accounting_finance_agent.budget import BudgetClient
from accounting_finance_agent.config import Settings, EXCEL_PROFILE
from accounting_finance_agent.runtime import RunContext, RunControls, RunLimitExceeded
from accounting_finance_agent.lifecycle import deadline
from accounting_finance_agent.spreadsheets import validate_delivery
from accounting_finance_agent import knowledge


class BenchmarkBuildChecks(unittest.TestCase):
    def setUp(self):
        self.settings=replace(Settings('gpt-6-luna','high',False,'offline'),profile=EXCEL_PROFILE)
        self.controls=RunControls(self.settings,RunContext('run','thread','UTC','virtual'),Mock())

    def client(self, handler):
        return BudgetClient(self.controls,transport=httpx.MockTransport(handler))

    def request(self, client, **extra):
        return client.post('https://api.openai.com/v1/responses',json={'model':'gpt-6-luna','input':'hello','max_output_tokens':100,**extra})

    def test_usage_reconciles_reservation_and_counts_each_http_attempt(self):
        with self.client(lambda r:httpx.Response(200,json={'usage':{'input_tokens':10,'output_tokens':5}})) as c:
            self.request(c);self.request(c)
            self.assertEqual(self.controls.counts['model'],2)
            self.assertEqual(c.spent,Decimal('0.000065'))

    def test_retry_ceiling_is_shared_at_http_boundary(self):
        hits=[]
        def respond(r):
            hits.append(1);return httpx.Response(503,json={'error':'temporary'})
        with self.client(respond) as c, patch('accounting_finance_agent.budget.time.sleep'), redirect_stdout(io.StringIO()):
            self.assertEqual(self.request(c).status_code,503)
        self.assertEqual(len(hits),6)
        self.assertEqual(self.controls.counts['model'],6)

    def test_unknown_usage_keeps_reservation(self):
        with self.client(lambda r:httpx.Response(200,json={'output':[]})) as c:
            self.request(c);self.assertGreater(c.spent,Decimal(0))

    def test_budget_denies_before_any_network_attempt(self):
        handler=Mock()
        with self.client(handler) as c:
            c.spent=Decimal('1')
            with self.assertRaises(RunLimitExceeded):self.request(c)
        handler.assert_not_called()

    def test_output_capacity_reduced_to_remaining_budget(self):
        bodies=[]
        def respond(r):
            bodies.append(json.loads(r.content));return httpx.Response(200,json={})
        with self.client(respond) as c:
            c.spent=Decimal('.99');self.request(c,max_output_tokens=32000)
            self.assertLess(bodies[0]['max_output_tokens'],32000)
            self.assertLessEqual(c.spent,Decimal(1))

    def test_invalid_request_does_not_retry(self):
        handler=Mock(return_value=httpx.Response(400,json={'error':'bad request'}))
        with self.client(handler) as c:self.request(c)
        self.assertEqual(handler.call_count,1)

    def test_unpriced_model_and_hidden_history_are_rejected(self):
        with self.client(Mock()) as c:
            for extra in ({'model':'other'},{'previous_response_id':'hidden'},{'stream':True}):
                with self.assertRaises(RunLimitExceeded):self.request(c,**extra)

    def test_retry_after_that_exceeds_deadline_stops(self):
        with self.client(lambda r:httpx.Response(429,headers={'Retry-After':'99999'})) as c:
            with self.assertRaises(RunLimitExceeded):self.request(c)
        self.assertEqual(self.controls.counts['model'],1)

    def test_hard_deadline_interrupts_waiting_operation(self):
        import time
        with self.assertRaises(RunLimitExceeded):
            with deadline(.01):time.sleep(.2)

    def test_missing_output_is_rejected(self):
        with TemporaryDirectory() as root:self.assertTrue(validate_delivery(root)['errors'])

    def test_formula_without_cache_is_rejected(self):
        with TemporaryDirectory() as root:
            w=openpyxl.Workbook();w.active.title='Inputs'
            for name in ['Income Statements','Analysis','Checks']:w.create_sheet(name)
            w['Income Statements']['A1']='=1+2';w.save(Path(root)/'working-paper.xlsx')
            result=validate_delivery(root)
            self.assertTrue(any('cache' in e for e in result['errors']))

    def test_benchmark_reference_scope_has_no_legacy_company_data(self):
        backend=knowledge.knowledge_backend(settings=self.settings)
        result=backend.read('/memories/company-profile.md')
        self.assertTrue(result.error)
        result=backend.read('/memories/AGENTS.md')
        self.assertIsNone(result.error)
        self.assertNotIn('Maple Harbour',str(result))
        self.assertTrue(backend.read('/skills/bank-reconciliation/SKILL.md').error)
        self.assertIsNone(backend.read('/skills/file-delivery-validation/recalculate.py').error)


class LifecycleAndGraderChecks(unittest.TestCase):
    def test_archives_use_sqlite_backup_and_preserve_files(self):
        import sqlite3
        from accounting_finance_agent import lifecycle
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo';(root/'.state').mkdir(parents=True)
            folder=root/'workspace/thread';folder.mkdir(parents=True);(folder/'final.txt').write_text('preserved')
            with sqlite3.connect(root/'.state/checkpoints.sqlite') as conn:
                conn.execute('CREATE TABLE evidence(value)');conn.execute("INSERT INTO evidence VALUES ('consistent')")
            with patch.object(lifecycle,'PROJECT_ROOT',root):out=lifecycle.archive_run('run',folder)
            self.assertEqual((out/'files/final.txt').read_text(),'preserved')
            with sqlite3.connect(out/'checkpoints.sqlite') as conn:
                self.assertEqual(conn.execute('SELECT value FROM evidence').fetchone()[0],'consistent')

    def test_retention_only_selects_expired_closed_threads(self):
        from accounting_finance_agent import lifecycle
        from datetime import datetime,timezone,timedelta
        with TemporaryDirectory() as tmp:
            root=Path(tmp);markers=root/'.state/closed-threads';markers.mkdir(parents=True)
            now=datetime.now(timezone.utc)
            for name,days in [('old',31),('recent',2)]:
                (markers/(name+'.json')).write_text(json.dumps({'closed':(now-timedelta(days=days)).isoformat()}))
            with patch.object(lifecycle,'PROJECT_ROOT',root):
                self.assertEqual(lifecycle.retention_candidates(now),['old'])

    def test_independent_oracle_contains_known_financial_answers(self):
        from accounting_finance_agent.config import PROJECT_ROOT
        data=json.loads((PROJECT_ROOT/'evaluations/excel-v1/evaluator/oracle.json').read_text())
        self.assertEqual(data['January']['Net income'],'8300')
        self.assertEqual(data['February']['Net income'],'13270')
        self.assertEqual(data['February']['Gross profit'],'34200')

    def test_namespace_wraps_only_configured_execution(self):
        from accounting_finance_agent.sandbox import BoundedSandbox
        from deepagents.backends.langsmith import LangSmithSandbox
        with patch.object(LangSmithSandbox,'execute',return_value=Mock()) as handler:
            backend=BoundedSandbox(sandbox=Mock(),command_timeout=120,network_isolated=True)
            backend.execute('echo hello')
            command=handler.call_args.args[0]
            self.assertTrue(command.startswith('unshare --user --map-root-user --net -- sh -c '))
            self.assertIn('echo hello',command)

class SeededDefectChecks(unittest.TestCase):
    def test_grader_detects_each_seeded_failure(self):
        import shutil
        from scripts.seed_excel_defects import seed
        from scripts.grade_excel_benchmark import grade
        from accounting_finance_agent.config import PROJECT_ROOT
        with TemporaryDirectory() as tmp:
            root=Path(tmp);original=root/'original';original.mkdir()
            for source in (PROJECT_ROOT/'evaluations/excel-v1/agent-inputs').iterdir():
                shutil.copyfile(source,original/source.name)
            w=openpyxl.Workbook();w.active.title='Inputs'
            for name in ['Income Statements','Analysis','Checks']:w.create_sheet(name)
            w['Income Statements'].append(['Net income',8300,13270])
            w['Checks']['A1']='=1+1';w.save(original/'working-paper.xlsx');w.close()
            seed(original,root/'mutants')
            reports={p.name:grade(p) for p in (root/'mutants').iterdir()}
            self.assertTrue(any('January incorrect: Net income' in e for e in reports['wrong-net-income']['errors']))
            self.assertTrue(any('four sheets' in e for e in reports['missing-sheet']['errors']))
            self.assertTrue(any('cache' in e for e in reports['no-formula-cache']['errors']))
            self.assertTrue(any('Source changed' in e for e in reports['altered-input']['errors']))

class SafeRecoveryChecks(unittest.TestCase):
    def test_reopening_a_thread_cancels_retention_eligibility(self):
        from accounting_finance_agent import lifecycle
        from uuid import uuid4
        with TemporaryDirectory() as tmp, patch.object(lifecycle,'PROJECT_ROOT',Path(tmp)):
            thread=str(uuid4());lifecycle.mark_closed(thread)
            marker=Path(tmp)/'.state/closed-threads'/(thread+'.json')
            self.assertTrue(marker.exists());lifecycle.mark_active(thread)
            self.assertFalse(marker.exists())

    def middleware(self):
        from accounting_finance_agent.file_metadata import FileMetadataFilesystemMiddleware
        from deepagents.backends import StateBackend
        settings=replace(Settings('gpt-6-luna','high',False,'offline'),profile=EXCEL_PROFILE)
        controls=RunControls(settings,RunContext('run','thread','UTC','virtual'),Mock())
        return FileMetadataFilesystemMiddleware(backend=StateBackend(),controls=controls)

    def test_read_retry_recovers_transient_failure(self):
        from types import SimpleNamespace
        middleware=self.middleware();request=SimpleNamespace(tool_call={'name':'read_file'})
        with patch.object(middleware,'_one_tool_call',side_effect=[TimeoutError(),TimeoutError(),'done']) as call, patch('time.sleep'), redirect_stdout(io.StringIO()):
            self.assertEqual(middleware.wrap_tool_call(request,Mock()),'done')
            self.assertEqual(call.call_count,3)

    def test_uncertain_write_is_never_replayed(self):
        from types import SimpleNamespace
        middleware=self.middleware();request=SimpleNamespace(tool_call={'name':'execute'})
        with patch.object(middleware,'_one_tool_call',side_effect=TimeoutError()) as call:
            with self.assertRaises(TimeoutError):middleware.wrap_tool_call(request,Mock())
            self.assertEqual(call.call_count,1)

if __name__=='__main__':unittest.main()
