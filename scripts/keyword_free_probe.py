"""Does the model half of the classifier earn its place?

On all 33 gold tickets the model and the keyword layer agree about escalation exactly: 11 caught by
both, 0 caught by either alone. That is not evidence the model contributes nothing — it is evidence
the gold set cannot tell, because every escalating row in it happens to contain keyword vocabulary.

This probe answers the question directly. Six tickets that escalate in meaning and contain none of
the words the patterns look for, plus one control that reads urgent and must NOT escalate. The
keyword layer is verified silent on all of them before the model sees them, so every catch here is
the model's alone.

    python scripts/keyword_free_probe.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import rules  # noqa: E402
from app.models import TicketIn  # noqa: E402
from app.pipeline import process  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "data" / "keyword_free_escalations.jsonl"


def main() -> int:
    items = [json.loads(l) for l in PROBE.read_text().splitlines() if l.strip()]

    # Precondition. If a pattern has since been widened to cover one of these, the row is no longer
    # a test of the model and the probe must say so rather than quietly take credit for the rules.
    leaked = []
    for r in items:
        base = rules.rules_only_extraction(r["text"])
        _, hits, _ = rules.apply_escalation_rules(r["text"], base)
        if hits:
            leaked.append((r["id"], [h.rule for h in hits]))

    from _spend import confirm
    confirm(len(items), "keyword-free probe")
    with ThreadPoolExecutor(max_workers=4) as ex:
        ds = list(ex.map(lambda r: process(TicketIn(text=r["text"], external_id=r["id"]), persist=False), items))

    rows, caught, missed, false_pos = [], 0, [], []
    for r, d in zip(items, ds):
        got = d.extraction.escalate
        want = r["expect_escalate"]
        ok = got == want
        if want and got:
            caught += 1
        elif want and not got:
            missed.append(r["id"])
        elif not want and got:
            false_pos.append(r["id"])
        rows.append((r, d, ok))

    want_n = sum(1 for r in items if r["expect_escalate"])
    lines = [
        "# Does the model catch escalations the keywords cannot?",
        "",
        f"`scripts/keyword_free_probe.py` · {len(items)} tickets · {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Why this exists",
        "",
        "On the 33-row gold set the two halves of the classifier agree about escalation *exactly*:",
        "11 tickets caught by both, none caught by either alone. Read carelessly that says the model",
        "adds nothing. Read honestly it says the gold set cannot tell, because every escalating row in",
        "it contains keyword vocabulary — which is unsurprising, since the rows and the patterns were",
        "written by the same hand.",
        "",
        "So: tickets that escalate in meaning and contain **none** of the words the patterns look for.",
        "The keyword layer is checked silent on each one before the model sees it, so anything caught",
        "here is caught by judgement alone.",
        "",
        ("> **Precondition failed** — the keyword layer now fires on: "
         + ", ".join(f"`{i}` ({', '.join(h)})" for i, h in leaked)
         + ". Those rows no longer test the model.") if leaked else
        "Precondition verified: the keyword layer fires on none of them.",
        "",
        "## Result",
        "",
        f"| Escalations the keywords cannot see | **{caught} of {want_n} caught by the model** |",
        "|---|---|",
        f"| Missed | {', '.join(missed) if missed else 'none'} |",
        f"| Control ticket wrongly escalated | {', '.join(false_pos) if false_pos else 'no'} |",
        "",
        "| id | what makes it invisible to the keywords | should escalate | model said | |",
        "|---|---|---|---|---|",
    ]
    for r, d, ok in rows:
        lines.append(
            f"| `{r['id']}` | {r['why']} | {'yes' if r['expect_escalate'] else 'no (control)'} | "
            f"{'**escalated**' if d.extraction.escalate else 'did not escalate'}"
            f"{' — ' + ', '.join(x.value for x in d.extraction.escalation_reasons) if d.extraction.escalation_reasons else ''} | "
            f"{'✅' if ok else '❌'} |")

    lines += ["", "## The tickets", ""]
    for r, d, _ in rows:
        lines += [f"**{r['id']}** — {r['text']}", "",
                  f"> {d.extraction.escalation_reason_text}", ""]

    out = ROOT / "docs" / "KEYWORD-FREE-PROBE.md"
    out.write_text("\n".join(lines) + "\n")
    (ROOT / "data" / "eval-results").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "eval-results" / "keyword_free.json").write_text(
        json.dumps({"caught": caught, "want": want_n, "missed": missed, "false_pos": false_pos,
                    "decisions": [d.model_dump(mode="json") for d in ds]}, indent=2))
    print("\n".join(lines[:40]))
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
