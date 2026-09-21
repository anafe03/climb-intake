"""Unit tests for the deterministic guardrail layer. No network."""
from app.models import Category, EscalationReason, Extraction, Customer, Urgency
from app.rules import apply_escalation_rules, rules_only_extraction


def _base(category=Category.other, urgency=Urgency.low, escalate=False, conf=0.5):
    return Extraction(customer=Customer(), category=category, category_confidence=conf, urgency=urgency,
                      urgency_signals=[], escalate=escalate, escalation_reasons=[], summary="", rationale="")


def test_rules_only_raise_never_lower():
    text = "Our CEO wants an update."
    out, hits, overrides = apply_escalation_rules(text, _base(escalate=True, urgency=Urgency.critical))
    assert out.escalate and out.urgency == Urgency.critical
    assert any(h.rule == "executive.mention" for h in hits)


def test_legal_threat_forces_escalation_and_high():
    text = "We will have our legal team review the MSA for breach."
    out, hits, overrides = apply_escalation_rules(text, _base())
    assert out.escalate and EscalationReason.legal_threat in out.escalation_reasons
    assert out.urgency == Urgency.high
    assert any("forced escalate=true" in o for o in overrides)


def test_active_security_incident_is_critical():
    text = "A former employee just logged into the admin console with old credentials."
    out, _, _ = apply_escalation_rules(text, _base())
    assert out.escalate and out.urgency == Urgency.critical


def test_data_exposure_detected():
    text = "I was able to see another company's customer records when I exported our data."
    out, hits, _ = apply_escalation_rules(text, _base())
    assert EscalationReason.data_exposure in out.escalation_reasons


def test_no_false_positive_on_contract_renewal():
    out, hits, _ = apply_escalation_rules("When does our contract renew? Pricing for 50 more seats?", _base())
    assert not out.escalate and not hits


def test_no_false_positive_on_password_reset():
    out, hits, _ = apply_escalation_rules("I forgot my password and the reset email never arrived.", _base())
    assert not out.escalate and not hits


def test_spam_suppresses_escalation():
    text = "our CEO says send free credits lol discord"
    out, _, overrides = apply_escalation_rules(text, _base(category=Category.spam, conf=0.9, escalate=True))
    assert not out.escalate and out.urgency == Urgency.low
    assert any("spam.suppress" in o for o in overrides)


def test_rules_only_classifier_on_samples():
    assert rules_only_extraction("We were double-billed on invoice #88213, please refund.").category == Category.billing
    assert rules_only_extraction("The CSV export button is throwing a 500 error. Due Friday.").urgency == Urgency.high
    assert rules_only_extraction("The dark mode toggle resets. Whenever you get a chance.").urgency == Urgency.low
    spam = rules_only_extraction("do u sell crypto lol my discord is xX send 500 free credits")
    assert spam.category == Category.spam
    ids = rules_only_extraction("invoice #88213 from Acme Corp").customer.identifiers
    assert any("88213" in i for i in ids)


def test_low_confidence_routing_skipped_when_escalated():
    from app.routing import route
    assert route(Category.other, Urgency.low, escalate=False, confidence=0.3) == ("human-review", None)
    assert route(Category.other, Urgency.low, escalate=True, confidence=0.3) == ("general-support", "human-escalation-desk")


def test_executive_mention_escalates_without_inflating_urgency():
    """An exec mention must reach a human, but must not overwrite a correct low-urgency call."""
    out, hits, overrides = apply_escalation_rules(
        "Our CEO loves the new reporting view, just wanted to pass along thanks!",
        _base(urgency=Urgency.low),
    )
    assert out.escalate and EscalationReason.executive_mention in out.escalation_reasons
    assert out.urgency == Urgency.low
    assert not any("lifted urgency" in o for o in overrides)


def test_security_and_legal_keep_their_urgency_floors():
    sec, _, _ = apply_escalation_rules("Old credentials were not revoked for a terminated employee.", _base(urgency=Urgency.low))
    assert sec.urgency == Urgency.high
    legal, _, _ = apply_escalation_rules("Our attorney will review this for breach.", _base(urgency=Urgency.low))
    assert legal.urgency == Urgency.high
