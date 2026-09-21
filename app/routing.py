"""Routing table: category + urgency -> simulated downstream queue."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from .models import Category, Urgency

_TABLE = Path(__file__).with_name("routing.yaml")


@lru_cache(maxsize=1)
def load_table() -> dict:
    with _TABLE.open() as f:
        return yaml.safe_load(f)


def route(category: Category, urgency: Urgency, escalate: bool, confidence: float = 1.0) -> tuple[str, str | None]:
    table = load_table()
    low = table.get("low_confidence", {})
    if not escalate and confidence < low.get("threshold", 0.0):
        return low["queue"], None
    entry = table["queues"].get(category.value) or table["queues"]["other"]
    queue = entry.get(urgency.value) or entry["default"]
    return queue, (table["escalation_queue"] if escalate else None)


def all_queues() -> list[str]:
    table = load_table()
    names = {q for entry in table["queues"].values() for q in entry.values()}
    names.add(table["escalation_queue"])
    if table.get("low_confidence"):
        names.add(table["low_confidence"]["queue"])
    return sorted(names)
