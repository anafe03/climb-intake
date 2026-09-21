"""Deterministic safety net that sits on top of the LLM.

Two jobs:
1. Escalation guardrails: regexes that can only RAISE the escalation flag, never lower it.
   The assignment says "low tolerance for missed escalations", so a false positive here is
   acceptable and a false negative is not.
2. Rules-only classification: a keyword heuristic used when no API key is present or the
   model call fails. It is deliberately simple and is documented as degraded mode.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .models import (
    Category,
    Customer,
    EscalationReason,
    Extraction,
    RuleHit,
    Urgency,
    max_urgency,
)


@dataclass(frozen=True)
class EscalationRule:
    name: str
    reason: EscalationReason
    pattern: re.Pattern
    urgency_floor: Urgency


def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE)


# Ordered: first match per rule is reported. Every rule can fire independently.
ESCALATION_RULES: list[EscalationRule] = [
    EscalationRule(
        "security.unauthorized_access",
        EscalationReason.security_incident,
        _rx(r"\b(unauthori[sz]ed|credentials?|revoked?|former employee|terminated employee|ex-employee|offboard(ed|ing)?|compromised|hacked|phish(ing|ed)?|malware|ransomware|brute.?force|session hijack|mfa|2fa|audit log)\b"),
        Urgency.high,
    ),
    EscalationRule(
        "security.vulnerability_report",
        EscalationReason.security_incident,
        _rx(r"\b(vulnerabilit(y|ies)|IDOR|CVE-\d+|sql injection|xss|cross.site|exploit|security (issue|flaw|hole|bug|contact)|responsible disclosure)\b"),
        Urgency.high,
    ),
    EscalationRule(
        "security.data_exposure",
        EscalationReason.data_exposure,
        _rx(r"(another (company|customer|tenant|org(anization)?)'?s?|other (companies|customers|tenants|orgs)'?|someone else'?s|not our) (customer )?(records|data|accounts?|information|invoices?|users?)|data (leak|breach|exposure)|leaked|exposed (data|records|pii)|permissions? issue"),
        Urgency.critical,
    ),
    EscalationRule(
        "legal.threat",
        EscalationReason.legal_threat,
        _rx(r"\b(legal team|legal action|lawyer|attorney|counsel|lawsuit|litigation|sue\b|suing|in breach|breach of|MSA\b|master services? agreement|arbitration|subpoena|cease and desist|small claims)"),
        Urgency.high,
    ),
    EscalationRule(
        "legal.compliance_request",
        EscalationReason.compliance_request,
        _rx(r"\b(GDPR|CCPA|HIPAA|DSAR|data subject|right to (be forgotten|erasure|deletion)|article 17|regulator|regulatory|data protection (authority|officer))\b"),
        Urgency.high,
    ),
    EscalationRule(
        "executive.mention",
        EscalationReason.executive_mention,
        _rx(r"\b(CEO|CFO|CTO|COO|CIO|CISO|CRO|CMO|founder|co-founder|VP\b|vice president|president|chief [a-z]+ officer|executive team|leadership team|board of directors|the board|general counsel)\b"),
        Urgency.medium,  # attention, not speed: a CEO compliment is not urgent
    ),
]

# Cues that an incident is active right now, used to lift security escalations to critical.
ACTIVE_INCIDENT = _rx(r"\b(logged in|logged into|this morning|right now|currently|still (has|have) access|we can see activity|was able to (see|access|view)|able to see|exported)\b")


def apply_escalation_rules(text: str, extraction: Extraction) -> tuple[Extraction, list[RuleHit], list[str]]:
    """Return a copy of `extraction` with escalation/urgency floors applied, plus an audit trail."""
    hits: list[RuleHit] = []
    overrides: list[str] = []
    out = extraction.model_copy(deep=True)

    for rule in ESCALATION_RULES:
        m = rule.pattern.search(text)
        if not m:
            continue
        floor = rule.urgency_floor
        if rule.reason in (EscalationReason.security_incident, EscalationReason.data_exposure) and ACTIVE_INCIDENT.search(text):
            floor = Urgency.critical
        effects = []
        if not out.escalate:
            out.escalate = True
            effects.append("escalate: false -> true")
            overrides.append(f"{rule.name} forced escalate=true (matched '{m.group(0)}')")
        if rule.reason not in out.escalation_reasons:
            out.escalation_reasons.append(rule.reason)
            effects.append(f"reason +{rule.reason.value}")
        lifted = max_urgency(out.urgency, floor)
        if lifted != out.urgency:
            overrides.append(f"{rule.name} lifted urgency {out.urgency.value} -> {lifted.value}")
            effects.append(f"urgency {out.urgency.value} -> {lifted.value}")
            out.urgency = lifted
        hits.append(RuleHit(rule=rule.name, reason=rule.reason, matched=m.group(0), effect="; ".join(effects) or "confirmed model decision"))

    # Spam never escalates and never carries urgency, regardless of keyword noise.
    if out.category == Category.spam and out.category_confidence >= 0.8:
        if out.escalate:
            overrides.append("spam.suppress cleared escalation on high-confidence spam")
            hits.append(RuleHit(rule="spam.suppress", reason=None, matched="category=spam", effect="escalate: true -> false"))
        out.escalate = False
        out.escalation_reasons = []
        out.urgency = Urgency.low
    return out, hits, overrides


# ---------------------------------------------------------------------------
# Rules-only classifier (degraded mode). Keep it honest: it is a heuristic.
# ---------------------------------------------------------------------------

SPAM_SIGNALS = _rx(r"\b(free credits?|discord|crypto|bitcoin|mining|lol|lmao|my uncle|seo|backlinks?|5-star|guaranteed|click here|unsubscribe|casino|giveaway)\b")
BILLING = _rx(r"\b(invoice|charged?|billed?|billing|refund|payment|plan|pricing|subscription|renewal|renew|seats?|credit card|card on file|overcharg\w*|double.?bill\w*|cobr\w+|factura|suscripci[oó]n|reembols\w*|pago)\b")
BUG = _rx(r"\b(error|500|bug|broken|throwing|crash\w*|not working|doesn'?t work|resets?|fails?|failing|down\b|outage|button|toggle|export\b|dashboard|checkout|latency|429|timeout|slow)\b")
ONBOARDING = _rx(r"\b(onboard\w*|implementation|kickoff|set ?up|go.?live|migration)\b")
FEATURE = _rx(r"\b(feature request|would be great|can you add|raise (the|our) limit|increase (the|our) limit|support for|roadmap|integrat\w+)\b")
DEADLINE = _rx(r"\b(due (today|tomorrow|friday|monday|tuesday|wednesday|thursday|this week)|by (end of|eod|eow|friday|monday|tomorrow|today)|end of (day|week)|today|asap|urgent\w*|immediately|right away|deadline)\b")
LOW_PRIORITY = _rx(r"\b(whenever you get a chance|no rush|low priority|not urgent|when you can|minor)\b")
OUTAGE = _rx(r"\b(entire|whole|completely down|is down|been down|are down|outage|all (of )?our (users|team|customers|staff)|can'?t (work|log ?in|access))\b")
WIDESPREAD_MONEY = _rx(r"\b(customers?|users?|clients?)\b.*\b(twice|double|duplicate)\b|\b(twice|double|duplicate)\b.*\b(customers?|users?|clients?)\b")
MONEY = _rx(r"\$\s?\d[\d,]*")
IDENTIFIER = _rx(r"(invoice\s*#?\s*\d+|#\d{3,}|account\s*#?\s*[A-Z]?-?\d+|[\w.+-]+@[\w-]+\.[\w.]+|@[A-Za-z0-9_]{4,})")
# Case-sensitive on purpose: a company name is a capitalised token after "from/at/on behalf of".
COMPANY = re.compile(r"(?:\bfrom|\bat|on behalf of)\s+([A-Z][A-Za-z0-9&]+(?:\s+(?:Corp|Inc|LLC|Ltd|Co|Labs|Group|Technologies|Systems))?)")
NOT_COMPANY = {"Chrome", "Firefox", "Safari", "Climb", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December", "The", "Our", "Your", "My", "Q1", "Q2", "Q3", "Q4"}


def rules_only_extraction(text: str) -> Extraction:
    t = text
    security_hit = any(r.pattern.search(t) for r in ESCALATION_RULES if r.reason in (EscalationReason.security_incident, EscalationReason.data_exposure))
    legal_hit = any(r.pattern.search(t) for r in ESCALATION_RULES if r.reason in (EscalationReason.legal_threat, EscalationReason.compliance_request))
    spam_score = len(SPAM_SIGNALS.findall(t))
    signals: list[str] = []

    if spam_score >= 2 and not security_hit:
        category, conf = Category.spam, 0.85
    elif security_hit:
        category, conf = Category.security, 0.8
    elif legal_hit:
        category, conf = Category.legal_contract, 0.7
    elif BUG.search(t) or BILLING.search(t):
        nb, nbi = len(BUG.findall(t)), len(BILLING.findall(t))
        category = Category.billing if nbi > nb else Category.bug
        conf = 0.6 if abs(nb - nbi) > 1 else 0.5
    elif ONBOARDING.search(t):
        category, conf = Category.onboarding, 0.6
    elif FEATURE.search(t):
        category, conf = Category.feature_request, 0.5
    else:
        category, conf = Category.other, 0.3

    urgency = Urgency.medium
    if category == Category.spam:
        urgency = Urgency.low
    elif WIDESPREAD_MONEY.search(t):
        urgency = Urgency.critical
        signals.append("multiple customers + duplicate charges")
    elif OUTAGE.search(t) and category == Category.bug:
        urgency = Urgency.critical
        signals.append(OUTAGE.search(t).group(0))
    elif LOW_PRIORITY.search(t):
        urgency = Urgency.low
        signals.append(LOW_PRIORITY.search(t).group(0))
    elif DEADLINE.search(t):
        urgency = Urgency.high
        signals.append(DEADLINE.search(t).group(0))
    if MONEY.search(t) and urgency == Urgency.medium:
        signals.append(MONEY.search(t).group(0))

    m = COMPANY.search(t)
    company = m.group(1) if m and m.group(1).split()[0] not in NOT_COMPANY else None
    customer = Customer(
        name=company,
        identifiers=[x if isinstance(x, str) else x[0] for x in IDENTIFIER.findall(t)],
    )
    return Extraction(
        customer=customer,
        category=category,
        category_confidence=conf,
        urgency=urgency,
        urgency_signals=signals,
        escalate=False,  # rules layer below decides
        escalation_reasons=[],
        summary=t.strip().split("\n")[0][:140],
        rationale=f"Rules-only mode (no model): category '{category.value}' by keyword match, urgency '{urgency.value}' from cue words. Escalation determined by guardrail regexes.",
    )
