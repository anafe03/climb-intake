"""Orchestration: mode selection -> extraction -> rule overrides -> routing -> audit."""
from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone

import anthropic
import openai

from . import audit, cascade, llm, pricing, routing, rules
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


def _merge_usage(first: dict, second: dict) -> dict:
    """Both reads were paid for, so both are reported. Hiding the draft's tokens would make the
    cascade look cheaper than it is, which is the one thing this measurement must not do."""
    out = dict(second)
    for k in ("input_tokens", "output_tokens", "cache_read_input_tokens"):
        out[k] = (first.get(k, 0) or 0) + (second.get(k, 0) or 0)
    return out


def _cascade_classify(text: str) -> tuple[Extraction, dict, dict]:
    """Pick a reader for this ticket. Two strategies, both measured in docs/CASCADE.md."""
    if cascade.triage_mode() == "rules":
        # Triage with the keyword layer, which costs nothing and has already read the text. One
        # model call, chosen before any money is spent.
        expensive, why = cascade.triage_by_rules(text)
        model = None if expensive else cascade.draft_model()
        x, meta = llm.classify(text, model=model)
        return x, meta, {"triage": "rules", "expensive": expensive, "why": why,
                         "reader": meta.get("model")}

    draft, dmeta = llm.classify(text, model=cascade.draft_model())
    reread, why = cascade.needs_second_read(draft)
    draft_cost = pricing.cost_usd(dmeta, dmeta.get("model"))
    note = {"triage": "draft", "draft_model": dmeta.get("model"), "reread": reread, "why": why,
            "draft_cost_usd": round(draft_cost, 6) if draft_cost else None}
    if not reread:
        return draft, dmeta, note
    final, fmeta = llm.classify(text)
    # Report the merged spend under the model that produced the shipped answer.
    merged = _merge_usage(dmeta, fmeta)
    note["draft_said"] = {"category": draft.category.value, "urgency": draft.urgency.value,
                          "escalate": draft.escalate}
    note["changed"] = (draft.category != final.category or draft.urgency != final.urgency
                       or draft.escalate != final.escalate)
    return final, merged, note


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
            if cascade.enabled():
                llm_extraction, meta, cascade_note = _cascade_classify(ticket.text)
            else:
                llm_extraction, meta = llm.classify(ticket.text)
                cascade_note = None
            model = meta.pop("model")
            usage = meta
            if cascade_note:
                usage["cascade"] = cascade_note
            # Price the decision where the tokens are known, so the audit record answers "what did
            # this cost" without anyone having to re-derive it from a rate card six months later.
            cost = pricing.cost_usd(usage, model)
            if cost is not None:
                usage["cost_usd"] = round(cost, 6)
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
