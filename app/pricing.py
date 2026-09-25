"""What a decision cost, in one place.

Three things were quoting prices independently — the spend gate, the bake-off, and nothing at all
in the product. A number a reader cannot trace is a number that goes stale silently, so the table
lives here and everything imports it.

Rates are USD per 1M tokens, list price as of 2026-09. **Verify before quoting one to a client.**
Cached input is an order of magnitude cheaper than fresh input, which is why the system prompt is
a stable prefix: about 90% of input tokens on a warm run are cache reads.
"""
from __future__ import annotations

PRICES: dict[str, dict[str, float]] = {
    "gpt-5":      {"in": 1.25, "cached_in": 0.125, "out": 10.00},
    "gpt-5-mini": {"in": 0.25, "cached_in": 0.025, "out": 2.00},
    "gpt-5-nano": {"in": 0.05, "cached_in": 0.005, "out": 0.40},
}
DEFAULT = "gpt-5"


def price_for(model: str | None) -> dict[str, float]:
    """Longest-prefix match, so a dated id like gpt-5-mini-2025-08-07 prices as gpt-5-mini."""
    name = model or DEFAULT
    for key in sorted(PRICES, key=len, reverse=True):
        if name.startswith(key):
            return PRICES[key]
    return PRICES[DEFAULT]


def cost_usd(usage: dict, model: str | None) -> float | None:
    """Cost of one decision from its measured usage. None when no model ran."""
    if not usage or not usage.get("input_tokens"):
        return None
    p = price_for(model)
    cached = usage.get("cache_read_input_tokens", 0) or 0
    fresh = max(usage.get("input_tokens", 0) - cached, 0)
    out = usage.get("output_tokens", 0) or 0
    return (fresh * p["in"] + cached * p["cached_in"] + out * p["out"]) / 1_000_000
