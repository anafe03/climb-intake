"""Export the tickets behind the escalation recall number, so the number can be clicked.

    python scripts/export_evidence.py

Reads saved runs; calls no model. Writes data/measured/escalation_evidence.json, which is committed
and shipped in the image. For every ticket that should escalate it records whether the model caught
it and whether a keyword rule also fired, which is what shows the model catching tickets the
keywords cannot see.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import rules  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data" / "eval-results"


def keywords_fire(text: str) -> bool:
    # The keyword layer is deterministic, so recomputing it gives exactly what the run saw.
    base = rules.rules_only_extraction(text)
    _, hits, _ = rules.apply_escalation_rules(text, base)
    return bool(hits)


def jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


GROUPS = [("climb", "Provided tickets", "The 10 tickets Climb supplied."),
          ("edge", "Edge cases", "Tickets written to test the hard parts."),
          ("adversarial", "Trick tickets", "Tickets written to break it."),
          ("keyword-free", "No keywords at all",
           "Tickets with none of the words the keyword list looks for. Only the model can catch these.")]


def from_bakeoff(path: Path) -> list[dict]:
    """Use the gpt-5 leg of the all-examples comparison, so this list and the table are one run."""
    saved = json.loads(path.read_text())
    groups = []
    for key, name, about in GROUPS:
        rows = []
        for r, d in zip(saved["rows"], saved["decisions"]):
            grp = r.get("group", "")
            if grp != key or not r["expected"]["escalate"]:
                continue
            rows.append({"id": r["id"], "text": r["text"], "caught": d["extraction"]["escalate"],
                         "model_alone": (d.get("llm_extraction") or {}).get("escalate", False),
                         "keywords": bool([h for h in d.get("rule_hits") or [] if h.get("reason")])})
        if rows:
            groups.append({"name": name, "about": about, "tickets": rows})
    return groups


def main() -> int:
    run = RES / "bakeoff-gpt-5-low.json"
    if run.exists():
        groups = from_bakeoff(run)
        out = ROOT / "data" / "measured" / "escalation_evidence.json"
        out.write_text(json.dumps({"groups": groups}, indent=2))
        for g in groups:
            c = sum(t["caught"] for t in g["tickets"])
            k = sum(not t["keywords"] and t["caught"] for t in g["tickets"])
            print(f"{g['name']:20} {c}/{len(g['tickets'])} caught, {k} with no keyword")
        print(f"wrote {out.relative_to(ROOT)} from the all-examples run")
        return 0
    groups = []

    gold = {r["id"]: r for r in jsonl(ROOT / "data" / "gold.jsonl")}
    llm = json.loads((RES / "llm.json").read_text())
    rows = []
    for d in llm["decisions"]:
        g = gold[d["ticket"]["external_id"]]
        if not g["expected"]["escalate"]:
            continue
        rows.append({"id": g["id"], "text": g["text"],
                     "caught": d["extraction"]["escalate"],
                     "model_alone": (d.get("llm_extraction") or {}).get("escalate", False),
                     "keywords": bool(d.get("rule_hits"))})
    groups.append({"name": "Gold set", "about": "The 10 provided tickets plus 23 edge cases.",
                   "tickets": sorted(rows, key=lambda r: r["id"])})

    adv = {r["id"]: r for r in jsonl(ROOT / "data" / "adversarial.jsonl")}
    stress = json.loads((RES / "stress-llm.json").read_text())
    rows = []
    for r in stress["results"]:
        a = adv[r["id"]]
        if not a["expected"]["escalate"]:
            continue
        rows.append({"id": a["id"], "text": a["text"], "caught": r["escalated"],
                     "model_alone": r["escalated"], "keywords": keywords_fire(a["text"]),
                     "attack": a["attack"]})
    groups.append({"name": "Adversarial set", "about": "Tickets written to break it.",
                   "tickets": rows})

    kf = {r["id"]: r for r in jsonl(ROOT / "data" / "keyword_free_escalations.jsonl")}
    probe = json.loads((RES / "keyword_free.json").read_text())
    rows = []
    for d in probe["decisions"]:
        k = kf[d["ticket"]["external_id"]]
        if not k["expect_escalate"]:
            continue
        rows.append({"id": k["id"], "text": k["text"], "caught": d["extraction"]["escalate"],
                     "model_alone": (d.get("llm_extraction") or {}).get("escalate", False),
                     "keywords": bool(d.get("rule_hits")), "attack": k["why"]})
    groups.append({"name": "No keywords at all",
                   "about": "Tickets with none of the words the keyword rules look for. Only the model can catch these.",
                   "tickets": rows})

    out = ROOT / "data" / "measured" / "escalation_evidence.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"groups": groups}, indent=2))
    for g in groups:
        c = sum(t["caught"] for t in g["tickets"])
        k = sum(not t["keywords"] and t["caught"] for t in g["tickets"])
        print(f"{g['name']:20} {c}/{len(g['tickets'])} caught, {k} of them with no keyword")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
