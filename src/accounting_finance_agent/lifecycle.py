"""Deadlines, consistent local archives and explicit closed-thread retention."""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import shutil
import signal
import sqlite3
from threading import current_thread, main_thread

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.runtime import RunLimitExceeded


@contextmanager
def deadline(seconds):
    if not hasattr(signal, 'setitimer') or current_thread() is not main_thread():
        raise RuntimeError('Strict benchmark deadlines require a POSIX main-process runner.')
    def expired(*_):
        raise RunLimitExceeded('Hard phase deadline reached.')
    previous = signal.signal(signal.SIGALRM, expired)
    timer = signal.setitimer(signal.ITIMER_REAL, max(.001, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *timer)
        signal.signal(signal.SIGALRM, previous)


def archive_run(run_id, folder):
    root = PROJECT_ROOT.parent / 'accounting-finance-agent-archives'
    if root.is_symlink():
        raise ValueError('Archive root must not be a link.')
    root.mkdir(mode=0o700, exist_ok=True)
    target = root / run_id
    target.mkdir(mode=0o700)
    for name in ('checkpoints.sqlite', 'worklog.sqlite'):
        source = PROJECT_ROOT / '.state' / name
        if source.exists():
            with sqlite3.connect(source) as src, sqlite3.connect(target / name) as dst:
                src.backup(dst)
    if folder:
        shutil.copytree(folder, target / 'files', symlinks=False,
                        ignore=lambda directory, names: [name for name in names
                            if (Path(directory) / name).is_symlink()])
    (target / 'archive.json').write_text(json.dumps({'run':run_id,'thread':folder.name if folder else None,'created':datetime.now(timezone.utc).isoformat()}))
    return target


def mark_active(thread_id):
    from uuid import UUID
    key = str(UUID(thread_id))
    (PROJECT_ROOT / '.state' / 'closed-threads' / (key + '.json')).unlink(missing_ok=True)


def mark_closed(thread_id):
    from uuid import UUID
    thread_id = str(UUID(thread_id))
    root = PROJECT_ROOT / '.state' / 'closed-threads'
    root.mkdir(parents=True, exist_ok=True)
    (root / (thread_id + '.json')).write_text(json.dumps({'closed':datetime.now(timezone.utc).isoformat()}))


def retention_candidates(now=None):
    now = now or datetime.now(timezone.utc)
    root = PROJECT_ROOT / '.state' / 'closed-threads'
    return [p.stem for p in root.glob('*.json')
            if datetime.fromisoformat(json.loads(p.read_text())['closed']) <= now - timedelta(days=30)]
