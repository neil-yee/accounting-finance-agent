"""Local factual run records and human review of exact workspace versions."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import RLock

from accounting_finance_agent.config import PROJECT_ROOT


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkLog:
    def __init__(self, database: Path | None = None):
        path = database if database is not None else PROJECT_ROOT / ".state" / "worklog.sqlite"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, started TEXT NOT NULL,
                finished TEXT, status TEXT NOT NULL, details TEXT NOT NULL,
                inputs TEXT NOT NULL, outputs TEXT, error_type TEXT);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, at TEXT NOT NULL,
                kind TEXT NOT NULL, details TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, at TEXT NOT NULL,
                decision TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT NOT NULL,
                manifest TEXT NOT NULL);
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def start(self, run_id, thread_id, details, inputs):
        with self.lock, self.conn:
            self.conn.execute("INSERT INTO runs VALUES (?, ?, ?, NULL, 'running', ?, ?, NULL, NULL)",
                              (run_id, thread_id, utc_now(), json.dumps(details), json.dumps(inputs)))

    def event(self, run_id, kind, **details):
        with self.lock, self.conn:
            self.conn.execute("INSERT INTO events(run_id, at, kind, details) VALUES (?, ?, ?, ?)",
                              (run_id, utc_now(), kind, json.dumps(details)))

    def finish(self, run_id, status, outputs, error_type=None):
        with self.lock, self.conn:
            self.conn.execute("UPDATE runs SET finished=?, status=?, outputs=?, error_type=? WHERE id=?",
                              (utc_now(), status, json.dumps(outputs), error_type, run_id))

    def runs(self, thread_id):
        with self.lock:
            return [dict(row) for row in self.conn.execute(
                "SELECT id, status, started, error_type FROM runs WHERE thread_id=? ORDER BY started DESC LIMIT 20",
                (thread_id,))]

    def recovery_summary(self, thread_id, run_id=None):
        """Return recorded facts for inspection; never resume or replay work."""
        with self.lock:
            if run_id is None:
                row = self.conn.execute(
                    "SELECT * FROM runs WHERE thread_id=? AND status IN ('failed','limited','running') "
                    "ORDER BY started DESC LIMIT 1", (thread_id,),
                ).fetchone()
            else:
                row = self.conn.execute("SELECT * FROM runs WHERE thread_id=? AND id=?",
                                        (thread_id, run_id)).fetchone()
            if row is None:
                raise ValueError("No matching run in the current thread.")
            events = self.conn.execute("SELECT kind, details FROM events WHERE run_id=? ORDER BY id",
                                       (row['id'],)).fetchall()
        data = dict(row)
        data['inputs'] = json.loads(data['inputs'])
        data['outputs'] = json.loads(data['outputs']) if data['outputs'] is not None else None
        data['events'] = [(event['kind'], json.loads(event['details'])) for event in events]
        data.pop('details', None)
        return data

    def review(self, run_id, thread_id, decision, current_manifest, reviewer, note=""):
        if decision not in {"approved", "rejected"}:
            raise ValueError("Review decision must be approved or rejected.")
        with self.lock, self.conn:
            row = self.conn.execute("SELECT * FROM runs WHERE id=? AND thread_id=?",
                                    (run_id, thread_id)).fetchone()
            if row is None:
                raise ValueError("No run with that ID in the current thread.")
            expected = json.loads(row["outputs"] or "{}")
            if decision == "approved" and (row["status"] != "needs_review" or expected != current_manifest):
                raise ValueError("Approval requires a successful run and unchanged workspace file hashes.")
            self.conn.execute("INSERT INTO reviews(run_id, at, decision, reviewer, note, manifest) VALUES (?, ?, ?, ?, ?, ?)",
                              (run_id, utc_now(), decision, reviewer, note, json.dumps(expected)))
        return expected

    def review_status(self, run_id, current_manifest):
        with self.lock:
            row = self.conn.execute("SELECT decision, manifest FROM reviews WHERE run_id=? ORDER BY id DESC LIMIT 1",
                                    (run_id,)).fetchone()
        if row is None:
            return "not reviewed"
        return row["decision"] + (" (workspace changed since review)" if json.loads(row["manifest"]) != current_manifest else "")

    def recovery_record(self, run_id):
        with self.lock:
            run = self.conn.execute("SELECT thread_id FROM runs WHERE id=?", (run_id,)).fetchone()
            events = self.conn.execute("SELECT kind, details FROM events WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        if run is None:
            raise ValueError("Unknown run ID.")
        created = [json.loads(row["details"]) for row in events if row["kind"] == "sandbox_created"]
        uploaded = [json.loads(row["details"]) for row in events if row["kind"] == "workspace_uploaded"]
        if not created or not uploaded:
            raise ValueError("No recorded sandbox and upload baseline for safe recovery.")
        return run["thread_id"], created[-1]["sandbox"], uploaded[-1]["files"]


@contextmanager
def thread_lease(thread_id: str):
    """Prevent overlapping local runs; stale locks require explicit owner removal."""
    from hashlib import sha256
    import os
    folder = PROJECT_ROOT / ".state" / "locks"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (sha256(thread_id.encode()).hexdigest() + ".lock")
    try:
        stream = path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError(f"Thread has a run lock: {path}. Check the owning process before removing a stale lock.") from exc
    try:
        with stream:
            json.dump({"pid": os.getpid(), "created": utc_now(), "thread_id": thread_id}, stream)
        yield
    finally:
        path.unlink(missing_ok=True)
