"""Run the same tickets repeatedly and report how much the answers move.

    python scripts/repeatability.py --repeats 5            # gold subset, current mode
    CLASSIFIER_MODE=rules python scripts/repeatability.py  # deterministic baseline

Writes docs/REPEATABILITY.md. The question it answers is not "is it accurate" — the eval does that —
but "would it say the same thing twice", which is what somebody asks when they have to defend a
routing decision to a customer.
"""
from __future__ import annotations

import argparse
import os
import statistics as st
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models import TicketIn  # noqa: E402
from app.pipeline import effective_mode, process  # noqa: E402
from tests.gold import load_gold  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# A spread of difficulty: one unambiguous, two borderline, one that must always escalate, one spam.
DEFAULT_IDS = ["climb-03", "climb-10", "edge-15", "edge-28", "climb-05"]


def agreement(values) -> tuple[str, float]:
    c = Counter(values).most_common(1)[0]
    return c[0], c[1] / len(values)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--ids", nargs="*", default=DEFAULT_IDS)
    a = ap.parse_args()

    mode = effective_mode()
    gold = {r["id"]: r for r in load_gold()}
    rows = [gold[i] for i in a.ids if i in gold]
    model_name = None

    lines = [
        "# Repeatability: does it say the same thing twice?",
        "",
        f"`scripts/repeatability.py --repeats {a.repeats}` · mode **{mode}** · "
        f"{time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "Accuracy is the eval's job. This answers a different question: run the *same* ticket several",
        "times and see whether the decision moves. It matters because somebody eventually has to",
        "defend a routing decision, and \"it depends what day you asked\" is not a defence.",
        "",
        "| ticket | escalate | category | confidence: mean / sd / min-max | urgency |",
        "|---|---|---|---|---|",
    ]
    all_sd, label_unanimous, esc_unanimous = [], 0, 0

    for row in rows:
        with ThreadPoolExecutor(max_workers=min(a.repeats, 5)) as ex:
            ds = list(ex.map(lambda _: process(TicketIn(text=row["text"]), persist=False), range(a.repeats)))
        model_name = model_name or next((d.model for d in ds if d.model), None)
        cats = [d.extraction.category.value for d in ds]
        cfs = [d.extraction.category_confidence for d in ds]
        urgs = [d.extraction.urgency.value for d in ds]
        escs = [d.extraction.escalate for d in ds]

        cat, cat_agree = agreement(cats)
        urg, urg_agree = agreement(urgs)
        esc, esc_agree = agreement(escs)
        sd = st.stdev(cfs) if len(set(cfs)) > 1 else 0.0
        all_sd.append(sd)
        label_unanimous += cat_agree == 1.0
        esc_unanimous += esc_agree == 1.0

        lines.append(
            f"| `{row['id']}` | **{'yes' if esc else 'no'}** ({esc_agree:.0%}) | {cat} ({cat_agree:.0%}) | "
            f"{st.mean(cfs):.2f} / {sd:.3f} / {min(cfs):.2f}–{max(cfs):.2f} | {urg} ({urg_agree:.0%}) |"
        )

    n = len(rows)
    lines += [
        "",
        "## Summary",
        "",
        f"- **Category label unanimous on {label_unanimous}/{n} tickets** across {a.repeats} runs each.",
        f"- **Escalation flag unanimous on {esc_unanimous}/{n} tickets.** This is the one that matters: "
        "a flag that flips between runs is not a safety guarantee.",
        f"- Confidence standard deviation averaged **{st.mean(all_sd):.3f}** "
        f"(max {max(all_sd):.3f}) — the number a ticket gets is reproducible to about ±{max(all_sd)*2:.2f}.",
    ]
    if mode == "rules":
        lines += [
            "",
            "**In keyword mode this is trivially true** — the fallback is pure regex and arithmetic, so "
            "every run is byte-identical. It is included as the floor: whatever the model does, the "
            "degraded path is perfectly reproducible, which is worth knowing when the model is down.",
        ]
    else:
        lines += [
            "",
            f"**Model: `{model_name}`.** Nothing is pinned — no seed, no temperature control — so this "
            "is the model's natural run-to-run spread, not a best case.",
        ]
    lines += [
        "",
        "## What this does not show",
        "",
        "Repeatable is not the same as correct, and it is not the same as calibrated. A system can be",
        "perfectly consistent and consistently wrong; `docs/EVAL-*.md` is where accuracy lives. And a",
        "stable 0.92 on a genuinely ambiguous ticket is still a bad 0.92 — see `DECISIONS.md` D34.",
    ]

    out = ROOT / "docs" / "REPEATABILITY.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
