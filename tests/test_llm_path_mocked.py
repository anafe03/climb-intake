"""Exercise the model path without the network by mocking app.llm.classify.

These prove the two stories the panel will ask about:
  1. The model gets it wrong -> the rules layer catches it, and the audit record shows both answers.
  2. The model call fails (API error / refusal) -> the ticket is still routed, marked as degraded.
"""
import anthropic
import httpx
import pytest

from app import llm, pipeline
from app.models import Category, Customer, EscalationReason, Extraction, TicketIn, Urgency


def _model_answer(**kw) -> Extraction:
    base = dict(customer=Customer(), category=Category.billing, category_confidence=0.9, urgency=Urgency.medium,
                urgency_signals=[], escalate=False, escalation_reasons=[], summary="s", rationale="model rationale")
    base.update(kw)
    return Extraction(**base)


@pytest.fixture
def llm_mode(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_MODE", "llm")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    assert pipeline.effective_mode() == "llm"


def test_model_misses_legal_threat_rules_catch_it(llm_mode, monkeypatch):
    monkeypatch.setattr(llm, "classify", lambda text: (_model_answer(), {"model": "mock", "input_tokens": 1, "output_tokens": 1}))
    d = pipeline.process(TicketIn(text="If this isn't fixed our legal team will review the MSA for breach."), persist=False)
    assert d.mode == "llm" and d.model == "mock"
    assert d.llm_extraction.escalate is False            # what the model said
    assert d.extraction.escalate is True                 # what we shipped
    assert EscalationReason.legal_threat in d.extraction.escalation_reasons
    assert d.extraction.urgency == Urgency.high          # lifted from medium
    assert any("forced escalate=true" in o for o in d.overrides)
    assert d.escalation_queue == "human-escalation-desk"


def test_model_answer_is_kept_when_rules_agree(llm_mode, monkeypatch):
    ans = _model_answer(category=Category.security, urgency=Urgency.critical, escalate=True,
                        escalation_reasons=[EscalationReason.security_incident], customer=Customer(name="Acme"))
    monkeypatch.setattr(llm, "classify", lambda text: (ans, {"model": "mock", "input_tokens": 1, "output_tokens": 1}))
    d = pipeline.process(TicketIn(text="A former employee logged in with old credentials this morning."), persist=False)
    assert d.extraction.customer.name == "Acme"
    assert d.overrides == []                              # rules confirmed, changed nothing
    assert [h.effect for h in d.rule_hits] == ["confirmed model decision"]


def test_model_cannot_lower_urgency_below_rule_floor(llm_mode, monkeypatch):
    monkeypatch.setattr(llm, "classify", lambda text: (_model_answer(urgency=Urgency.low, escalate=True, escalation_reasons=[EscalationReason.data_exposure]), {"model": "mock"}))
    d = pipeline.process(TicketIn(text="I was able to see another company's customer records this morning."), persist=False)
    assert d.extraction.urgency == Urgency.critical


def test_api_error_degrades_to_rules(llm_mode, monkeypatch):
    def boom(text):
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    monkeypatch.setattr(llm, "classify", boom)
    d = pipeline.process(TicketIn(text="Our CEO wants an update on onboarding today."), persist=False)
    assert d.mode == "llm_fallback_rules"
    assert d.error and "APIConnectionError" in d.error
    assert d.extraction.escalate is True and d.queue     # still routed, still escalated


def test_refusal_degrades_to_rules(llm_mode, monkeypatch):
    def refuse(text):
        raise llm.RefusedError("model refused: policy")
    monkeypatch.setattr(llm, "classify", refuse)
    d = pipeline.process(TicketIn(text="The CSV export throws a 500. Due Friday."), persist=False)
    assert d.mode == "llm_fallback_rules" and d.extraction.category == Category.bug


def test_extraction_schema_is_structured_output_friendly():
    """Structured outputs reject some JSON Schema keywords. Keep the model schema plain."""
    schema = Extraction.model_json_schema()
    banned = {"minLength", "maxLength", "minimum", "maximum", "pattern", "format"}
    def walk(node):
        if isinstance(node, dict):
            assert not (banned & node.keys()), f"unsupported keyword in {node}"
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(schema)
