"""Record a set of decisions once, so a demo never has to classify live.

    python scripts/record_fixture.py samples    # from the saved gold eval run — free
    python scripts/record_fixture.py demo       # runs the demo set through the model — costs

Writes data/recorded/<set>.json. The service replays these into the audit store with no model
call, which is what `POST /tickets/load-recorded` does. A live demo should read ONE ticket live —
that is the interesting moment — and replay the rest, rather than watching a spinner for minutes
and betting the presentation on a network that might not cooperate.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.models import Decision, TicketIn  # noqa: E402
from app.pipeline import process  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "recorded"


def from_gold_eval() -> list[Decision]:
    """The ten Climb samples already ran in the last llm eval. Reuse them rather than pay twice."""
    saved = json.loads((ROOT / "data" / "eval-results" / "llm.json").read_text())
    decisions = [Decision(**d) for d in saved["decisions"]]
    picked = [d for d in decisions if (d.ticket.external_id or "").startswith("climb-")]
    picked.sort(key=lambda d: d.ticket.external_id or "")
    if len(picked) != 10:
        raise SystemExit(f"expected 10 climb decisions in the saved eval, found {len(picked)}")
    return picked


def run_live(path: Path, source: str) -> list[Decision]:
    from _spend import confirm
    items = json.loads(path.read_text())
    confirm(len(items), f"recording {source}")
    tickets = [TicketIn(text=i["text"], source=source, external_id=str(i["id"])) for i in items]
    with ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(lambda t: process(t, persist=False), tickets))


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "samples"
    if which == "samples":
        decisions = from_gold_eval()
    elif which == "demo":
        decisions = run_live(ROOT / "data" / "demo_tickets.json", "demo-set")
    else:
        raise SystemExit("usage: record_fixture.py [samples|demo]")

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "set": which,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": next((d.model for d in decisions if d.model), None),
        "decisions": [d.model_dump(mode="json") for d in decisions],
    }
    out = OUT / f"{which}.json"
    out.write_text(json.dumps(payload, indent=2))
    live = sum(1 for d in decisions if d.mode == "llm")
    print(f"wrote {out.relative_to(ROOT)}: {len(decisions)} decisions, {live} read by {payload['model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
