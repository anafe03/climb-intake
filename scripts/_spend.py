"""Estimate what a bulk run will cost, and make the operator agree to it.

Every script that fans out over the gold set imports this. It exists because the expensive mistake
in this project was never one call — it was running a 33-ticket eval five times without thinking.
"""
from __future__ import annotations

import os
import sys

# USD per 1M tokens. Verify against current list price before quoting.
PRICES = {
    "gpt-5":      {"in": 1.25, "cached": 0.125, "out": 10.00},
    "gpt-5-mini": {"in": 0.25, "cached": 0.025, "out": 2.00},
    "gpt-5-nano": {"in": 0.05, "cached": 0.005, "out": 0.40},
}
# Measured per ticket: ~2.5k input (90% cached after the first call), and output that varies
# ~4x with reasoning effort. These are the numbers the estimate is built from.
TOKENS = {"in": 2500, "cached_frac": 0.9, "out": {"minimal": 450, "low": 900, "medium": 1600, "high": 2600}}


def price_for(model: str) -> dict:
    for k in ("gpt-5-nano", "gpt-5-mini", "gpt-5"):
        if model.startswith(k):
            return PRICES[k]
    return PRICES["gpt-5"]


def estimate(calls: int, model: str | None = None, effort: str | None = None) -> float:
    model = model or os.environ.get("OPENAI_MODEL", "gpt-5")
    effort = effort or os.environ.get("OPENAI_REASONING_EFFORT", "low")
    p = price_for(model)
    cached = TOKENS["in"] * TOKENS["cached_frac"]
    fresh = TOKENS["in"] - cached
    out = TOKENS["out"].get(effort, TOKENS["out"]["low"])
    return calls * (fresh * p["in"] + cached * p["cached"] + out * p["out"]) / 1_000_000


def confirm(calls: int, what: str, model: str | None = None) -> None:
    """Print the estimate; stop above the budget unless the operator opts in.

    SPEND_BUDGET_USD sets the threshold (default 0.25). SPEND_OK=1 skips the prompt for CI.
    """
    model = model or os.environ.get("OPENAI_MODEL", "gpt-5")
    effort = os.environ.get("OPENAI_REASONING_EFFORT", "low")
    usd = estimate(calls, model, effort)
    print(f"  {what}: {calls} calls on {model} at effort={effort} ≈ ${usd:.2f}", file=sys.stderr)
    budget = float(os.environ.get("SPEND_BUDGET_USD", "0.25"))
    if usd <= budget or os.environ.get("SPEND_OK") == "1":
        return
    print(f"  over the ${budget:.2f} budget. Re-run with SPEND_OK=1, or lower it:", file=sys.stderr)
    print(f"    OPENAI_MODEL=gpt-5-mini  (about {estimate(calls,'gpt-5-mini',effort)/usd:.0%} of the cost)", file=sys.stderr)
    print(f"    OPENAI_REASONING_EFFORT=minimal  (about {estimate(calls,model,'minimal')/usd:.0%})", file=sys.stderr)
    sys.exit(2)
