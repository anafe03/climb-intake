"""Which model does this job actually need?

    python scripts/model_bakeoff.py                          # 10 Climb tickets x 3 models
    python scripts/model_bakeoff.py --models gpt-5 gpt-5-mini --ids climb-03 climb-10

Runs the same gold tickets through several models and reports quality, latency and measured token
cost side by side. Writes docs/MODEL-BAKEOFF.md.

The question it answers is the one a client asks second, right after "does it work": what does it
cost to run, and can something cheaper do it. Escalation recall is the metric that decides it — a
cheaper model is only interesting if it never misses one.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models import TicketIn  # noqa: E402
from app.pipeline import process  # noqa: E402
from tests.gold import load_gold, score_one, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# USD per 1M tokens. Verify against platform.openai.com/pricing before quoting these — they are what
# this report assumes, not a claim about current list price. Token counts below are measured.
PRICES = {
    "gpt-5":       {"in": 1.25, "cached_in": 0.125, "out": 10.00},
    "gpt-5-mini":  {"in": 0.25, "cached_in": 0.025, "out": 2.00},
    "gpt-5-nano":  {"in": 0.05, "cached_in": 0.005, "out": 0.40},
}
CLIMB_10 = [f"climb-{i:02d}" for i in range(1, 11)]
# Default to the WHOLE gold set. Running only the 10 provided samples measures missed escalations
# and nothing else: none of them is designed to tempt a false one. The traps live in the edge rows,
# and leaving them out is how a bake-off recommends a model that over-escalates. See D52.
ALL_GOLD = None  # resolved at runtime


def run(model: str, rows: list[dict], workers: int) -> dict:
    os.environ["OPENAI_MODEL"] = model
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        ds = list(ex.map(lambda r: process(TicketIn(text=r["text"], external_id=r["id"]), persist=False), rows))
    wall = time.perf_counter() - t0
    fails = [d for d in ds if d.mode != "llm"]
    s = summarize([score_one(r, d) for r, d in zip(rows, ds)])
    lat = sorted(d.latency_ms for d in ds)
    tin = sum(d.usage.get("input_tokens", 0) for d in ds)
    tcached = sum(d.usage.get("cache_read_input_tokens", 0) for d in ds)
    tout = sum(d.usage.get("output_tokens", 0) for d in ds)
    p = PRICES.get(model)
    cost = None
    if p and ds:
        fresh = max(tin - tcached, 0)
        cost = (fresh * p["in"] + tcached * p["cached_in"] + tout * p["out"]) / 1_000_000 / len(ds)
    return {"model": ds[0].model if ds and ds[0].model else model, "summary": s, "fails": len(fails),
            "p50": lat[len(lat) // 2], "p95": lat[int(len(lat) * .95) - 1], "wall": wall,
            "tin": tin / len(ds), "tcached": tcached / len(ds), "tout": tout / len(ds),
            "cost_per_ticket": cost, "n": len(ds)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["gpt-5", "gpt-5-mini", "gpt-5-nano"])
    ap.add_argument("--ids", nargs="*", default=None,
                    help="default: every gold ticket. Pass --climb10 for the provided samples only.")
    ap.add_argument("--climb10", action="store_true", help="only the 10 provided samples (see D52)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    gold = {r["id"]: r for r in load_gold()}
    ids = a.ids or (CLIMB_10 if a.climb10 else list(gold))
    rows = [gold[i] for i in ids if i in gold]
    a.ids = ids
    print(f"{len(rows)} tickets x {len(a.models)} models = {len(rows)*len(a.models)} calls\n")

    results = []
    for m in a.models:
        print(f"  running {m} …", flush=True)
        try:
            results.append(run(m, rows, a.workers))
        except Exception as e:  # noqa: BLE001
            print(f"    skipped: {type(e).__name__}: {str(e)[:120]}")

    lines = [
        "# Model bake-off: what does this job actually need?",
        "",
        f"`scripts/model_bakeoff.py` · {len(rows)} tickets ({', '.join(a.ids[:3])}…) · "
        f"{time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "Same prompt, same schema, same guardrails — only the model changes. **Escalation recall is the",
        "metric that decides this.** A cheaper model is only interesting if it never misses one; every",
        "other number is a trade you can discuss.",
        "",
        "| model | escalation recall | missed | **false escalations** | category | urgency exact | p50 | cost / ticket |",
        "|---|---|---|---|---|---|---|---|",
    ]
    top = results[0]["cost_per_ticket"] if results and results[0]["cost_per_ticket"] else None
    for r in results:
        s = r["summary"]
        cost = f"${r['cost_per_ticket']*100:.3f}¢" if r["cost_per_ticket"] else "—"
        rel = f"{r['cost_per_ticket']/top:.2f}x" if (top and r["cost_per_ticket"]) else "—"
        lines.append(
            f"| `{r['model']}` | **{s['escalation_recall']:.0%}** | {s['missed_escalations'] or 'none'} | "
            f"**{s['false_escalations'] or 'none'}** | {s['category_accuracy']:.0%} | "
            f"{s['urgency_exact']:.0%} | {r['p50']/1000:.1f} s | {cost} |")

    lines += ["", "## Tokens measured per ticket", "",
              "| model | input | of which cached | output |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| `{r['model']}` | {r['tin']:.0f} | {r['tcached']:.0f} | {r['tout']:.0f} |")

    lines += [
        "",
        "Prices are the per-million rates in `scripts/model_bakeoff.py`; **verify them against current",
        "list price before quoting a figure.** The token counts are measured from `response.usage`.",
        "",
        "## Reading it",
        "",
        "At this volume the absolute cost is noise — the interesting number is the ratio, and what you",
        "give up for it. The honest way to use this table is: find the cheapest model that still shows",
        "100% escalation recall and no missed escalations, run that in production, and keep the",
        "expensive one for the human-review queue where the classifier already said it was unsure.",
        "",
        "Two caveats worth saying out loud: this is 10 tickets, so a single disagreement moves a column",
        "by 10 points, and the guardrail layer sits underneath every row — a model that misses an",
        "escalation here would still have been caught by the keyword rules before the ticket shipped.",
    ]
    out = ROOT / "docs" / "MODEL-BAKEOFF.md"
    out.write_text("\n".join(lines) + "\n")
    (ROOT / "data" / "eval-results").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "eval-results" / "bakeoff.json").write_text(json.dumps(results, indent=2, default=str))
    print("\n".join(lines))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
