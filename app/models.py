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
    """Who sent the ticket. Never invented: if the text has no company name, name is null."""
    name: Optional[str] = Field(default=None, description="Company/account name if stated verbatim in the ticket, else null.")
    contact_name: Optional[str] = Field(default=None, description="Person's name if stated, else null.")
    identifiers: list[str] = Field(default_factory=list, description="Verbatim identifiers such as invoice numbers, account ids, emails, handles.")


class Extraction(BaseModel):
    """The structured fields the assignment asks for, plus the evidence behind them."""
    customer: Customer
    category: Category
    category_confidence: float = Field(description="0.0-1.0")
    urgency: Urgency
    urgency_signals: list[str] = Field(description="Short verbatim cues that drove the urgency call (deadlines, money, scope, recurrence).")
    escalate: bool
    escalation_reasons: list[EscalationReason]
    summary: str = Field(description="One sentence, what the customer wants.")
    rationale: str = Field(description="2-4 sentences explaining category, urgency, and the escalation decision.")


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
