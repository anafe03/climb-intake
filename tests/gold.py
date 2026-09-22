"""Shared gold-set loader and scorer used by tests and scripts/eval.py."""
from __future__ import annotations

import json
from pathlib import Path

from app.models import Decision, URGENCY_RANK, Urgency

GOLD = Path(__file__).resolve().parent.parent / "data" / "gold.jsonl"


def load_gold() -> list[dict]:
    return [json.loads(l) for l in GOLD.read_text().splitlines() if l.strip()]


def score_one(row: dict, d: Decision) -> dict:
    """Confidence is scored asymmetrically on purpose.

    The ceiling is a safety property and applies in every mode: the system must never claim more
    certainty about a sender than the text supports. The floor is a quality property and applies
    only to the model path; the keyword fallback cannot read "I'm a security researcher" and
    honestly reporting 0.00 there is correct behaviour, not a miss.
    """
    exp, amb = row["expected"], set(row.get("ambiguous", []))
    x = d.extraction
    urg_delta = abs(URGENCY_RANK[x.urgency] - URGENCY_RANK[Urgency(exp["urgency"])])
    return {
        "id": row["id"],
        "group": row["group"],
        "must_escalate": bool(exp["escalate"]),
        "escalated": x.escalate,
        "escalation_ok": (x.escalate == exp["escalate"]) or ("escalate" in amb) or (x.escalate and not exp["escalate"] and False),
        "missed_escalation": exp["escalate"] and not x.escalate,
        "false_escalation": (not exp["escalate"]) and x.escalate and "escalate" not in amb,
        "reasons_ok": all(r in [e.value for e in x.escalation_reasons] for r in exp.get("reasons", [])),
        "category_ok": (x.category.value == exp["category"]) or ("category" in amb),
        "urgency_exact": x.urgency.value == exp["urgency"],
        "urgency_ok": (x.urgency.value == exp["urgency"]) or ("urgency" in amb and urg_delta <= 1),
        "customer_ok": (exp.get("customer_name") is None and x.customer.name is None) or (exp.get("customer_name") and x.customer.name and exp["customer_name"].lower() in x.customer.name.lower()),
        # The scored inference (D26): only checked where gold states an expected band.
        "confidence_scored": "customer_confidence" in exp,
        "confidence_ceiling_ok": (
            "customer_confidence" not in exp
            or x.customer.confidence <= exp["customer_confidence"][1]
        ),
        "confidence_floor_ok": (
            "customer_confidence" not in exp
            or d.mode != "llm"
            or x.customer.confidence >= exp["customer_confidence"][0]
        ),
        "confidence_got": x.customer.confidence,
        "confidence_band": exp.get("customer_confidence"),
        "guess": x.customer.best_guess,
        "basis_given": bool(x.customer.basis) or x.customer.confidence == 0.0,
        "identifier_ok": (not exp.get("identifier_contains")) or any(exp["identifier_contains"] in i for i in x.customer.identifiers),
        "queue": d.queue,
        "got": {"category": x.category.value, "urgency": x.urgency.value, "escalate": x.escalate, "reasons": [r.value for r in x.escalation_reasons], "customer": x.customer.name},
        "expected": exp,
    }


def summarize(results: list[dict]) -> dict:
    n = len(results)
    must = [r for r in results if r["must_escalate"]]
    return {
        "n": n,
        "escalation_recall": (sum(1 for r in must if r["escalated"]) / len(must)) if must else 1.0,
        "missed_escalations": [r["id"] for r in results if r["missed_escalation"]],
        "false_escalations": [r["id"] for r in results if r["false_escalation"]],
        "reasons_accuracy": sum(r["reasons_ok"] for r in must) / len(must) if must else 1.0,
        "category_accuracy": sum(r["category_ok"] for r in results) / n,
        "urgency_exact": sum(r["urgency_exact"] for r in results) / n,
        "urgency_accuracy": sum(r["urgency_ok"] for r in results) / n,
        "customer_accuracy": sum(bool(r["customer_ok"]) for r in results) / n,
        "identifier_accuracy": sum(r["identifier_ok"] for r in results) / n,
        "overconfidence": [
            f"{r['id']} claimed {r['confidence_got']:.2f}, ceiling {r['confidence_band'][1]}"
            for r in results if r["confidence_scored"] and not r["confidence_ceiling_ok"]
        ],
        "confidence_calibration": (
            sum(r["confidence_floor_ok"] and r["confidence_ceiling_ok"] for r in results if r["confidence_scored"])
            / max(1, sum(r["confidence_scored"] for r in results))
        ),
        "confidence_misses": [
            f"{r['id']} got {r['confidence_got']:.2f}, expected {r['confidence_band']}"
            for r in results if r["confidence_scored"] and not (r["confidence_floor_ok"] and r["confidence_ceiling_ok"])
        ],
        "basis_always_given": all(r["basis_given"] for r in results),
    }
