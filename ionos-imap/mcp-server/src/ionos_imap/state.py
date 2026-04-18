"""SQLite state store for envelope caching and worker health."""

from __future__ import annotations

import datetime
import json
import logging
import os
import sqlite3
from typing import Any

log = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS envelopes (
    uid TEXT NOT NULL,
    folder TEXT NOT NULL,
    subject TEXT,
    from_name TEXT,
    from_email TEXT,
    date TEXT,
    flags TEXT,          -- JSON array
    size_bytes INTEGER,
    has_attachments INTEGER,
    message_id TEXT,
    in_reply_to TEXT,
    to_addrs TEXT,       -- JSON array
    cc_addrs TEXT,       -- JSON array
    seen_at_local TEXT,
    PRIMARY KEY (uid, folder)
);

CREATE INDEX IF NOT EXISTS idx_envelopes_folder_date ON envelopes(folder, date DESC);
CREATE INDEX IF NOT EXISTS idx_envelopes_folder_unseen ON envelopes(folder, flags) WHERE flags NOT LIKE '%Seen%';

CREATE TABLE IF NOT EXISTS folders (
    name TEXT PRIMARY KEY,
    uidvalidity INTEGER,
    uidnext INTEGER,
    last_synced TEXT
);

CREATE TABLE IF NOT EXISTS worker_health (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_heartbeat TEXT,
    last_idle_at TEXT,
    connection_state TEXT,
    watched_folders TEXT  -- JSON array
);
"""


class StateStore:
    """SQLite-backed local state store for envelope caching."""

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

    def upsert_envelope(self, env: dict) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO envelopes
               (uid, folder, subject, from_name, from_email, date, flags,
                size_bytes, has_attachments, message_id, in_reply_to,
                to_addrs, cc_addrs, seen_at_local)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                env["uid"],
                env["folder"],
                env.get("subject", ""),
                env.get("from", {}).get("name"),
                env.get("from", {}).get("email", ""),
                env.get("date", ""),
                json.dumps(env.get("flags", [])),
                env.get("size_bytes", 0),
                1 if env.get("has_attachments") else 0,
                env.get("message_id", ""),
                env.get("in_reply_to"),
                json.dumps([a for a in env.get("to", [])]),
                json.dumps([a for a in env.get("cc", [])]),
                datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def upsert_envelopes(self, envelopes: list[dict]) -> None:
        for env in envelopes:
            self.upsert_envelope(env)

    def list_envelopes(
        self,
        folder: str = "INBOX",
        since: str | None = None,
        unseen_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        query = "SELECT * FROM envelopes WHERE folder = ?"
        params: list[Any] = [folder]

        if since:
            query += " AND date >= ?"
            params.append(since)
        if unseen_only:
            query += " AND flags NOT LIKE ?"
            params.append('%\\\\Seen%')

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_envelope(r) for r in rows]

    def _row_to_envelope(self, row: sqlite3.Row) -> dict:
        return {
            "uid": row["uid"],
            "folder": row["folder"],
            "date": row["date"],
            "from": {"name": row["from_name"], "email": row["from_email"]},
            "to": json.loads(row["to_addrs"]) if row["to_addrs"] else [],
            "cc": json.loads(row["cc_addrs"]) if row["cc_addrs"] else [],
            "subject": row["subject"],
            "flags": json.loads(row["flags"]) if row["flags"] else [],
            "size_bytes": row["size_bytes"],
            "has_attachments": bool(row["has_attachments"]),
            "message_id": row["message_id"],
            "in_reply_to": row["in_reply_to"],
        }

    def get_folder_state(self, folder: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM folders WHERE name = ?", (folder,)
        ).fetchone()
        if not row:
            return None
        return {
            "name": row["name"],
            "uidvalidity": row["uidvalidity"],
            "uidnext": row["uidnext"],
            "last_synced": row["last_synced"],
        }

    def update_folder_state(
        self, folder: str, uidvalidity: int, uidnext: int
    ) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO folders (name, uidvalidity, uidnext, last_synced)
               VALUES (?, ?, ?, ?)""",
            (
                folder,
                uidvalidity,
                uidnext,
                datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def purge_folder(self, folder: str) -> int:
        """Remove all cached envelopes for a folder (e.g., after UIDVALIDITY change)."""
        cursor = self._conn.execute(
            "DELETE FROM envelopes WHERE folder = ?", (folder,)
        )
        self._conn.commit()
        return cursor.rowcount

    def update_worker_health(
        self,
        last_heartbeat: str | None = None,
        last_idle_at: str | None = None,
        connection_state: str | None = None,
        watched_folders: list[str] | None = None,
    ) -> None:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO worker_health
               (id, last_heartbeat, last_idle_at, connection_state, watched_folders)
               VALUES (1, ?, ?, ?, ?)""",
            (
                last_heartbeat or now,
                last_idle_at,
                connection_state or "unknown",
                json.dumps(watched_folders or []),
            ),
        )
        self._conn.commit()

    def get_worker_health(self) -> dict:
        row = self._conn.execute(
            "SELECT * FROM worker_health WHERE id = 1"
        ).fetchone()
        if not row:
            return {
                "alive": False,
                "last_heartbeat": None,
                "last_idle_at": None,
                "connection_state": "no_worker",
                "folder_states": [],
            }
        return {
            "alive": True,
            "last_heartbeat": row["last_heartbeat"],
            "last_idle_at": row["last_idle_at"],
            "connection_state": row["connection_state"],
            "folder_states": json.loads(row["watched_folders"])
                if row["watched_folders"]
                else [],
        }
