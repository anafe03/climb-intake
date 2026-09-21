"""Audit log: every routing decision is persisted to SQLite and emitted as a JSON log line."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .models import Decision

log = logging.getLogger("climb.audit")

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  source TEXT,
  external_id TEXT,
  ticket_text TEXT NOT NULL,
  mode TEXT NOT NULL,
  model TEXT,
  category TEXT NOT NULL,
  urgency TEXT NOT NULL,
  escalate INTEGER NOT NULL,
  queue TEXT NOT NULL,
  escalation_queue TEXT,
  latency_ms INTEGER,
  decision_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_queue ON decisions(queue);
"""


def db_path() -> Path:
    p = Path(os.environ.get("AUDIT_DB_PATH", "./data/audit.db"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


_initialised: set[str] = set()


@contextmanager
def connect():
    path = db_path()
    # timeout: wait for a writer lock instead of raising "database is locked" under concurrency.
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        if str(path) not in _initialised:
            # WAL lets readers proceed while one writer commits; NORMAL sync is safe under WAL.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.executescript(SCHEMA)
            _initialised.add(str(path))
        yield conn
        conn.commit()
    finally:
        conn.close()


def record(d: Decision) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                d.id, d.created_at, d.ticket.source, d.ticket.external_id, d.ticket.text,
                d.mode, d.model, d.extraction.category.value, d.extraction.urgency.value,
                int(d.extraction.escalate), d.queue, d.escalation_queue, d.latency_ms,
                d.model_dump_json(),
            ),
        )
    # Structured log line for cloud log sinks (Cloud Logging / CloudWatch parse JSON on stdout).
    log.info(json.dumps({
        "event": "routing_decision",
        "id": d.id,
        "mode": d.mode,
        "category": d.extraction.category.value,
        "urgency": d.extraction.urgency.value,
        "escalate": d.extraction.escalate,
        "reasons": [r.value for r in d.extraction.escalation_reasons],
        "queue": d.queue,
        "escalation_queue": d.escalation_queue,
        "rule_hits": [h.rule for h in d.rule_hits],
        "overrides": d.overrides,
        "latency_ms": d.latency_ms,
        "usage": d.usage,
    }))


def get(decision_id: str) -> Decision | None:
    with connect() as conn:
        row = conn.execute("SELECT decision_json FROM decisions WHERE id=?", (decision_id,)).fetchone()
    return Decision.model_validate_json(row["decision_json"]) if row else None


def list_recent(limit: int = 100, queue: str | None = None) -> list[Decision]:
    q = "SELECT decision_json FROM decisions"
    args: tuple = ()
    if queue:
        q += " WHERE queue=? OR escalation_queue=?"
        args = (queue, queue)
    q += " ORDER BY created_at DESC LIMIT ?"
    with connect() as conn:
        rows = conn.execute(q, args + (limit,)).fetchall()
    return [Decision.model_validate_json(r["decision_json"]) for r in rows]


def total() -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]


def find_by_external(source: str, external_id: str) -> Decision | None:
    with connect() as conn:
        row = conn.execute("SELECT decision_json FROM decisions WHERE source=? AND external_id=? ORDER BY created_at DESC LIMIT 1", (source, external_id)).fetchone()
    return Decision.model_validate_json(row["decision_json"]) if row else None


def queue_counts() -> dict[str, int]:
    with connect() as conn:
        rows = conn.execute("SELECT queue, COUNT(*) c FROM decisions GROUP BY queue").fetchall()
        esc = conn.execute("SELECT escalation_queue q, COUNT(*) c FROM decisions WHERE escalation_queue IS NOT NULL GROUP BY escalation_queue").fetchall()
    counts = {r["queue"]: r["c"] for r in rows}
    for r in esc:
        counts[r["q"]] = counts.get(r["q"], 0) + r["c"]
    return counts


def clear() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM decisions")
    _initialised.discard(str(db_path()))
