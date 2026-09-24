"""Run the gold set through the pipeline and write a scorecard.

    python scripts/eval.py            # mode from env (auto)
    CLASSIFIER_MODE=rules python scripts/eval.py
Writes docs/EVAL-<mode>.md and data/eval-results/<mode>.json
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
from app.models import TicketIn  # noqa: E402
from app.pipeline import effective_mode, process  # noqa: E402
from tests.gold import load_gold, score_one, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    # --rescore re-runs the scoring over a saved run instead of calling the model again. Adding a
    # metric should not cost another eval: the decisions are already on disk, and what changed is
    # how they are judged.
    rescore = "--rescore" in sys.argv
    mode = effective_mode()
    if rescore:
        mode = next((a for a in sys.argv[1:] if not a.startswith("-")), mode)
    gold = load_gold()
    if rescore:
        from app.models import Decision
        saved = json.loads((ROOT / "data" / "eval-results" / f"{mode}.json").read_text())
        decisions = [Decision(**d) for d in saved["decisions"]]
        by_id = {d.ticket.external_id: d for d in decisions}
        decisions = [by_id[r["id"]] for r in gold]
        wall = float("nan")
    else:
        if mode == "llm":
            from _spend import confirm
            confirm(len(gold), "gold eval")
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=int(os.environ.get("BATCH_CONCURRENCY", "4"))) as ex:
            decisions = list(ex.map(lambda r: process(TicketIn(text=r["text"], source="eval", external_id=r["id"]), persist=False), gold))
        wall = time.perf_counter() - t0
    results = [score_one(r, d) for r, d in zip(gold, decisions)]
    s = summarize(results)
    tokens_in = sum(d.usage.get("input_tokens", 0) for d in decisions)
    tokens_out = sum(d.usage.get("output_tokens", 0) for d in decisions)
    lat = sorted(d.latency_ms for d in decisions)
    p50, p95 = lat[len(lat) // 2], lat[int(len(lat) * 0.95) - 1]
    model = next((d.model for d in decisions if d.model), None)

    lines = [
        f"# Eval scorecard: mode={mode}" + (f", model={model}" if model else ""),
        "",
        f"Generated {time.strftime('%Y-%m-%d %H:%M')} on {s['n']} gold tickets (10 Climb samples + {s['n'] - 10} edge cases)."
        + (" Scoring re-run over the saved decisions; the model was not called again." if rescore else ""),
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Escalation recall (must-escalate tickets caught) | **{s['escalation_recall']:.0%}** |",
        f"| Missed escalations | {s['missed_escalations'] or 'none'} |",
        f"| False escalations (not tolerated by gold) | {s['false_escalations'] or 'none'} |",
        f"| Escalation reason accuracy | {s['reasons_accuracy']:.0%} |",
        f"| Category accuracy (ambiguity-aware) | {s['category_accuracy']:.0%} |",
        f"| Urgency exact / within tolerance | {s['urgency_exact']:.0%} / {s['urgency_accuracy']:.0%} |",
        f"| Urgency **under**-called (said calmer than gold) | {s['urgency_under_rate']:.0%} \u2014 {s['urgency_under'] or 'none'} |",
        f"| Urgency over-called (said more urgent than gold) | {s['urgency_over_rate']:.0%} \u2014 {s['urgency_over'] or 'none'} |",
        f"| Under-calls on tickets gold does NOT mark ambiguous | {s['urgency_hard_under'] or 'none'} |",
        f"| Any critical ticket read as less than critical | {'NO' if s['urgency_never_under_critical'] else 'YES \u2014 investigate'} |",
        f"| Customer name accuracy (incl. correctly null) | {s['customer_accuracy']:.0%} |",
        f"| Identifier extraction | {s['identifier_accuracy']:.0%} |",
        f"| Overclaimed sender confidence (safety: must be none) | {s['overconfidence'] or 'none'} |",
        f"| Sender-inference confidence within expected band | {s['confidence_calibration']:.0%} |",
        f"| Confidence misses | {s['confidence_misses'] or 'none'} |",
        f"| Every guess carries its basis | {'yes' if s['basis_always_given'] else 'NO'} |",
        f"| Latency p50 / p95 per ticket | {p50} ms / {p95} ms |",
        f"| Wall time (concurrency {os.environ.get('BATCH_CONCURRENCY', '4')}) | {'not re-run' if rescore else f'{wall:.1f} s'} |",
        f"| Tokens in / out | {tokens_in} / {tokens_out} |",
        "",
        "## Why urgency is reported by direction",
        "",
        "Accuracy scores an under-call and an over-call as the same mistake. They are not. This is a",
        "screening test: calling a well patient sick costs a second look, calling a sick patient well",
        "costs the thing the test exists for. An over-called ticket reaches a queue faster than it",
        "needed to and someone downgrades it. An under-called ticket sits.",
        "",
        "So the number to read is **under-calls**, and specifically under-calls on tickets the gold set",
        "does *not* mark ambiguous on urgency \u2014 the rest are disagreements the gold set already",
        "licenses. The same asymmetry is built into the guardrail layer, which may raise urgency and",
        "never lower it.",
        "",
        "## Per-ticket",
        "",
        "| id | expected | got | esc ok | cat ok | urg ok | queue |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        e, g = r["expected"], r["got"]
        ok = lambda b: "✅" if b else "❌"
        lines.append(f"| {r['id']} | {e['category']}/{e['urgency']}/{'ESC' if e['escalate'] else '-'} | {g['category']}/{g['urgency']}/{'ESC' if g['escalate'] else '-'} {('['+', '.join(g['reasons'])+']') if g['reasons'] else ''} | {ok(not r['missed_escalation'] and not r['false_escalation'])} | {ok(r['category_ok'])} | {ok(r['urgency_ok'])} | {r['queue']} |")
    lines += ["", "## Rationales (model output, verbatim)", ""]
    for r, d in zip(gold, decisions):
        lines.append(f"**{r['id']}** — {d.extraction.rationale}")
        if d.overrides:
            lines.append("  - overrides: " + "; ".join(d.overrides))
        lines.append("")

    out_md = ROOT / "docs" / f"EVAL-{mode}.md"
    out_md.write_text("\n".join(lines))
    out_json = ROOT / "data" / "eval-results"
    out_json.mkdir(parents=True, exist_ok=True)
    (out_json / f"{mode}.json").write_text(json.dumps({"summary": s, "results": results, "decisions": [d.model_dump() for d in decisions]}, indent=2, default=str))
    print("\n".join(lines[:16]))
    print(f"\nwrote {out_md.relative_to(ROOT)}")
    return 0 if not s["missed_escalations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
