"""Keep conversation checkpoints and a small thread directory on the local host."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver

from accounting_finance_agent.config import PROJECT_ROOT


CHECKPOINT_DATABASE = PROJECT_ROOT / ".state" / "checkpoints.sqlite"


@dataclass(frozen=True)
class Thread:
    id: str
    title: str


class ThreadHistory:
    """Track selectable conversations alongside LangGraph's checkpoint tables."""

    def __init__(self, checkpointer: SqliteSaver, mode: str):
        self.checkpointer = checkpointer
        self.mode = mode
        with checkpointer.lock, checkpointer.conn:
            checkpointer.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS finance_threads (
                    thread_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS finance_active_threads (
                    mode TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL
                );
                """
            )

    def new(self) -> Thread:
        thread = Thread(str(uuid4()), "")
        with self.checkpointer.lock, self.checkpointer.conn:
            self.checkpointer.conn.execute(
                "INSERT INTO finance_threads(thread_id, mode, updated_at) VALUES (?, ?, ?)",
                (thread.id, self.mode, datetime.now(timezone.utc).isoformat()),
            )
        return self.select(thread.id)

    def select(self, thread_id: str) -> Thread:
        with self.checkpointer.lock, self.checkpointer.conn:
            row = self.checkpointer.conn.execute(
                "SELECT thread_id, title FROM finance_threads WHERE thread_id = ? AND mode = ?",
                (thread_id, self.mode),
            ).fetchone()
            if row is None:
                raise ValueError(
                    f"No saved thread {thread_id!r} in {self.mode} mode. "
                    "Use :threads to list available IDs."
                )
            self.checkpointer.conn.execute(
                "INSERT INTO finance_active_threads(mode, thread_id) VALUES (?, ?) "
                "ON CONFLICT(mode) DO UPDATE SET thread_id = excluded.thread_id",
                (self.mode, thread_id),
            )
        return Thread(*row)

    def initial(self, thread_id: str | None = None) -> Thread:
        if thread_id:
            return self.select(thread_id)
        with self.checkpointer.lock:
            row = self.checkpointer.conn.execute(
                "SELECT thread_id FROM finance_active_threads WHERE mode = ?", (self.mode,)
            ).fetchone()
        return self.select(row[0]) if row else self.new()

    def list(self) -> list[Thread]:
        with self.checkpointer.lock:
            rows = self.checkpointer.conn.execute(
                "SELECT thread_id, title FROM finance_threads WHERE mode = ? "
                "ORDER BY updated_at DESC, thread_id",
                (self.mode,),
            ).fetchall()
        return [Thread(*row) for row in rows]

    def record_prompt(self, thread: Thread, prompt: str) -> None:
        title = " ".join(prompt.split())[:90]
        with self.checkpointer.lock, self.checkpointer.conn:
            self.checkpointer.conn.execute(
                "UPDATE finance_threads SET title = CASE WHEN title = '' THEN ? ELSE title END, "
                "updated_at = ? WHERE thread_id = ? AND mode = ?",
                (title, datetime.now(timezone.utc).isoformat(), thread.id, self.mode),
            )


@contextmanager
def open_history(*, mode: str, database: Path = CHECKPOINT_DATABASE) -> Iterator[ThreadHistory]:
    """Own the SQLite connection for the whole terminal session."""
    database.parent.mkdir(parents=True, exist_ok=True)
    with SqliteSaver.from_conn_string(str(database)) as checkpointer:
        yield ThreadHistory(checkpointer, mode)
