"""Does it get the customer and the identifiers right?

    python scripts/extraction_probe.py
    CLASSIFIER_MODE=rules python scripts/extraction_probe.py

The gold set mostly tests routing. This tests extraction: company names from signatures, the
difference between a stated name and a guess, identifiers, and two traps where a company is named
in the text but is not the customer. Writes docs/EXTRACTION-<mode>.md.
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
from tests.gold import score_one  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    rows = [json.loads(l) for l in (ROOT / "data" / "extraction_cases.jsonl").read_text().splitlines() if l.strip()]
    mode = effective_mode()
    if mode == "llm":
        from _spend import confirm
        confirm(len(rows), "extraction probe")
    with ThreadPoolExecutor(max_workers=4) as ex:
        ds = list(ex.map(lambda r: process(TicketIn(text=r["text"], external_id=r["id"]), persist=False), rows))

    name_ok = id_ok = id_n = 0
    lines = [f"# Extraction: names, contacts, identifiers (mode={mode})", "",
             f"`scripts/extraction_probe.py` · {len(rows)} tickets · {time.strftime('%Y-%m-%d %H:%M')}", "",
             "| id | what it tests | expected customer | got | identifier | |", "|---|---|---|---|---|---|"]
    for r, d in zip(rows, ds):
        sc = score_one(r, d)
        c = d.extraction.customer
        name_ok += bool(sc["customer_ok"])
        want_id = r["expected"].get("identifier_contains")
        if want_id:
            id_n += 1
            id_ok += sc["identifier_ok"]
        got = c.name or (f"(guess) {c.best_guess}" if c.best_guess else "none")
        lines.append(
            f"| `{r['id']}` | {r['tests']} | {r['expected'].get('customer_name') or 'none'} | {got} | "
            f"{(('found' if sc['identifier_ok'] else 'MISSED') + ' ' + want_id) if want_id else ''} | "
            f"{'✅' if sc['customer_ok'] and sc['identifier_ok'] else '⚠️'} |")
    lines[4:4] = [f"**Customer name right: {name_ok} of {len(rows)}.** "
                  f"**Identifiers found: {id_ok} of {id_n}.** A name counts as right only if the company is "
                  "stated in the text; a guess from an email domain must stay a guess.", ""]
    out = ROOT / "docs" / f"EXTRACTION-{mode}.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
