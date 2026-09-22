# Repeatability: does it say the same thing twice?

`scripts/repeatability.py --repeats 5` · mode **rules** · 2026-09-22 16:22

Accuracy is the eval's job. This answers a different question: run the *same* ticket several
times and see whether the decision moves. It matters because somebody eventually has to
defend a routing decision, and "it depends what day you asked" is not a defence.

| ticket | category (agreement) | confidence mean / sd / range | urgency | escalate |
|---|---|---|---|---|
| `climb-03` | security (100%) | 0.00 / 0.000 / 0.00–0.00 | critical (100%) | yes (100%) |
| `climb-10` | bug (100%) | 0.00 / 0.000 / 0.00–0.00 | critical (100%) | no (100%) |
| `edge-15` | other (100%) | 0.00 / 0.000 / 0.00–0.00 | medium (100%) | no (100%) |
| `edge-28` | billing (100%) | 0.00 / 0.000 / 0.00–0.00 | medium (100%) | no (100%) |
| `climb-05` | spam (100%) | 0.00 / 0.000 / 0.00–0.00 | low (100%) | no (100%) |

## Summary

- **Category label unanimous on 5/5 tickets** across 5 runs each.
- **Escalation flag unanimous on 5/5 tickets.** This is the one that matters: a flag that flips between runs is not a safety guarantee.
- Confidence standard deviation averaged **0.000** (max 0.000) — the number a ticket gets is reproducible to about ±0.00.

**In keyword mode this is trivially true** — the fallback is pure regex and arithmetic, so every run is byte-identical. It is included as the floor: whatever the model does, the degraded path is perfectly reproducible, which is worth knowing when the model is down.

## What this does not show

Repeatable is not the same as correct, and it is not the same as calibrated. A system can be
perfectly consistent and consistently wrong; `docs/EVAL-*.md` is where accuracy lives. And a
stable 0.92 on a genuinely ambiguous ticket is still a bad 0.92 — see `DECISIONS.md` D34.
