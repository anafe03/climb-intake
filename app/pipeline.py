"""Orchestration: mode selection -> extraction -> rule overrides -> routing -> audit."""
from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone

import anthropic
import openai

from . import audit, llm, routing, rules
from .models import Decision, Extraction, TicketIn

log = logging.getLogger("climb.pipeline")

# Last model-call outcome, so /health can distinguish "a key is configured" from "the model works".
# Costs nothing: it is a side effect of traffic, not a probe.
LAST_MODEL_CALL: dict = {"status": "unknown", "at": None, "error": None}


def has_credentials() -> bool:
    return llm.provider() is not None


def effective_mode() -> str:
    mode = os.environ.get("CLASSIFIER_MODE", "auto").lower()
    if mode == "auto":
        return "llm" if has_credentials() else "rules"
    return mode


def process(ticket: TicketIn, persist: bool = True) -> Decision:
    # Fast path for sequential retries: skip the model call if we already decided this ticket.
    # Correctness does not rest here — a unique index in audit.record() arbitrates concurrent
    # resubmits, since this check and the later insert are not atomic together.
    if persist and ticket.external_id:
        existing = audit.find_by_external(ticket.source, ticket.external_id)
        if existing:
            return existing
    started = time.perf_counter()
    mode = effective_mode()
    model = None
    usage: dict = {}
    error = None
    llm_extraction: Extraction | None = None

    if mode == "llm":
        try:
            llm_extraction, meta = llm.classify(ticket.text)
            model = meta.pop("model")
            usage = meta
            base = llm_extraction
            LAST_MODEL_CALL.update(status="ok", at=datetime.now(timezone.utc).isoformat(timespec="seconds"), error=None)
        except (anthropic.APIError, openai.APIError, llm.RefusedError, ValueError) as e:
            # Degrade rather than drop: a routing service must always produce a decision.
            error = f"{type(e).__name__}: {e}"
            LAST_MODEL_CALL.update(status="failing", at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                   error=error[:300])
            log.warning("llm classification failed, falling back to rules: %s", error)
            mode = "llm_fallback_rules"
            base = rules.rules_only_extraction(ticket.text)
    else:
        base = rules.rules_only_extraction(ticket.text)

    final, hits, overrides = rules.apply_escalation_rules(ticket.text, base)
    queue, esc_queue = routing.route(final.category, final.urgency, final.escalate, final.category_confidence)

    decision = Decision(
        id=uuid.uuid4().hex[:12],
        created_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        ticket=ticket,
        mode=mode,
        model=model,
        extraction=final,
        llm_extraction=llm_extraction,
        rule_hits=hits,
        overrides=overrides,
        queue=queue,
        escalation_queue=esc_queue,
        latency_ms=int((time.perf_counter() - started) * 1000),
        usage=usage,
        error=error,
    )
    if persist:
        # record() returns the authoritative decision: this one, or the winner of a concurrent
        # resubmit of the same (source, external_id).
        decision = audit.record(decision)
    return decision
