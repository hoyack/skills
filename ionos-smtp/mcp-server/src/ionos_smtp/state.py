"""SQLite state store for outbound message tracking (queue mode)."""

from __future__ import annotations

import datetime
import json
import logging
import os
import sqlite3
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS outbound_messages (
    queue_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    sent_at TEXT,
    message_id TEXT,
    payload TEXT
);

CREATE INDEX IF NOT EXISTS idx_outbound_status ON outbound_messages(status);

CREATE TABLE IF NOT EXISTS worker_health (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_heartbeat TEXT,
    last_send_at TEXT,
    connection_state TEXT,
    sends_this_minute INTEGER DEFAULT 0
);
"""


class StateStore:
    """SQLite-backed state for outbound message tracking."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")

    def close(self) -> None:
        self._conn.close()

    def create_outbound(
        self, queue_id: str, payload: dict, message_id: str | None = None
    ) -> None:
        self._conn.execute(
            """INSERT INTO outbound_messages
               (queue_id, created_at, status, attempts, message_id, payload)
               VALUES (?, ?, 'pending', 0, ?, ?)""",
            (
                queue_id,
                datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                message_id,
                json.dumps(payload),
            ),
        )
        self._conn.commit()

    def update_outbound(
        self,
        queue_id: str,
        status: str,
        message_id: str | None = None,
        last_error: str | None = None,
        increment_attempts: bool = False,
    ) -> None:
        parts = ["status = ?"]
        params: list[Any] = [status]

        if message_id:
            parts.append("message_id = ?")
            params.append(message_id)
        if last_error:
            parts.append("last_error = ?")
            params.append(last_error)
        if increment_attempts:
            parts.append("attempts = attempts + 1")
        if status == "sent":
            parts.append("sent_at = ?")
            params.append(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())

        params.append(queue_id)
        self._conn.execute(
            f"UPDATE outbound_messages SET {', '.join(parts)} WHERE queue_id = ?",
            params,
        )
        self._conn.commit()

    def get_outbound(self, queue_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM outbound_messages WHERE queue_id = ?", (queue_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "queue_id": row["queue_id"],
            "created_at": row["created_at"],
            "status": row["status"],
            "attempts": row["attempts"],
            "last_error": row["last_error"],
            "sent_at": row["sent_at"],
            "message_id": row["message_id"],
        }

    def update_worker_health(
        self,
        connection_state: str | None = None,
        last_send_at: str | None = None,
    ) -> None:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO worker_health
               (id, last_heartbeat, last_send_at, connection_state)
               VALUES (1, ?, ?, ?)""",
            (now, last_send_at, connection_state or "unknown"),
        )
        self._conn.commit()

    def get_worker_health(self) -> dict:
        row = self._conn.execute(
            "SELECT * FROM worker_health WHERE id = 1"
        ).fetchone()
        if not row:
            return {"alive": False, "last_heartbeat": None, "connection_state": "no_worker"}
        return {
            "alive": True,
            "last_heartbeat": row["last_heartbeat"],
            "last_send_at": row["last_send_at"],
            "connection_state": row["connection_state"],
        }
