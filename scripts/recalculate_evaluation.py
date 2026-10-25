"""Recalculate a copied delivery under evaluator control, without running agent code."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
from uuid import uuid4

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.lifecycle import deadline
from accounting_finance_agent.runtime import RunContext, RunControls
from accounting_finance_agent.sandbox import sandbox_backend
from accounting_finance_agent.spreadsheets import validate_delivery
from accounting_finance_agent.workspace import use_workspace


class EvaluationLog:
    def __init__(self):
        self.events = []

    def event(self, run_id, kind, **details):
        self.events.append({'kind': kind, **details})


def recalculate(folder, destination, settings):
    """Keep original evidence unchanged; recalculate only the untrusted XLSX copy.

    No generated Python, macros, external sources or agent-supplied helper runs.
    Formula dependency meaning and narrative/layout are separate review items.
    """
    folder, destination = Path(folder), Path(destination)
    original = validate_delivery(folder)
    if not original.get('workbook'):
        return {'errors': original['errors'], 'status': 'no_candidate'}
    source = folder / original['workbook']
    if destination.exists():
        raise ValueError('Use a fresh evaluator output folder.')
    destination.mkdir(parents=True)
    (destination / 'staging').mkdir()
    shutil.copyfile(source, destination / 'staging/working-paper.xlsx')
    helper = PROJECT_ROOT / 'skills/file-delivery-validation/recalculate.py'
    shutil.copyfile(helper, destination / 'recalculate.py')
    # Only the fixed agent-facing source files are copied; never oracle answers.
    for name in ('source.csv', 'notes.json', 'task.txt'):
        shutil.copyfile(folder / name, destination / name)
    identity = str(uuid4())
    log = EvaluationLog()
    controls = RunControls(replace(settings, run_seconds=240),
                           RunContext(identity, identity, settings.timezone, str(destination)), log)
    report = {'original_workbook_sha256': sha256(source.read_bytes()).hexdigest(),
              'helper_sha256': sha256(helper.read_bytes()).hexdigest(),
              'status': 'running', 'events': log.events}
    try:
        with deadline(240), use_workspace(destination), sandbox_backend(
            snapshot_id=settings.sandbox_snapshot_id, allowed_hosts=(),
            command_timeout=120, controls=controls,
            event=lambda kind, **details: log.event(identity, kind, **details),
        ) as backend:
            result = backend.execute('python3 /workspace/recalculate.py /workspace/staging/working-paper.xlsx /workspace/final', timeout=120)
            report['command'] = {'exit_code': result.exit_code, 'output': result.output}
            if result.exit_code != 0:
                raise RuntimeError('Evaluator recalculation failed.')
        from grade_excel_benchmark import grade
        report['grader'] = grade(destination)
        report['status'] = 'complete'
        report['original_unchanged'] = sha256(source.read_bytes()).hexdigest() == report['original_workbook_sha256']
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    (destination / 'evaluator-recalculation.json').write_text(json.dumps(report, indent=2))
    return report
