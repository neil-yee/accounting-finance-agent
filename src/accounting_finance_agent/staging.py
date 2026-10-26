"""Stage approved procedural helpers, never task answers or evaluator code."""
from hashlib import sha256
from pathlib import Path
from accounting_finance_agent.config import EXCEL_PROFILE
from accounting_finance_agent.knowledge import SKILLS_ROOT
from accounting_finance_agent.workspace import _local_path, use_workspace, _replace

HELPERS = ('financial-working-paper/build.py', 'financial-working-paper/validate.py',
           'file-delivery-validation/recalculate.py')


def stage_approved_helpers(settings, workspace):
    if settings.profile != EXCEL_PROFILE:
        return {}
    staged = {}
    with use_workspace(Path(workspace)):
        for name in HELPERS:
            source = SKILLS_ROOT / name
            if source.is_symlink() or any(p.is_symlink() for p in source.parents):
                raise ValueError('Approved helpers must not be links.')
            content = source.read_bytes()
            relative = 'approved-tools/' + name
            target = _local_path(relative)
            if target.exists() and target.read_bytes() != content:
                raise ValueError('Staged helper differs from approved version: ' + relative)
            if not target.exists():
                _replace(target, content)
            staged[relative] = sha256(content).hexdigest()
    return staged
