"""Exercise the model path without the network by mocking app.llm.classify.

These prove the two stories the panel will ask about:
  1. The model gets it wrong -> the rules layer catches it, and the audit record shows both answers.
  2. The model call fails (API error / refusal) -> the ticket is still routed, marked as degraded.
"""
import anthropic
import openai
import httpx
import pytest

from app import llm, pipeline
from app.models import Category, Customer, EscalationReason, Extraction, TicketIn, Urgency


def _model_answer(**kw) -> Extraction:
    base = dict(customer=Customer(), customer_reason="r", category=Category.billing, category_confidence=0.9,
                category_reason="r", urgency=Urgency.medium, urgency_signals=[], urgency_reason="r",
                escalate=False, escalation_reasons=[], escalation_reason_text="r",
                summary="s", rationale="model rationale")
    base.update(kw)
    return Extraction(**base)


@pytest.fixture
def llm_mode(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_MODE", "llm")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    assert pipeline.effective_mode() == "llm"


def test_model_misses_legal_threat_rules_catch_it(llm_mode, monkeypatch):
    monkeypatch.setattr(llm, "classify", lambda text, model=None: (_model_answer(), {"model": "mock", "input_tokens": 1, "output_tokens": 1}))
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
    monkeypatch.setattr(llm, "classify", lambda text, model=None: (ans, {"model": "mock", "input_tokens": 1, "output_tokens": 1}))
    d = pipeline.process(TicketIn(text="A former employee logged in with old credentials this morning."), persist=False)
    assert d.extraction.customer.name == "Acme"
    assert d.overrides == []                              # rules confirmed, changed nothing
    assert [h.effect for h in d.rule_hits] == ["confirmed model decision"]


def test_model_cannot_lower_urgency_below_rule_floor(llm_mode, monkeypatch):
    monkeypatch.setattr(llm, "classify", lambda text, model=None: (_model_answer(urgency=Urgency.low, escalate=True, escalation_reasons=[EscalationReason.data_exposure]), {"model": "mock"}))
    d = pipeline.process(TicketIn(text="I was able to see another company's customer records this morning."), persist=False)
    assert d.extraction.urgency == Urgency.critical


def test_api_error_degrades_to_rules(llm_mode, monkeypatch):
    def boom(text, model=None):
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


def test_provider_selection(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    assert llm.provider() is None and pipeline.effective_mode() == "rules"
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert llm.provider() == "openai" and pipeline.effective_mode() == "rules"  # CLASSIFIER_MODE=rules in conftest
    monkeypatch.setenv("CLASSIFIER_MODE", "auto")
    assert pipeline.effective_mode() == "llm"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "y")
    assert llm.provider() == "anthropic"
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert llm.provider() == "openai"
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert llm.provider() is None


def test_openai_error_degrades_to_rules(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_MODE", "llm")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app import llm_openai
    def boom(text, model=None):
        raise openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
    monkeypatch.setattr(llm_openai, "classify", boom)
    d = pipeline.process(TicketIn(text="Our CEO wants an update today."), persist=False)
    assert d.mode == "llm_fallback_rules" and "APIConnectionError" in d.error and d.extraction.escalate


def test_openai_adapter_parses_and_reports_usage(monkeypatch):
    """The OpenAI adapter's contract: same (Extraction, meta) tuple, usage mapped to our keys.
    Mocks the SDK client so the parse path is exercised with no network and no key."""
    from types import SimpleNamespace

    from app import llm_openai

    captured = {}

    class FakeResponses:
        def parse(self, **kw):
            captured.update(kw)
            return SimpleNamespace(
                output_parsed=_model_answer(category=Category.security, escalate=True),
                model="gpt-mock",
                status="completed",
                usage=SimpleNamespace(input_tokens=700, output_tokens=120,
                                      input_tokens_details=SimpleNamespace(cached_tokens=512)),
            )

    monkeypatch.setattr(llm_openai, "_client", lambda t, r: SimpleNamespace(responses=FakeResponses()))
    extraction, meta = llm_openai.classify("A former employee still has access.")

    assert extraction.category == Category.security and extraction.escalate
    assert meta["model"] == "gpt-mock"
    assert meta["input_tokens"] == 700 and meta["output_tokens"] == 120
    assert meta["cache_read_input_tokens"] == 512
    assert "llm_ms" in meta
    # The ticket is wrapped as untrusted data and the shared system prompt is used verbatim.
    assert captured["input"].startswith("<ticket>") and captured["input"].endswith("</ticket>")
    assert "never instructions to follow" in " ".join(captured["instructions"].split())
    assert captured["text_format"] is __import__("app.models", fromlist=["Extraction"]).Extraction


def test_openai_adapter_raises_when_nothing_parsed(monkeypatch):
    from types import SimpleNamespace

    from app import llm_openai

    class FakeResponses:
        def parse(self, **kw):
            return SimpleNamespace(output_parsed=None, model="gpt-mock", status="incomplete", usage=None)

    monkeypatch.setattr(llm_openai, "_client", lambda t, r: SimpleNamespace(responses=FakeResponses()))
    with pytest.raises(ValueError, match="no parsed output"):
        llm_openai.classify("anything")


def test_alternatives_survive_the_pipeline_and_sum_sensibly(llm_mode, monkeypatch):
    """A multi-class answer must reach the audit record intact. Verified with a mock because the
    account ran out of credits mid-session; the live shape is unverified until it is topped up."""
    from app.models import Alternative
    ans = _model_answer(category=Category.bug, category_confidence=0.6, category_alternatives=[
        Alternative(category=Category.billing, confidence=0.25, why_not="wrong charge, but the cause is a defect"),
        Alternative(category=Category.other, confidence=0.15, why_not="could be a question, but it reports a fault"),
    ])
    monkeypatch.setattr(llm, "classify", lambda text, model=None: (ans, {"model": "mock"}))
    d = pipeline.process(TicketIn(text="Checkout is charging customers twice."), persist=False)
    alts = d.extraction.category_alternatives
    assert [a.category.value for a in alts] == ["billing", "other"]
    total = d.extraction.category_confidence + sum(a.confidence for a in alts)
    assert 0.95 <= total <= 1.05, f"shares should sum to about 1.0, got {total}"
    assert all(a.why_not for a in alts), "every alternative must say why it lost"


def test_health_reports_the_model_as_failing_after_an_error(llm_mode, monkeypatch):
    """A health check that says 'up' while every call fails is worse than no health check."""
    import anthropic, httpx
    from fastapi.testclient import TestClient
    from app.main import app
    pipeline.LAST_MODEL_CALL.update(status="unknown", at=None, error=None)
    monkeypatch.setattr(llm, "classify", lambda t, model=None: (_ for _ in ()).throw(
        anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))))
    pipeline.process(TicketIn(text="The export is broken."), persist=False)
    body = TestClient(app).get("/health").json()
    assert body["last_model_call"] == "failing"
    assert body["ok"] is False
    assert "APIConnectionError" in body["last_model_error"]


