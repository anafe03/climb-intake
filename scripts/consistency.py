"""Run each of the 10 Climb tickets several times and show how much every answer moves.

    python scripts/consistency.py --label baseline          # 10 tickets x 5 runs
    python scripts/consistency.py --label one-shot --runs 5

Nothing here is scored against a right answer; that is the eval's job. This answers "would it say the
same thing again?" for every field the service produces: category, urgency, escalation, where it was
routed, who sent it, and the two confidence scores. Results are saved to data/measured so they can be
shown, and written up in docs/CONSISTENCY.md.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.models import TicketIn  # noqa: E402
from app.pipeline import effective_mode, process  # noqa: E402
from tests.gold import load_gold  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [
    ("category", lambda d: d.extraction.category.value),
    ("urgency", lambda d: d.extraction.urgency.value),
    ("escalate", lambda d: "yes" if d.extraction.escalate else "no"),
    ("route", lambda d: d.queue + (f" + {d.escalation_queue}" if d.escalation_queue else "")),
    ("who (stated name)", lambda d: d.extraction.customer.name or "not stated"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--label", default="baseline")
    a = ap.parse_args()
    if effective_mode() != "llm":
        raise SystemExit("needs an API key: the question is whether the model repeats itself")

    tickets = [r for r in load_gold() if r["id"].startswith("climb-")]
    jobs = [(r, i) for r in tickets for i in range(a.runs)]
    from _spend import confirm
    confirm(len(jobs), f"consistency {a.label}")
    with ThreadPoolExecutor(max_workers=4) as ex:
        ds = list(ex.map(lambda j: process(TicketIn(text=j[0]["text"], source=f"consistency-{a.label}"),
                                           persist=False), jobs))

    by: dict[str, list] = {}
    for (r, _), d in zip(jobs, ds):
        by.setdefault(r["id"], []).append(d)

    results = []
    for r in tickets:
        runs = by[r["id"]]
        row = {"id": r["id"], "text": r["text"], "runs": len(runs),
               "failed": sum(1 for d in runs if d.mode != "llm"), "fields": {}}
        for name, get in FIELDS:
            vals = [get(d) for d in runs]
            top, n = Counter(vals).most_common(1)[0]
            row["fields"][name] = {"values": vals, "most_common": top, "same": n, "flipped": n < len(vals)}
        for name, get in [("category confidence", lambda d: d.extraction.category_confidence),
                          ("who confidence", lambda d: d.extraction.customer.confidence)]:
            vals = [round(get(d), 2) for d in runs]
            row["fields"][name] = {"values": vals, "min": min(vals), "max": max(vals),
                                   "spread": round(max(vals) - min(vals), 2),
                                   "sd": round(st.pstdev(vals), 3)}
        results.append(row)

    out = ROOT / "data" / "measured" / f"consistency-{a.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": a.label, "runs": a.runs, "tickets": results,
                               "when": time.strftime("%Y-%m-%d %H:%M")}, indent=2))

    flips = {name: [r["id"] for r in results if r["fields"][name]["flipped"]] for name, _ in FIELDS}
    spreads = {n: [r["fields"][n]["spread"] for r in results] for n in ("category confidence", "who confidence")}
    print(f"\n{a.label}: {len(tickets)} tickets x {a.runs} runs = {len(jobs)} reads, "
          f"{sum(r['failed'] for r in results)} failed")
    for name, ids in flips.items():
        print(f"  {name:20} changed on {len(ids)} of {len(tickets)} tickets {ids or ''}")
    for n, v in spreads.items():
        print(f"  {n:20} spread: average {st.mean(v):.2f}, largest {max(v):.2f}")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
