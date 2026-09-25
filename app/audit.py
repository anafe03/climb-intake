"""Audit log: every routing decision is persisted to SQLite and emitted as a JSON log line."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from . import pricing
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

# Idempotency is enforced here, not in application logic. A check-then-insert in the request path
# races: two concurrent resubmits of the same ticket both read "absent" and both insert.
UNIQUE_EXTERNAL = """
CREATE UNIQUE INDEX IF NOT EXISTS idx_decisions_external
  ON decisions(source, external_id) WHERE external_id IS NOT NULL;
"""

# Rows predating the unique index may contain duplicates; keep the earliest of each group.
DEDUPE = """
DELETE FROM decisions WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY source, external_id ORDER BY created_at) rn
    FROM decisions WHERE external_id IS NOT NULL
  ) WHERE rn > 1
);
"""


def db_path() -> Path:
    p = Path(os.environ.get("AUDIT_DB_PATH", "./data/audit.db"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


_initialised: set[str] = set()
_init_lock = threading.Lock()


def _ensure_initialised(path: Path) -> None:
    """Run once per process per DB file, under a lock.

    `PRAGMA journal_mode=WAL` needs an exclusive lock on the file. Without the lock, the first burst
    of concurrent requests on a fresh DB races here and one thread gets "database is locked"
    (found by tests/test_api.py::test_upload_* on a fresh per-test DB).
    """
    key = str(path)
    if key in _initialised:
        return
    with _init_lock:
        if key in _initialised:
            return
        conn = sqlite3.connect(path, timeout=10.0)
        try:
            # WAL lets readers proceed while one writer commits. Persistent on the file.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)
            removed = conn.executescript(DEDUPE) and None
            removed = conn.total_changes
            conn.executescript(UNIQUE_EXTERNAL)
            conn.commit()
            if removed:
                log.warning(json.dumps({"event": "audit_dedupe_on_startup", "rows_removed": removed}))
        finally:
            conn.close()
        _initialised.add(key)


@contextmanager
def connect():
    path = db_path()
    _ensure_initialised(path)
    # timeout: wait for the writer lock instead of raising "database is locked" under concurrency.
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA synchronous=NORMAL")  # per-connection; safe under WAL
        yield conn
        conn.commit()
    finally:
        conn.close()


def record(d: Decision) -> Decision:
    """Persist the decision and return the authoritative one.

    If another writer won the race for this (source, external_id), the insert is ignored and the
    winner is returned, so every caller sees the same decision and the queues count it once.
    """
    with connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO decisions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                d.id, d.created_at, d.ticket.source, d.ticket.external_id, d.ticket.text,
                d.mode, d.model, d.extraction.category.value, d.extraction.urgency.value,
                int(d.extraction.escalate), d.queue, d.escalation_queue, d.latency_ms,
                d.model_dump_json(),
            ),
        )
        if cur.rowcount == 0:
            row = conn.execute(
                "SELECT decision_json FROM decisions WHERE source=? AND external_id=?",
                (d.ticket.source, d.ticket.external_id),
            ).fetchone()
            if row:
                winner = Decision.model_validate_json(row["decision_json"])
                log.info(json.dumps({"event": "routing_decision_deduplicated",
                                     "discarded_id": d.id, "kept_id": winner.id,
                                     "source": d.ticket.source, "external_id": d.ticket.external_id}))
                return winner
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
    return d


def _hydrate(raw: str) -> Decision:
    """Rebuild a stored decision, pricing it if it was written before costs were recorded.

    Older rows have the token counts but no `cost_usd`. Deriving it on read means the whole history
    is comparable without a migration, and the rate card still lives in exactly one place.
    """
    d = Decision.model_validate_json(raw)
    if d.usage and "cost_usd" not in d.usage:
        c = pricing.cost_usd(d.usage, d.model)
        if c is not None:
            d.usage["cost_usd"] = round(c, 6)
    return d


def get(decision_id: str) -> Decision | None:
    with connect() as conn:
        row = conn.execute("SELECT decision_json FROM decisions WHERE id=?", (decision_id,)).fetchone()
    return _hydrate(row["decision_json"]) if row else None



def list_recent(limit: int = 100, queue: str | None = None) -> list[Decision]:
    q = "SELECT decision_json FROM decisions"
    args: tuple = ()
    if queue:
        q += " WHERE queue=? OR escalation_queue=?"
        args = (queue, queue)
    q += " ORDER BY created_at DESC LIMIT ?"
    with connect() as conn:
        rows = conn.execute(q, args + (limit,)).fetchall()
    return [_hydrate(r["decision_json"]) for r in rows]


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


def clear(keep_source: str | None = None) -> None:
    """Delete decisions. With keep_source, rows from that source survive (e.g. typed-in tickets)."""
    with connect() as conn:
        if keep_source:
            conn.execute("DELETE FROM decisions WHERE source IS NOT ? ", (keep_source,))
        else:
            conn.execute("DELETE FROM decisions")
    _initialised.discard(str(db_path()))
