"""Concurrent resubmits of the SAME (source, external_id) must yield exactly one decision.

The first implementation was a check-then-insert: two threads both read "not present", both
classified, both inserted. Observed live during a demo when a browser click overlapped a script
run, producing 15 rows for 10 sample tickets with two different urgencies for the same ticket."""
from concurrent.futures import ThreadPoolExecutor

from app import audit
from app.models import TicketIn
from app.pipeline import process


def test_same_external_id_concurrently_yields_one_row(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "race.db"))
    audit._initialised.clear()
    ticket = lambda _: TicketIn(text="We were double-billed on invoice #88213.", source="crm", external_id="T-1")
    with ThreadPoolExecutor(max_workers=12) as ex:
        decisions = list(ex.map(lambda i: process(ticket(i)), range(12)))
    assert audit.total() == 1, f"expected 1 audit row, got {audit.total()}"
    assert len({d.id for d in decisions}) == 1, "all callers must receive the same decision id"


def test_distinct_external_ids_are_not_collapsed(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "race2.db"))
    audit._initialised.clear()
    with ThreadPoolExecutor(max_workers=12) as ex:
        list(ex.map(lambda i: process(TicketIn(text=f"Invoice #{i} is wrong.", source="crm", external_id=f"T-{i}")), range(12)))
    assert audit.total() == 12


def test_no_external_id_means_no_dedupe(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "race3.db"))
    audit._initialised.clear()
    for _ in range(3):
        process(TicketIn(text="Same words, no id."))
    assert audit.total() == 3
