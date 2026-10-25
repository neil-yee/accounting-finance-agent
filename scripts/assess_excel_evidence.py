"""Reconstruct selected-series provenance from host records without changing approval."""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.worklog import WorkLog
from accounting_finance_agent.workspace import use_workspace, workspace_manifest


def stale_approval_probe():
    """Exercise a disposable synthetic review record, never approve a real run."""
    with TemporaryDirectory() as tmp, closing(WorkLog(Path(tmp) / 'probe.sqlite')) as probe:
        outputs = {'working-paper.xlsx': 'original-sha'}
        probe.start('synthetic-run', 'synthetic-thread', {}, {})
        probe.finish('synthetic-run', 'needs_review', outputs)
        probe.review('synthetic-run', 'synthetic-thread', 'approved', outputs,
                     'synthetic test identity', 'Disposable test; not owner approval.')
        try:
            probe.review('synthetic-run', 'synthetic-thread', 'approved',
                         {'working-paper.xlsx': 'changed-sha'}, 'synthetic test identity')
        except ValueError:
            return {'stale_approval_rejected': True, 'scope': 'disposable synthetic database only'}
        return {'stale_approval_rejected': False}


def assess(path):
    series = json.loads(Path(path).read_text())
    result = {'series_id': series['series_id'], 'trials': [], 'owner_review': 'pending',
              'stale_approval_probe': stale_approval_probe()}
    with closing(WorkLog()) as log:
        for item in series['runs']:
            run = item.get('run')
            if not run:
                result['trials'].append({'ordinal': item['ordinal'], 'status': 'not finished'})
                continue
            row = log.conn.execute('SELECT * FROM runs WHERE id=?', (run['id'],)).fetchone()
            details, inputs, outputs = [json.loads(row[k] or '{}') for k in ['details', 'inputs', 'outputs']]
            events = [{'kind': e['kind'], **json.loads(e['details'])} for e in log.conn.execute(
                'SELECT kind,details FROM events WHERE run_id=? ORDER BY id', (run['id'],))]
            usage = [e for e in events if e['kind'] == 'api_usage']
            snapshots = [e for e in events if e['kind'] == 'sandbox_created']
            with use_workspace(Path(item['workspace'])):
                current = workspace_manifest()
            source_match = all(inputs.get(name) == series['fixture_sha256'].get('agent-inputs/' + name)
                               for name in ['source.csv', 'notes.json', 'task.txt'])
            unchanged = all(outputs.get(name) == inputs.get(name)
                            for name in ['source.csv', 'notes.json', 'task.txt'])
            trace = PROJECT_ROOT / 'traces' / ('trace-' + run['id'] + '.json')
            trace_result = {'downloaded': trace.is_file()}
            if trace.is_file():
                data = json.loads(trace.read_text())
                trace_result.update({'root_matches': data['trace_id'] == run['id'],
                                     'unfinished_records': data['unfinished_run_count'],
                                     'records': data['run_count']})
            result['trials'].append({
                'ordinal': item['ordinal'], 'run_id': run['id'], 'status': row['status'],
                'configuration_matches': details['configuration']['configuration_sha256'] == series['configuration']['configuration_sha256'],
                'source_identity_matches_fixture': source_match, 'sources_preserved': unchanged,
                'saved_outputs_match_current': outputs == current,
                'snapshot_ids': [e.get('snapshot_id') for e in snapshots],
                'provider_models': sorted({e.get('provider_model', '') for e in usage}),
                'provider_tiers': sorted({e.get('service_tier') or '' for e in usage}),
                'input_tokens': sum(e['usage']['input_tokens'] for e in usage),
                'output_tokens': sum(e['usage']['output_tokens'] for e in usage),
                'request_starts': sum(e['kind'] == 'model_started' for e in events),
                'tool_starts': sum(e['kind'] == 'tool_started' for e in events),
                'harness': [e for e in events if e['kind'] == 'harness_configuration'],
                'backups': [e['path'] for e in events if e['kind'] == 'backup_saved'],
                'sandbox_deletion_requested': any(e['kind'] == 'sandbox_deletion_requested' for e in events),
                'trace': trace_result,
                'actual_reviews': log.conn.execute('SELECT COUNT(*) FROM reviews WHERE run_id=?', (run['id'],)).fetchone()[0],
            })
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('series', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); result = assess(a.series)
    a.output.write_text(json.dumps(result, indent=2)); print(a.output)
