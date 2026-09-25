"""Record genuine failed extractions, so the demo can show what a failure looks like.

    python scripts/record_failures.py

Every ticket here is sent to the real model with a deadline far too short to meet, so the call
genuinely times out and the pipeline falls back to the keyword rules. Nothing is mocked: the error
text in each record is what the client raised. Timeouts are the failure that actually happens in
production; the slowest real reads have run past 40 seconds.

The three tickets are chosen to show the range of what the fallback does:
  climb-03  keywords still catch the escalation, so the fallback is fine
  climb-01  an ordinary billing ticket, still routed correctly
  kf-02     a legal threat written with 'solicitors', which the keywords cannot see, so the
            fallback misses the escalation. That is the cost of the model being down.
Writes data/recorded/failures.json for POST /tickets/load-recorded?fixture=failures.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ["LLM_TIMEOUT_S"] = "0.2"          # nothing real finishes in 200 ms
os.environ["LLM_CONNECTION_RETRIES"] = "0"   # fail once, not four times
os.environ["LLM_MAX_RETRIES"] = "0"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models import TicketIn  # noqa: E402
from app.pipeline import effective_mode, process  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def jsonl(path: Path) -> dict[str, dict]:
    return {r["id"]: r for r in (json.loads(l) for l in path.read_text().splitlines() if l.strip())}


def main() -> int:
    if effective_mode() != "llm":
        raise SystemExit("needs an API key: the point is a real call that really fails")
    gold = jsonl(ROOT / "data" / "gold.jsonl")
    kf = jsonl(ROOT / "data" / "keyword_free_escalations.jsonl")
    picks = [("climb-03", gold["climb-03"]["text"]),
             ("climb-01", gold["climb-01"]["text"]),
             ("kf-02", kf["kf-02"]["text"])]

    decisions = []
    for tid, text in picks:
        d = process(TicketIn(text=text, source="failures", external_id=tid), persist=False)
        if d.mode == "llm":
            raise SystemExit(f"{tid} did not fail; the deadline was not short enough")
        decisions.append(d)
        print(f"{tid}: mode={d.mode} escalate={d.extraction.escalate} queue={d.queue}\n"
              f"        error: {d.error}")

    out = ROOT / "data" / "recorded" / "failures.json"
    out.write_text(json.dumps({
        "set": "failures",
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": None,
        "decisions": [d.model_dump(mode="json") for d in decisions],
    }, indent=2))
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
