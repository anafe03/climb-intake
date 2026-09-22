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
        # No urgency lift. The escalation flag already routes this to a human; forcing urgency up
        # only overwrites a judgment the model makes better. Observed live: for a CEO thank-you note
        # and a roadmap-call request, the model correctly said "low" and this floor pushed both to
        # "medium" for no operational gain. Security and legal keep their floors because those are
        # time-sensitive by nature; an executive mention is about visibility, not speed.
        Urgency.low,
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

# Off-platform contact handles, solicitation boilerplate, and get-rich noise. Two or more hits
# classify as spam. Single hits are deliberately not enough: a real customer can say "lol".
SPAM_SIGNALS = _rx(
    r"\b(free credits?|discord|telegram|whatsapp|crypto|bitcoin|mining|lol|lmao|my (uncle|cousin)|"
    r"seo|backlinks?|5-star|guaranteed|click here|unsubscribe|casino|giveaway|hmu|dm me|"
    r"lead lists?|b2b leads?|contact lists?|cold (email|outreach)|wanna partner|"
    r"first \d+ free|reply [A-Z]{3,} to)\b"
)
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
# Contextual cues for the keyword layer's own (weak) guess at who is writing.
EMAIL_DOMAIN = _rx(r"[\w.+-]+@([\w-]+\.[\w.]+)")
FREE_MAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "proton.me"}
ENTERPRISE_CUE = _rx(r"\b(enterprise|our (team|analysts|staff|engineers|org)|[0-9]{2,} (users|seats|analysts|people)|workspace|unity catalog|databricks|sql warehouse|basecamp|SOW|MSA)\b")
SCALE_CUE = _rx(r"\b(all )?(\d{2,}) (of our )?(users|analysts|staff|employees|people|seats)\b")
PLAN_CUE = _rx(r"\b(team|pro|business|enterprise|starter) plan\b")

COMPANY = re.compile(r"(?:\bfrom|\bat|on behalf of)\s+([A-Z][A-Za-z0-9&]+(?:\s+(?:Corp|Inc|LLC|Ltd|Co|Labs|Group|Technologies|Systems|Logistics|Health|Healthcare|Partners|Solutions|Media|Capital|Industries|Analytics|Digital))?)")
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
    ids = [x if isinstance(x, str) else x[0] for x in IDENTIFIER.findall(t)]

    # Scored guess at the sender, same contract as the model path but from cues only.
    guess, conf, basis = None, 0.0, []
    if company:
        guess, conf, basis = company, 1.0, ["company named in the text"]
    else:
        dom = EMAIL_DOMAIN.search(t)
        if dom and dom.group(1).lower() not in FREE_MAIL:
            guess, conf = f"someone at {dom.group(1)}", 0.8
            basis.append(f"work email domain {dom.group(1)}")
        elif dom:
            guess, conf = "an individual user", 0.3
            basis.append("personal email domain")
        if ENTERPRISE_CUE.search(t):
            basis.append(f"enterprise product language: “{ENTERPRISE_CUE.search(t).group(0)}”")
            if conf < 0.5:
                guess, conf = (guess or "an enterprise customer"), max(conf, 0.45)
        sc = SCALE_CUE.search(t)
        if sc:
            basis.append(f"stated scale: “{sc.group(0)}”")
            guess, conf = (guess or "a customer with a sizeable team"), max(conf, 0.5)
        pl = PLAN_CUE.search(t)
        if pl:
            basis.append(f"plan referenced: “{pl.group(0)}”")
            guess, conf = (guess or f"a customer on the {pl.group(0)}"), max(conf, 0.45)
        if not guess and ids:
            guess, conf = "an existing customer (account reference present)", 0.3
            basis.append(f"identifier in the text: {ids[0]}")

    customer = Customer(name=company, identifiers=ids, best_guess=guess,
                        confidence=round(conf, 2), basis=basis)
    cust_reason = (f"The text names “{company}” directly." if company
                   else (f"No company is named. Guessed from {basis[0]}." if basis
                         else "Nothing in the text identifies the sender — no name, domain, "
                              "account reference, or scale cue."))
    return Extraction(
        customer=customer,
        category=category,
        category_confidence=conf,
        urgency=urgency,
        urgency_signals=signals,
        escalate=False,  # the guardrail layer below decides
        escalation_reasons=[],
        summary=t.strip().split("\n")[0][:140],
        customer_reason=cust_reason,
        category_reason=f"Keyword match put this in '{category.value}'. This is the fallback classifier, "
                        f"which counts cue words rather than reading the request, so it cannot weigh a near alternative.",
        urgency_reason=(f"Cue words set '{urgency.value}': {', '.join(signals)}." if signals
                        else f"No urgency cue words matched, so this defaults to '{urgency.value}'."),
        escalation_reason_text="Escalation is decided by the guardrail regexes that run after this step, "
                               "not by the keyword classifier.",
        rationale=f"Keyword-rules mode (no model available): category '{category.value}' by cue words, "
                  f"urgency '{urgency.value}'. Escalation is decided by the guardrail layer.",
    )
