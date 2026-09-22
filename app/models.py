"""Pydantic models shared by the classifier, rules layer, API, and audit log."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    security = "security"
    legal_contract = "legal_contract"
    onboarding = "onboarding"
    feature_request = "feature_request"
    spam = "spam"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


URGENCY_RANK = {Urgency.low: 0, Urgency.medium: 1, Urgency.high: 2, Urgency.critical: 3}


def max_urgency(a: Urgency, b: Urgency) -> Urgency:
    return a if URGENCY_RANK[a] >= URGENCY_RANK[b] else b


class EscalationReason(str, Enum):
    security_incident = "security_incident"
    data_exposure = "data_exposure"
    legal_threat = "legal_threat"
    compliance_request = "compliance_request"
    executive_mention = "executive_mention"


class Customer(BaseModel):
    """Who sent the ticket.

    Two separate things, deliberately kept apart:
      * `name` / `contact_name` — stated verbatim in the text. Facts.
      * `best_guess` + `confidence` + `basis` — an inference from context when nothing is stated.
        Downstream can gate on the confidence; a reader can audit the reasoning.
    """
    name: Optional[str] = Field(default=None, description="Company or account name ONLY if stated verbatim in the ticket, else null.")
    contact_name: Optional[str] = Field(default=None, description="Person's name ONLY if stated verbatim, else null.")
    identifiers: list[str] = Field(default_factory=list, description="Verbatim identifiers: invoice numbers, account ids, emails, handles, ticket refs.")
    best_guess: Optional[str] = Field(default=None, description="Best inference about who this is, when `name` is null. E.g. 'enterprise Databricks customer, likely healthcare' or 'existing paying customer on the Team plan'. Null only if the text gives nothing at all.")
    confidence: float = Field(default=0.0, description="0.0-1.0 confidence in `best_guess`. Use `name` verbatim -> 1.0. A domain in an email -> ~0.8. Product/plan references only -> ~0.4. Nothing -> 0.0.")
    basis: list[str] = Field(default_factory=list, description="The specific cues the guess rests on, quoted or named. Empty when nothing was inferable.")


class Extraction(BaseModel):
    """The structured fields the assignment asks for, plus the evidence behind them."""
    customer: Customer
    customer_reason: str = Field(description="One or two sentences: how you identified the sender, or why the text does not support a firmer answer.")
    category: Category
    category_confidence: float = Field(description="0.0-1.0")
    category_reason: str = Field(description="One or two sentences: what puts it in this category rather than the nearest alternative. Name the alternative you rejected.")
    urgency: Urgency
    urgency_signals: list[str] = Field(description="Short verbatim cues that drove the urgency call (deadlines, money, scope, recurrence).")
    urgency_reason: str = Field(description="One or two sentences: which criteria set this level. Urgency is never stated, so say what you inferred it from.")
    escalate: bool
    escalation_reasons: list[EscalationReason]
    escalation_reason_text: str = Field(description="One or two sentences: why a human is or is not needed. If not, name the escalation topics you checked and ruled out.")
    summary: str = Field(description="One sentence, what the customer wants.")
    rationale: str = Field(description="2-4 sentences tying the whole decision together.")


class RuleHit(BaseModel):
    rule: str
    reason: Optional[EscalationReason] = None
    matched: str
    effect: str


class TicketIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    source: str = "api"
    external_id: Optional[str] = None


class Decision(BaseModel):
    id: str
    created_at: str
    ticket: TicketIn
    mode: str  # llm | rules | llm_fallback_rules
    model: Optional[str] = None
    extraction: Extraction  # final, after rule overrides
    llm_extraction: Optional[Extraction] = None  # raw model output before overrides (audit)
    rule_hits: list[RuleHit] = Field(default_factory=list)
    overrides: list[str] = Field(default_factory=list)
    queue: str
    escalation_queue: Optional[str] = None
    latency_ms: int
    usage: dict = Field(default_factory=dict)
    error: Optional[str] = None
