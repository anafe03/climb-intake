"""Go looking for failures on purpose.

The gold set reports 100% on escalation in both modes. A number like that is either a very easy
test or a test written by the same person who wrote the thing being tested — here it is some of
both. This set exists to find the edge, not to be passed: twelve tickets built to defeat a keyword
list, a classifier, or both, with the attack named on every row.

    python scripts/stress.py                  # model path
    CLASSIFIER_MODE=rules python scripts/stress.py

Writes docs/STRESS.md. A failing row is the point, not a defect.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.models import TicketIn  # noqa: E402
from app.pipeline import effective_mode, process  # noqa: E402
from tests.gold import score_one, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "data" / "adversarial.jsonl"


def main() -> int:
    rows = [json.loads(l) for l in SET.read_text().splitlines() if l.strip()]
    mode = effective_mode()
    if mode == "llm":
        from _spend import confirm
        confirm(len(rows), "stress set")
    with ThreadPoolExecutor(max_workers=4) as ex:
        ds = list(ex.map(lambda r: process(TicketIn(text=r["text"], external_id=r["id"]), persist=False), rows))
    scored = [score_one(r, d) for r, d in zip(rows, ds)]
    s = summarize(scored)

    missed = [r["id"] for r in scored if r["missed_escalation"]]
    false = [r["id"] for r in scored if r["false_escalation"]]
    under = s["urgency_under"]

    lines = [
        f"# Stress set: where does it break? (mode={mode})",
        "",
        f"`scripts/stress.py` · {len(rows)} tickets written to defeat it · {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "The gold set scores 100% on escalation in both modes. That is a suspicious number, and the",
        "honest response is to go looking for the edge rather than quote it. Every row here names the",
        "attack it is making. **A failing row is the output, not a defect.**",
        "",
        "| | |",
        "|---|---|",
        f"| Missed escalations | {', '.join(missed) if missed else '**none**'} |",
        f"| False escalations | {', '.join(false) if false else '**none**'} |",
        f"| Urgency under-called | {', '.join(x.split()[0] for x in under) if under else '**none**'} |",
        f"| Category (strict) | {s['category_strict']:.0%} |",
        "",
        "| id | the attack | wanted | got | |",
        "|---|---|---|---|---|",
    ]
    for r, d, sc in zip(rows, ds, scored):
        e, x = r["expected"], d.extraction
        want = f"{e['category']}/{e['urgency']}/{'ESC' if e['escalate'] else 'no esc'}"
        got = f"{x.category.value}/{x.urgency.value}/{'ESC' if x.escalate else 'no esc'}"
        ok = not sc["missed_escalation"] and not sc["false_escalation"] and sc["urgency_ok"] and sc["category_ok"]
        lines.append(f"| `{r['id']}` | {r['attack']} | {want} | {got} | {'✅' if ok else '⚠️'} |")

    lines += ["", "## What each row was trying to do, and what happened", ""]
    for r, d, sc in zip(rows, ds, scored):
        x = d.extraction
        hits = ", ".join(h.rule for h in d.rule_hits) or "no keyword matched"
        lines += [
            f"**{r['id']} — {r['attack']}**", "",
            f"> {r['text'][:300]}{'…' if len(r['text']) > 300 else ''}", "",
            f"- Wanted: `{r['expected']['category']}` / `{r['expected']['urgency']}` / "
            f"{'escalate' if r['expected']['escalate'] else 'no escalation'}",
            f"- Got: `{x.category.value}` / `{x.urgency.value}` / "
            f"{'escalated' if x.escalate else 'not escalated'} — keywords: {hits}",
            f"- Reasoning: {x.escalation_reason_text}",
            "",
        ]

    out = ROOT / "docs" / f"STRESS-{mode}.md"
    out.write_text("\n".join(lines) + "\n")
    (ROOT / "data" / "eval-results").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "eval-results" / f"stress-{mode}.json").write_text(
        json.dumps({"summary": s, "results": scored}, indent=2, default=str))
    print("\n".join(lines[:26]))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
