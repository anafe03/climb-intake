"""Cold-start race: many threads hit a fresh audit DB at once.

Before the init lock, `PRAGMA journal_mode=WAL` could race with other connections and a thread got
`sqlite3.OperationalError: database is locked`. Observed twice in the API tests; NOT reproducible on
demand (0/15 runs of the old code failed here). The fix removes the window by construction: init runs
on a single connection under a lock before any other thread opens the file. This test pins the
scenario so a regression that reintroduces the window has somewhere to show up."""
from concurrent.futures import ThreadPoolExecutor

from app import audit
from app.models import TicketIn
from app.pipeline import process


def test_fresh_db_survives_concurrent_first_writes(tmp_path, monkeypatch):
    for round_ in range(5):  # five cold files, 16 threads each
        monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / f"fresh{round_}.db"))
        audit._initialised.clear()
        with ThreadPoolExecutor(max_workers=16) as ex:
            decisions = list(ex.map(lambda i: process(TicketIn(text=f"Refund invoice #{i}.")), range(64)))
        assert len({d.id for d in decisions}) == 64
        assert audit.total() == 64
