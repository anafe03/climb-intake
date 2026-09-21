"""Full-pipeline eval against the gold set with Claude. Skipped without credentials.
Run: TEST_CLASSIFIER_MODE=llm pytest tests/test_gold_llm_mode.py -s"""
import os
import pytest

from app.models import TicketIn
from app.pipeline import effective_mode, process
from tests.gold import load_gold, score_one, summarize

pytestmark = pytest.mark.skipif(
    os.environ.get("TEST_CLASSIFIER_MODE") != "llm" or not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
    reason="set TEST_CLASSIFIER_MODE=llm and an API key to run the model eval",
)


def test_llm_mode_gold():
    assert effective_mode() == "llm"
    results = [score_one(row, process(TicketIn(text=row["text"]), persist=False)) for row in load_gold()]
    s = summarize(results)
    print(s)
    assert s["missed_escalations"] == [], s
    assert s["category_accuracy"] >= 0.85, s
    assert s["urgency_accuracy"] >= 0.80, s
    assert s["customer_accuracy"] >= 0.90, s
