"""Side-by-side of two eval runs (default: rules vs llm). Shows only rows that differ.

    python scripts/compare_evals.py            # data/eval-results/rules.json vs llm.json
    python scripts/compare_evals.py a.json b.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "eval-results"


def load(p):
    d = json.loads(Path(p).read_text())
    return d["summary"], {r["id"]: r for r in d["results"]}


def main():
    a, b = (sys.argv[1], sys.argv[2]) if len(sys.argv) == 3 else (ROOT / "rules.json", ROOT / "llm.json")
    for p in (a, b):
        if not Path(p).exists():
            print(f"missing {p}. Run scripts/eval.py in that mode first.")
            return 1
    sa, ra = load(a)
    sb, rb = load(b)
    print(f"{'metric':32} {'A':>8} {'B':>8}   A={Path(a).name} B={Path(b).name}")
    for k in ("escalation_recall", "category_accuracy", "urgency_exact", "urgency_accuracy", "customer_accuracy", "identifier_accuracy"):
        print(f"{k:32} {sa[k]:>8.0%} {sb[k]:>8.0%}")
    print(f"{'missed_escalations':32} {str(sa['missed_escalations']):>8} {str(sb['missed_escalations']):>8}")
    print(f"{'false_escalations':32} {str(sa['false_escalations']):>8} {str(sb['false_escalations']):>8}")
    print("\nRows that differ (category/urgency/escalate):")
    for rid in ra:
        ga, gb = ra[rid]["got"], rb.get(rid, {}).get("got")
        if not gb:
            continue
        fa = f"{ga['category']}/{ga['urgency']}/{'ESC' if ga['escalate'] else '-'}"
        fb = f"{gb['category']}/{gb['urgency']}/{'ESC' if gb['escalate'] else '-'}"
        if fa != fb:
            e = ra[rid]["expected"]
            print(f"  {rid:9} A {fa:28} B {fb:28} expected {e['category']}/{e['urgency']}/{'ESC' if e['escalate'] else '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
