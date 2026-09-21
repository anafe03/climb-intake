"""Cold-start race: many threads hit a fresh audit DB at once.

Before the init lock, `PRAGMA journal_mode=WAL` raced with other connections and one thread got
`sqlite3.OperationalError: database is locked`. This test fails reliably without the lock."""
from concurrent.futures import ThreadPoolExecutor

from app import audit
from app.models import TicketIn
from app.pipeline import process


def test_fresh_db_survives_concurrent_first_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "fresh.db"))
    audit._initialised.clear()
    with ThreadPoolExecutor(max_workers=16) as ex:
        decisions = list(ex.map(lambda i: process(TicketIn(text=f"Refund invoice #{i}.")), range(64)))
    assert len({d.id for d in decisions}) == 64
    assert audit.total() == 64
