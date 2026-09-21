"""Shared gold-set loader and scorer used by tests and scripts/eval.py."""
from __future__ import annotations

import json
from pathlib import Path

from app.models import Decision, URGENCY_RANK, Urgency

GOLD = Path(__file__).resolve().parent.parent / "data" / "gold.jsonl"


def load_gold() -> list[dict]:
    return [json.loads(l) for l in GOLD.read_text().splitlines() if l.strip()]


def score_one(row: dict, d: Decision) -> dict:
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
    }
