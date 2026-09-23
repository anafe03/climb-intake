"""Unit tests for the deterministic guardrail layer. No network."""
from app.models import Category, EscalationReason, Extraction, Customer, Urgency
from app.rules import apply_escalation_rules, rules_only_extraction


def _base(category=Category.other, urgency=Urgency.low, escalate=False, conf=0.5):
    return Extraction(customer=Customer(), customer_reason="", category=category, category_confidence=conf,
                      category_reason="", urgency=urgency, urgency_signals=[], urgency_reason="",
                      escalate=escalate, escalation_reasons=[], escalation_reason_text="",
                      summary="", rationale="")


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


def test_spam_suppression_undoes_a_keyword_escalation_and_leaves_no_net_change():
    """Marketing copy that name-drops GDPR trips the compliance rule; spam suppression must undo it.

    Found live on a vendor solicitation reading 'GDPR-compliant'. The audit trail keeps every step,
    but the shipped answer must equal what the model said.
    """
    text = "Scale your pipeline with our verified B2B lead lists! 40,000 contacts, GDPR-compliant, first 500 free."
    model_answer = _base(category=Category.spam, urgency=Urgency.low, escalate=False, conf=0.9)
    out, hits, overrides = apply_escalation_rules(text, model_answer)
    assert (out.category, out.urgency, out.escalate) == (Category.spam, Urgency.low, False)
    assert any("compliance_request" in o for o in overrides)   # it did fire
    assert any("spam.suppress" in o for o in overrides)        # and was undone


def test_keyword_layer_reads_signature_lines_in_any_language():
    """A signed-off ticket names its sender even when the body is not English.

    Found live: a Spanish billing ticket ending "— Carlos Mendoza, Grupo Andino" was reported as
    "nothing identifies the sender" because the company regex only looked for "from"/"at".
    """
    es = rules_only_extraction("Hola, nos facturaron dos veces la suscripción de octubre. Gracias. — Carlos Mendoza, Grupo Andino")
    assert es.customer.name == "Grupo Andino" and es.customer.contact_name == "Carlos Mendoza"
    assert es.customer.confidence == 1.0

    en = rules_only_extraction("We were double-billed again. Please fix. - Dana Whitfield, Acme Logistics")
    assert en.customer.name == "Acme Logistics" and en.customer.contact_name == "Dana Whitfield"

    # An em-dash that is not a signature must not invent a customer.
    plain = rules_only_extraction("The export button is broken — it returns a 500 every time.")
    assert plain.customer.name is None and plain.customer.confidence == 0.0


def test_category_and_customer_confidences_are_independent():
    """They were the same local variable for a while, so the customer guess silently overwrote the
    category score. Symptom: spam scored 0.45 instead of 0.85, spam-suppression stopped firing, and
    tickets fell below the 0.50 threshold into human-review. Caught by looking at the queue board.
    """
    spam = rules_only_extraction(
        "Scale your pipeline with our verified B2B lead lists! 40,000 enterprise data contacts, "
        "GDPR-compliant, first 500 free. Reply LEADS to get started."
    )
    assert spam.category is Category.spam
    assert spam.category_confidence == 0.85, "category confidence was clobbered by the customer guess"
    assert spam.customer.confidence != spam.category_confidence, "the two must not track each other"

    # And the downstream consequence: suppression depends on the category score being right.
    out, _, overrides = apply_escalation_rules(
        "Our verified B2B lead lists are GDPR-compliant, first 500 free. Reply LEADS to get started.", spam
    )
    assert out.escalate is False and out.urgency is Urgency.low
    assert any("spam.suppress" in o for o in overrides)


def test_no_gold_ticket_falls_below_the_review_threshold_by_accident():
    """A category score under 0.50 diverts to human-review. That should be rare and deliberate."""
    from tests.gold import load_gold
    low = [(r["id"], rules_only_extraction(r["text"]).category_confidence) for r in load_gold()]
    diverted = [(i, c) for i, c in low if c < 0.5]
    assert len(diverted) <= 6, f"too many tickets below the review threshold: {diverted}"


def test_exposure_to_the_wrong_audience_escalates_not_just_exposure_to_us():
    """Found by gold edge-33. The original pattern only caught "someone else's data reached us" and
    required "exposed" and "data" to be adjacent, so "exposed our internal cost data to everyone in
    the workspace" matched nothing and the escalation was missed in keyword mode.
    """
    leak_out = "A permissions change we made last week seems to have exposed our internal cost data to everyone in the workspace, including contractors."
    out, hits, _ = apply_escalation_rules(leak_out, _base())
    assert out.escalate and EscalationReason.data_exposure in out.escalation_reasons

    leak_in = "I was able to see another company's customer records when I exported our data."
    out2, _, _ = apply_escalation_rules(leak_in, _base())
    assert out2.escalate

    # The widened pattern must not turn every mention of permissions into an incident.
    for benign in ["Where do I change permissions for a new teammate?",
                   "Can you document how role permissions inherit?",
                   "We were double-billed for March on invoice #88213."]:
        clean, hits, _ = apply_escalation_rules(benign, _base())
        assert not clean.escalate, f"false positive on: {benign}"
