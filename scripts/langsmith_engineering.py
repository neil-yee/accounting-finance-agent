"""Publish and optionally run the existing offline unittest cases in LangSmith.

``sync`` creates or updates datasets; it never executes checks. ``run`` executes
existing checks in isolated local subprocesses and uploads experiment results.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'tests'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

GROUPS = {
    'foundation-runtime': ('test_foundations', 'test_agent_runtime'),
    'sandbox-workspace': ('test_sandbox', 'test_workspace', 'test_transfer_check', 'test_approved_staging', 'test_evaluation_boundaries', 'test_evaluation_checkpoint'),
    'recovery': ('test_recovery_integration', 'test_evaluation_probe'),
    'benchmark-controls': ('test_benchmark_build',),
    'evaluation-infrastructure': ('test_context_cases', 'test_evaluation_context', 'test_evaluation_grader', 'test_evaluation_recalculation', 'test_evaluation_seeding'),
    'financial-helpers': ('test_financial_working_paper', 'test_management_review'),
}
PREFIX = 'accounting-finance-engineering-v1-'
NAMESPACE = uuid.UUID('c923b46f-a58c-461d-a78b-8295379b639c')


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def cases():
    loader = unittest.TestLoader()
    suite = loader.discover(str(TESTS), pattern='test_*.py')
    if loader.errors:
        raise RuntimeError('Test discovery failed; no datasets were changed.\n' + '\n'.join(loader.errors))
    module_group = {module: group for group, modules in GROUPS.items() for module in modules}
    grouped = collections.defaultdict(list)
    for case in flatten(suite):
        test_id = case.id()
        module = test_id.split('.')[0]
        if module not in module_group:
            raise ValueError(f'Unclassified test module {module}; update GROUPS before syncing.')
        grouped[module_group[module]].append(test_id)
    return {g: sorted(grouped[g]) for g in GROUPS}


def sync():
    from langsmith import Client
    client = Client()
    grouped = cases()  # Fail before creating or changing remote data.
    for group, ids in grouped.items():
        name = PREFIX + group
        datasets = list(client.list_datasets(dataset_name=name))
        exact = [d for d in datasets if d.name == name]
        if len(exact) > 1:
            raise RuntimeError(f'Ambiguous dataset name: {name}')
        dataset = exact[0] if exact else client.create_dataset(
            name, description='Existing local offline unittest cases. Input identifies a test; expected outcome is that its existing assertions pass. Execute using scripts/langsmith_engineering.py.')
        existing = {str(e.id): e for e in client.list_examples(dataset_id=dataset.id)}
        wanted = set()
        missing = []
        for test_id in ids:
            example_id = str(uuid.uuid5(NAMESPACE, name + ':' + test_id))
            wanted.add(example_id)
            inputs = {'test_id': test_id, 'group': group}
            expected = {'status': 'passed'}
            if example_id not in existing:
                missing.append({'id': example_id, 'inputs': inputs, 'outputs': expected,
                                'metadata': {'source': 'repo unittest', 'offline': True}})
            elif existing[example_id].inputs != inputs or existing[example_id].outputs != expected:
                raise RuntimeError(f'Existing example differs for {test_id}; inspect rather than overwrite.')
        if missing:
            client.create_examples(dataset_id=dataset.id, examples=missing)
        extras = set(existing) - wanted
        if extras:
            print(f'WARNING {name}: {len(extras)} extra remote examples were not removed.', flush=True)
        print(f'DATASET {group} {len(ids)} {dataset.id}', flush=True)


def execute(test_id):
    # Selection is restricted to cases discovered in this checkout. Discovery
    # is repeated inside the offline environment; test assertions are unchanged.
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append(True)
        raise AssertionError('Network access is disabled in offline engineering checks.')
    stream = io.StringIO()
    with (patch.dict(os.environ, {'OPENAI_API_KEY': 'offline-placeholder', 'LANGSMITH_TRACING': 'false'}, clear=True),
          patch.object(socket.socket, 'connect', side_effect=blocked),
          patch('socket.create_connection', side_effect=blocked),
          patch('accounting_finance_agent.config.load_dotenv', return_value=False)):
        suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
        result = unittest.TextTestRunner(stream=stream, verbosity=2, buffer=True).run(suite)
    if attempts or not result.wasSuccessful() or result.testsRun != 1:
        status = 'failed'
    elif result.skipped:
        status = 'skipped'
    else:
        status = 'passed'
    return {'status': status, 'tests_run': result.testsRun, 'network_attempts': len(attempts),
            'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'report': stream.getvalue()[-12000:]}


def target(inputs):
    # Running a separate process keeps mocks and fake credentials from affecting
    # LangSmith uploads. The process still relies on unittest's test fixtures.
    test_id = inputs['test_id']
    allowed = {i for group in cases().values() for i in group}
    if test_id not in allowed:
        raise ValueError('Unknown test ID in dataset; sync and inspect the checkout.')
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), 'execute', test_id],
                          cwd=ROOT, capture_output=True, text=True, timeout=180)
    if proc.returncode:
        raise RuntimeError(f'Local test runner exited {proc.returncode}: {proc.stderr[-4000:]}')
    return json.loads(proc.stdout)


def evaluator(outputs, reference_outputs):
    status = outputs.get('status')
    if status == 'skipped':
        return {'key': 'engineering_check_passed', 'value': 'skipped', 'comment': 'Skipped; not a pass.'}
    return {'key': 'engineering_check_passed', 'score': int(status == reference_outputs['status']),
            'comment': f'Local unittest status: {status}; network attempts: {outputs.get("network_attempts")}.'}


def run(group):
    from langsmith import Client, evaluate
    if group not in GROUPS:
        raise ValueError(f'Unknown group {group}')
    return evaluate(target, data=PREFIX + group, evaluators=[evaluator], client=Client(),
                    experiment_prefix='engineering-' + group, max_concurrency=1,
                    description='Existing offline unittest checks, executed locally with network blocked.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('inventory', 'sync', 'run', 'execute'))
    p.add_argument('name', nargs='?')
    args = p.parse_args()
    if args.action == 'inventory':
        for name, ids in cases().items():
            print(f'{name}: {len(ids)}')
    elif args.action == 'sync':
        sync()
    elif args.action == 'run':
        if args.name is None: p.error('run requires a group name')
        run(args.name)
    else:
        if args.name is None: p.error('execute requires a test ID')
        result = execute(args.name)
        print(json.dumps(result))


if __name__ == '__main__':
    main()
