"""Run three frozen trials; preserve failures and independently recalculate copies."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
from time import monotonic
from uuid import uuid4

from accounting_finance_agent.config import EXCEL_PROFILE, PROJECT_ROOT, load_settings
from accounting_finance_agent.__main__ import run_prompt
from accounting_finance_agent.provenance import effective_configuration
from accounting_finance_agent.persistence import open_history
from accounting_finance_agent.worklog import WorkLog
from accounting_finance_agent.workspace import thread_workspace
from grade_excel_benchmark import grade
from recalculate_evaluation import recalculate


def hashes(root):
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def evaluator_hashes():
    paths = [Path(__file__), Path(__file__).with_name('grade_excel_benchmark.py'),
             Path(__file__).with_name('recalculate_evaluation.py'),
             Path(__file__).with_name('seed_excel_defects.py')]
    return {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}


def usage(log, run_id):
    events = [dict(row) for row in log.conn.execute(
        'SELECT kind, details FROM events WHERE run_id=? ORDER BY id', (run_id,))]
    calls = [json.loads(e['details']) for e in events if e['kind'] == 'api_usage']
    return {'completed_inference_calls': len(calls),
            'input_tokens': sum(e['usage']['input_tokens'] for e in calls),
            'output_tokens': sum(e['usage']['output_tokens'] for e in calls),
            'conservative_usd': calls[-1]['committed_usd'] if calls else None,
            'provider_models': sorted({str(e.get('provider_model') or '') for e in calls}),
            'service_tiers': sorted({e.get('service_tier', '') or '' for e in calls}),
            'request_starts': sum(e['kind'] == 'model_started' for e in events),
            'tool_starts': sum(e['kind'] == 'tool_started' for e in events)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--assets', type=Path, default=PROJECT_ROOT/'evaluations/excel-v4')
    args = parser.parse_args()
    if not args.run:
        parser.error('Use --run to start three paid model/sandbox trials.')
    settings = load_settings(require_sandbox=True, profile=EXCEL_PROFILE)
    assets = args.assets.resolve()
    fixture = hashes(assets)
    configuration = effective_configuration(settings)
    graders = evaluator_hashes()
    series_id = str(uuid4())
    output = PROJECT_ROOT / '.state/evaluations' / ('excel-' + series_id + '.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    record = {'series_id': series_id, 'started': datetime.now(timezone.utc).isoformat(),
              'configuration': configuration, 'fixture_sha256': fixture,
              'evaluator_sha256': graders, 'fixture_path': str(assets), 'status': 'running', 'runs': [],
              'dimensions': {'what': 'artifacts, calculations, required behavior and evidence',
                             'who': 'independent code grader; assistant review and owner review recorded separately',
                             'when': 'offline synthetic trials', 'why': 'capability, consistency and regression'},
              'human_review': 'pending owner review', 'all_three_must_pass': True}
    save = lambda: output.write_text(json.dumps(record, indent=2))
    save()
    print('SERIES RECORD:', output, flush=True)
    with open_history(mode='excel-evaluation') as history, closing(WorkLog()) as log:
        for n in range(3):
            if (hashes(assets) != fixture or evaluator_hashes() != graders or
                    effective_configuration(settings)['configuration_sha256'] != configuration['configuration_sha256']):
                record['status'] = 'invalidated'; save()
                raise RuntimeError('Frozen configuration/fixture/evaluator changed; start a new series.')
            thread = history.new()
            folder = thread_workspace(thread.id)
            for source in (assets / 'agent-inputs').iterdir():
                shutil.copyfile(source, folder / source.name)
            item = {'ordinal': n + 1, 'thread': thread.id, 'workspace': str(folder), 'status': 'running'}
            record['runs'].append(item); save()
            prompt = (folder / 'task.txt').read_text()
            history.record_prompt(thread, prompt)
            started = monotonic()
            try:
                run_prompt(settings, history, log, thread.id, prompt, sandbox=True)
            except Exception as exc:
                item['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            finally:
                item['agent_elapsed_seconds'] = round(monotonic() - started, 3)
                runs = log.runs(thread.id)
                item['run'] = runs[0] if runs else None
                if runs:
                    item['usage'] = usage(log, runs[0]['id'])
                item['status'] = 'agent_finished'; save()
            if (hashes(assets) != fixture or evaluator_hashes() != graders or
                    effective_configuration(settings)['configuration_sha256'] != configuration['configuration_sha256']):
                record['status'] = 'invalidated'; save()
                raise RuntimeError('Frozen configuration/fixture/evaluator changed; start a new series.')
            try:
                item['grader'] = grade(folder, assets)
                item['independent_recalculation'] = recalculate(
                    folder, output.parent / (series_id + '-trial-' + str(n + 1)), settings, assets)
            except Exception as exc:
                item['evaluation_error'] = {'type': type(exc).__name__, 'message': str(exc)}
            independent = item.get('independent_recalculation', {})
            item['numeric_gate'] = bool(
                not item.get('error') and (item.get('run') or {}).get('status') == 'needs_review'
                and item.get('grader', {}).get('numeric_pass')
                and independent.get('status') == 'complete'
                and independent.get('original_unchanged')
                and independent.get('grader', {}).get('numeric_pass'))
            item['status'] = 'evaluated'; save()
    record['status'] = 'complete'
    record['numeric_consistency_gate'] = len(record['runs']) == 3 and all(r['numeric_gate'] for r in record['runs'])
    record['finished'] = datetime.now(timezone.utc).isoformat()
    save()
    print('SERIES COMPLETE:', output, flush=True)


if __name__ == '__main__':
    main()