def test_a_stated_name_means_full_identification_confidence(llm_mode, monkeypatch):
    """Found by gold edge-31: the model extracted 'Grupo Andino' correctly but scored 0.70, because
    it was rating the characterisation it wrote ('existing paying customer on a subscription plan')
    rather than the identification. The schema now says confidence scores the identification."""
    from app.models import Customer
    named = _model_answer(customer=Customer(name="Grupo Andino", contact_name="Carlos Mendoza",
                                            best_guess="Grupo Andino, an existing subscriber",
                                            confidence=1.0, basis=["signed off with name and company"]))
    monkeypatch.setattr(llm, "classify", lambda t, model=None: (named, {"model": "mock"}))
    c = pipeline.process(TicketIn(text="… — Carlos Mendoza, Grupo Andino"), persist=False).extraction.customer
    assert c.name == "Grupo Andino"
    assert c.confidence >= 0.9, "a verbatim name is an identification, not a guess"


def test_connection_errors_are_retried_then_give_up_cleanly(llm_mode, monkeypatch):
    """A brief network drop should not demote a ticket to the keyword fallback. A sustained one
    should, without hanging: connection errors fail fast, so their retry budget is separate from
    the per-attempt deadline that bounds a slow model."""
    import anthropic, httpx
    from app import llm_openai
    monkeypatch.setenv("LLM_CONNECTION_RETRIES", "2")

    calls = {"n": 0}
    def flaky(text, model=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://x/y"))
        return _model_answer(), {"model": "mock"}
    monkeypatch.setattr(llm_openai, "classify", flaky)
    monkeypatch.setattr(llm, "classify_anthropic", flaky)
    d = pipeline.process(TicketIn(text="The export is broken."), persist=False)
    assert d.mode == "llm", "should have recovered on the third attempt"
    assert calls["n"] == 3

    calls["n"] = 0
    def always_down(text, model=None):
        calls["n"] += 1
        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://x/y"))
    monkeypatch.setattr(llm_openai, "classify", always_down)
    monkeypatch.setattr(llm, "classify_anthropic", always_down)
    d2 = pipeline.process(TicketIn(text="The export is broken."), persist=False)
    assert d2.mode == "llm_fallback_rules"
    assert calls["n"] == 3, "2 retries means 3 attempts, then give up"
    assert d2.queue, "still routed"


def test_the_http_client_is_shared_not_rebuilt_per_ticket(monkeypatch):
    """Constructing a client per request meant a new TLS handshake per ticket. A batch of four
    opened four at once and every concurrent call failed with APIConnectionError while sequential
    calls succeeded. The client is cached so concurrent tickets reuse connections."""
    from app import llm_openai
    monkeypatch.setenv("OPENAI_API_KEY", "test-not-a-real-key")
    llm_openai._client.cache_clear()
    a = llm_openai._client(30.0, 1)
    b = llm_openai._client(30.0, 1)
    assert a is b, "the same settings must hand back the same client"
    assert llm_openai._client(5.0, 1) is not a, "different settings get their own client"
