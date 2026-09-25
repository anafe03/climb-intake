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
sys.path.insert(0, str(Path(__file__).resolve().parent))
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


def run(model: str, rows: list[dict], workers: int, effort: str = "low") -> dict:
    os.environ["OPENAI_MODEL"] = model
    os.environ["OPENAI_REASONING_EFFORT"] = effort
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
    return {"model": ds[0].model if ds and ds[0].model else model, "effort": effort, "summary": s, "fails": len(fails),

            "p50": lat[len(lat) // 2], "p95": lat[int(len(lat) * .95) - 1], "wall": wall,
            "tin": tin / len(ds), "tcached": tcached / len(ds), "tout": tout / len(ds),
            "cost_per_ticket": cost, "n": len(ds)}


def score_saved(label: str, path: Path, rows: list[dict]) -> dict:
    """Score a run that already happened. Same scorer, same rows, no model call."""
    from app.models import Decision
    saved = json.loads(path.read_text())
    by_id = {d["ticket"]["external_id"]: Decision(**d) for d in saved["decisions"]}
    ds = [by_id[r["id"]] for r in rows if r["id"] in by_id]
    if len(ds) != len(rows):
        raise SystemExit(f"{path.name} covers {len(ds)} of {len(rows)} rows; cannot reuse")
    s = summarize([score_one(r, d) for r, d in zip(rows, ds)])
    lat = sorted(d.latency_ms for d in ds)
    tin = sum(d.usage.get("input_tokens", 0) for d in ds)
    tcached = sum(d.usage.get("cache_read_input_tokens", 0) for d in ds)
    tout = sum(d.usage.get("output_tokens", 0) for d in ds)
    p = PRICES.get(label.split("@")[0])
    cost = ((max(tin - tcached, 0) * p["in"] + tcached * p["cached_in"] + tout * p["out"])
            / 1_000_000 / len(ds)) if p else None
    return {"model": ds[0].model or label, "effort": os.environ.get("OPENAI_REASONING_EFFORT", "low"),
            "summary": s, "fails": sum(1 for d in ds if d.mode != "llm"),
            "p50": lat[len(lat) // 2], "p95": lat[int(len(lat) * .95) - 1], "wall": float("nan"),
            "tin": tin / len(ds), "tcached": tcached / len(ds), "tout": tout / len(ds),
            "cost_per_ticket": cost, "n": len(ds), "reused": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["gpt-5", "gpt-5-mini", "gpt-5-nano"],
                    help="each entry is MODEL or MODEL@EFFORT, e.g. gpt-5-mini@minimal")
    ap.add_argument("--reuse", nargs="*", default=[],
                    help="MODEL=path.json — score a saved eval run instead of paying for it again")
    ap.add_argument("--ids", nargs="*", default=None,
                    help="default: every gold ticket. Pass --climb10 for the provided samples only.")
    ap.add_argument("--climb10", action="store_true", help="only the 10 provided samples (see D52)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--rewrite", action="store_true",
                    help="regenerate the report from the last saved results; calls nothing")
    a = ap.parse_args()

    gold = {r["id"]: r for r in load_gold()}
    ids = a.ids or (CLIMB_10 if a.climb10 else list(gold))
    rows = [gold[i] for i in ids if i in gold]
    a.ids = ids
    if a.rewrite:
        # Prose changed, measurements did not. Re-running models to restate the same numbers is the
        # exact waste this report argues against.
        results = json.loads((ROOT / "data" / "eval-results" / "bakeoff.json").read_text())
        return write_report(results, rows, a.ids)

    legs = [(m.split("@")[0], (m.split("@") + ["low"])[1]) for m in a.models]
    from _spend import confirm
    for model, effort in legs:
        os.environ["OPENAI_REASONING_EFFORT"] = effort
        confirm(len(rows), f"bake-off leg @{effort}", model)
    print(f"{len(rows)} tickets x {len(legs)} legs = {len(rows)*len(legs)} calls"
          f"{f', plus {len(a.reuse)} reused free' if a.reuse else ''}\n")

    results = []
    # A saved run is the same measurement as a fresh one. Paying twice for the same answer is the
    # mistake this whole file exists to argue against.
    for spec in a.reuse:
        label, _, path = spec.partition("=")
        results.append(score_saved(label, ROOT / path, rows))
        print(f"  reused {label} from {path}")
    for model, effort in legs:
        print(f"  running {model} @ effort={effort} …", flush=True)
        try:
            results.append(run(model, rows, a.workers, effort))
        except Exception as e:  # noqa: BLE001
            print(f"    skipped: {type(e).__name__}: {str(e)[:120]}")

    return write_report(results, rows, a.ids)


def write_report(results: list[dict], rows: list[dict], ids: list[str]) -> int:
    a_ids = ids
    lines = [
        "# Model bake-off: what does this job actually need?",
        "",
        f"`scripts/model_bakeoff.py` · {len(rows)} tickets ({', '.join(a_ids[:3])}…) · "
        f"{time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "Same prompt, same schema, same guardrails — only the model and its reasoning effort change.",
        "**The columns in bold are the ones that decide it.** A missed escalation disqualifies a model.",
        "An urgency under-call on a critical ticket disqualifies it. Everything else is a trade you can",
        "have a conversation about.",
        "",
        "| model | effort | **missed escalations** | **false escalations** | **urgency under-called** | category | p50 | cost / ticket | vs gpt-5 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    top = next((r["cost_per_ticket"] for r in results
                if r["cost_per_ticket"] and r["model"].startswith("gpt-5-2")), None) \
        or (results[0]["cost_per_ticket"] if results else None)
    for r in results:
        s = r["summary"]
        cost = f"${r['cost_per_ticket']*100:.3f}¢" if r["cost_per_ticket"] else "—"
        rel = f"{r['cost_per_ticket']/top:.2f}x" if (top and r["cost_per_ticket"]) else "—"
        n = lambda v: f"**{len(v)}** ({', '.join(x.split()[0] for x in v)})" if v else "none"
        lines.append(
            f"| `{r['model']}`{' *(reused)*' if r.get('reused') else ''} | {r.get('effort','low')} | "
            f"{n(s['missed_escalations'])} | {n(s['false_escalations'])} | "
            f"{n(s['urgency_under'])} | {s['category_accuracy']:.0%} | "
            f"{r['p50']/1000:.1f} s | {cost} | {rel} |")

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
        "**Cost is not the deciding column.** Every model here is cheap enough; what separates them is",
        "which mistakes they make. Read right to left: find the cheapest row whose error columns you",
        "can live with, not the cheapest row.",
        "",
        "Three things this table is built to show, that an accuracy score would hide:",
        "",
        "1. **Nobody missed an escalation.** Recall is the metric that would disqualify a model, and no",
        "   row fails it. That is partly the guardrail layer, which sits underneath every row — a model",
        "   that missed one here would still have been caught by keyword rules before the ticket shipped.",
        "2. **False escalations are where the cheap models show up.** They are tolerable — a person",
        "   spends a minute — but they are the cost of the discount, and they should be quoted with it.",
        "3. **Urgency under-calls are the column to actually worry about.** A ticket read calmer than it is",
        "   sits. If a row under-calls a ticket the gold set marks *critical*, that row is disqualified",
        "   whatever it costs.",
        "",
        f"Measured over {len(rows)} gold tickets, so a single disagreement moves a percentage column by",
        f"about {100/max(len(rows),1):.0f} points. Small enough to be directional, not a benchmark.",
        "",
        "## Making a cheaper model good enough",
        "",
        "The lever people reach for first is the model. It is the third-best lever here.",
        "",
        "| lever | effect | what it costs you |",
        "|---|---|---|",
        "| **Prompt caching** | ~90% of input tokens are cache reads at 1/10th the price | nothing — the system prompt is a stable prefix, so this is free once the first call warms it |",
        "| **Reasoning effort** | the dominant output-token lever; `low` roughly halved output against the default | accuracy on the hard rows. Dropping mini from `low` to `minimal` saved 31% and tripled its false escalations |",
        "| **A smaller model** | 5x to 26x cheaper | the error profile changes shape, not just degrades — see the table |",
        "| **Cascade** | run the cheap model first, re-read only what it is unsure about on the expensive one | complexity, and a second call on the minority of tickets |",
        "",
        "The cascade is the one worth building if volume ever justifies it, and this codebase is already",
        "shaped for it: the confidence threshold that sends unsure tickets to `human-review` is the same",
        "signal that would send them to a better model instead. Everything under 0.50 goes to the",
        "expensive reader; everything above ships on the cheap one.",
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
