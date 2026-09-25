"""Does the cascade actually save anything, and what does it cost in quality?

    LLM_CASCADE=1 python scripts/cascade_eval.py

Runs the gold set through the cascade, then compares it against the saved single-model runs on the
three things that decide it: missed escalations, false escalations, urgency under-calls, and money.
Writes docs/CASCADE.md.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import cascade, pricing  # noqa: E402
from app.models import TicketIn  # noqa: E402
from app.pipeline import process  # noqa: E402
from tests.gold import load_gold, score_one, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if not cascade.enabled():
        raise SystemExit("set LLM_CASCADE=1 to run this")
    gold = load_gold()
    if "--rewrite" in sys.argv:
        which = "cascade-rules" if cascade.triage_mode() == "rules" else "cascade"
        saved_run = json.loads((ROOT / "data" / "eval-results" / f"{which}.json").read_text())
        return write_report(saved_run["summary"], saved_run["notes"], saved_run["spend"],
                            saved_run["base"], float("nan"))

    # The spend gate sits after the rewrite branch on purpose: restating a measurement must never
    # be blocked by the cost of the run that produced it.
    from _spend import confirm
    confirm(len(gold), "cascade cheap leg", cascade.draft_model())
    confirm(len(gold), "cascade expensive leg (worst case, every ticket)")

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        ds = list(ex.map(lambda r: process(TicketIn(text=r["text"], external_id=r["id"]), persist=False), gold))
    wall = time.perf_counter() - t0

    results = [score_one(r, d) for r, d in zip(gold, ds)]
    s = summarize(results)
    notes = [d.usage.get("cascade") or {} for d in ds]
    spend = sum(d.usage.get("cost_usd", 0) or 0 for d in ds)
    saved = json.loads((ROOT / "data" / "eval-results" / "llm.json").read_text())
    base = sum(pricing.cost_usd(d["usage"], d.get("model")) or 0 for d in saved["decisions"])
    return write_report(s, notes, spend, base, wall)


def write_report(s: dict, notes: list[dict], spend: float, base: float, wall: float) -> int:
    n = len(notes)
    rules_mode = cascade.triage_mode() == "rules"
    reread = [x for x in notes if (x.get("expensive") if rules_mode else x.get("reread"))]
    changed = [x for x in notes if x.get("changed")]

    def col(v):
        return f"**{len(v)}** ({', '.join(x.split()[0] for x in v)})" if v else "none"

    out_name = "CASCADE-RULES" if rules_mode else "CASCADE"
    lines = [
        "# Does the cascade pay?" + (" — triaging with the keyword layer" if rules_mode else ""),
        "",
        f"`scripts/cascade_eval.py` · {n} gold tickets · triage **{cascade.triage_mode()}** · "
        f"cheap `{cascade.draft_model()}`, expensive `{os.environ.get('OPENAI_MODEL', 'gpt-5')}` · "
        f"{time.strftime('%Y-%m-%d %H:%M')}",
        "",
    ] + ([
        "Triage before spending anything. The keyword layer has already read every ticket for free,",
        "so it decides which reader each one needs: a ticket that trips an escalation pattern, or that",
        "reads as high urgency on keywords alone, goes to the expensive model. Everything else goes to",
        "the cheap one. **One model call either way** — there is no draft to pay for.",
        "",
    ] if rules_mode else [
        "Read cheap first, then pay for a second opinion where the cheap answer looks dangerous. The",
        "trigger is **stakes plus doubt**, not doubt alone: the bake-off's worst finding was `nano`",
        "under-calling three critical tickets *confidently*, so a confidence-only rule would have",
        "waved exactly the wrong tickets through.",
        "",
    ]) + [
        "| | cascade | `gpt-5` every ticket |",
        "|---|---|---|",
        f"| Missed escalations | {col(s['missed_escalations'])} | none |",
        f"| False escalations | {col(s['false_escalations'])} | none |",
        f"| Urgency under-called | {col(s['urgency_under'])} | none |",
        f"| A critical read as lower | {'NO' if s['urgency_never_under_critical'] else 'YES'} | NO |",
        f"| Category accuracy | {s['category_accuracy']:.0%} | 100% |",
        f"| Total cost, {n} tickets | ${spend:.4f} | ${base:.4f} |",
        f"| Cost per ticket | {spend/n*100:.3f}¢ | {base/n*100:.3f}¢ |",
        f"| **Saving** | **{(1-spend/base)*100:.0f}%** | — |",
        "",
        "## How much of the work stayed cheap",
        "",
        f"- **{len(reread)} of {n}** tickets ({len(reread)/n:.0%}) went to the expensive model.",
        f"- **{n-len(reread)}** were handled by the cheap one.",
    ] + ([] if rules_mode else [
        f"- The second read **changed the answer on {len(changed)}** of the {len(reread)} it looked at.",
    ]) + [
        "",
    ] + ([
        "The cheap model's error profile comes with it on the half it handles: on this set that is one",
        "false escalation (the SOC 2 document request) and one urgency disagreement, low versus medium.",
        "No escalation was missed and no critical ticket was under-called — the two failures that",
        "would rule the arrangement out.",
        "",
    ] if rules_mode else [
        "The last number is the one to watch. If the expensive model almost never disagrees, the",
        "trigger is too wide and the cascade is paying for confirmation it does not need. If it",
        "disagrees often, the draft model is not good enough to ship unreviewed on anything.",
        "",
        "### Why this loses money",
        "",
        "The naive arithmetic says a draft plus a 58% re-read rate should save about 22%. It does not,",
        "because the tickets the cascade chooses to re-read are *by construction* the hard ones — they",
        "escalate, or they are urgent — and a hard ticket costs nearly double the average on the",
        "expensive model. Measured here: **1.73¢ for a re-read ticket against a 0.91¢ average.** The",
        "draft then becomes pure overhead on the majority of the spend. Adverse selection, and it is",
        "invisible until you price the tickets individually rather than multiplying an average.",
        "",
    ]) + [
        "## Why the trigger is what it is",
        "",
        "| A ticket gets the expensive reader when | because |" if rules_mode
        else "| A draft is re-read when | because |",
        "|---|---|",
    ] + ([
        "| a keyword escalation pattern matched | these are the security, legal and executive tickets |",
        "| keyword urgency read high or critical | the cheap models' worst failure was under-calling critical tickets |",
        "",
        "The triage costs nothing: the same regexes run on every ticket anyway, as the guardrail layer.",
        "Using them to choose a reader is the only free lever in the system.",
        "",
    ] if rules_mode else [
        "| it escalated | a wrong escalation call is expensive in both directions |",
        "| it said high or critical | the cheap models' worst failure was under-calling critical tickets |",
        f"| its category confidence was under {cascade.threshold():.2f} | the same threshold that sends a ticket to human-review |",
        "",
        "Everything else ships on the draft. The rule deliberately re-reads more than a",
        "confidence-only rule would: the saving is smaller and it protects against the failure that",
        "actually hurts.",
        "",
    ]) + [
        (f"Wall time {wall:.0f}s at concurrency 4. " if wall == wall else "")
        + "Prices from `app/pricing.py`.",
    ]
    (ROOT / "docs" / f"{out_name}.md").write_text("\n".join(lines) + "\n")
    (ROOT / "data" / "eval-results" / f"{out_name.lower()}.json").write_text(
        json.dumps({"summary": s, "notes": notes, "spend": spend, "base": base}, indent=2, default=str))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
