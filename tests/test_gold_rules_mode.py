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
