"""The guardrail layer alone must never miss a mandatory escalation on the gold set.
This is the safety-net claim: even if the model is down, nothing security/legal/exec slips through."""
from app.models import TicketIn
from app.pipeline import process
from tests.gold import load_gold, score_one, summarize


def test_rules_mode_escalation_recall_is_perfect():
    results = [score_one(row, process(TicketIn(text=row["text"]), persist=False)) for row in load_gold()]
    s = summarize(results)
    assert s["missed_escalations"] == [], s
    assert s["escalation_recall"] == 1.0


def test_rules_mode_never_produces_empty_queue():
    for row in load_gold():
        d = process(TicketIn(text=row["text"]), persist=False)
        assert d.queue
        assert d.mode == "rules"


def test_every_guess_carries_its_basis():
    """A scored guess with no stated basis is unauditable. Confidence 0 is the only exception."""
    for row in load_gold():
        c = process(TicketIn(text=row["text"]), persist=False).extraction.customer
        assert c.basis or c.confidence == 0.0, f"{row['id']}: confidence {c.confidence} with no basis"
        assert 0.0 <= c.confidence <= 1.0
        if c.name:
            assert c.confidence >= 0.9, f"{row['id']}: named customer but confidence {c.confidence}"


def test_a_guess_never_becomes_a_stated_name():
    """The whole safety argument for D26 rests on this: inference never enters `name`."""
    for row in load_gold():
        x = process(TicketIn(text=row["text"]), persist=False).extraction
        if x.customer.name:
            assert x.customer.name.lower() in row["text"].lower(), f"{row['id']}: invented a name"
