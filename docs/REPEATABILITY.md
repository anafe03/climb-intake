# Repeatability: does it say the same thing twice?

`scripts/repeatability.py --repeats 3` · mode **llm** · 2026-09-22 18:16

Accuracy is the eval's job. This answers a different question: run the *same* ticket several
times and see whether the decision moves. It matters because somebody eventually has to
defend a routing decision, and "it depends what day you asked" is not a defence.

| ticket | escalate | category | confidence: mean / sd / min-max | urgency |
|---|---|---|---|---|
| `climb-03` | **yes** (100%) | security (100%) | 0.78 / 0.029 / 0.75–0.80 | critical (100%) |
| `climb-10` | **no** (100%) | bug (100%) | 0.80 / 0.050 / 0.75–0.85 | critical (100%) |
| `edge-28` | **no** (100%) | other (100%) | 0.67 / 0.104 / 0.55–0.75 | medium (100%) |
| `climb-05` | **no** (100%) | spam (100%) | 0.98 / 0.000 / 0.98–0.98 | low (100%) |

## Summary

- **Category label unanimous on 4/4 tickets** across 3 runs each.
- **Escalation flag unanimous on 4/4 tickets.** This is the one that matters: a flag that flips between runs is not a safety guarantee.
- Confidence standard deviation averaged **0.046** (max 0.104) — the number a ticket gets is reproducible to about ±0.21.

**Model: `gpt-5-2025-08-07`.** Nothing is pinned — no seed, no temperature control — so this is the model's natural run-to-run spread, not a best case.

## Three configurations, measured

The same four tickets, three runs each, under three setups. Two things changed between the first row
and the second: the model, and the prompt. So the third row was run to separate them.

| setup | escalation flag | category label | confidence sd (avg / max) | does the score discriminate? |
|---|---|---|---|---|
| gpt-5, confidence-as-a-grade prompt | 100% | 100% | 0.021 / 0.027 | no — 0.92 on an ambiguous ticket, 0.92 on a borderline one |
| gpt-5, confidence-as-a-share prompt | 100% | 100% | 0.046 / 0.104 | yes — 0.98 spam, 0.80 clear bug, 0.67 ambiguous |
| gpt-5-nano, same share prompt | 100% | 75% | 0.073 / 0.176 | yes, but one label flipped between runs |

### What that says

**The escalation flag never moved.** Four tickets, three configurations, twelve runs each way, and it
was unanimous every time. That is the number this system is judged on, and it is the one that held.

**Asking for a share of opinion roughly doubled the variance, and that was the right trade.** Under
the old prompt the score was stable and useless: it said 0.92 whether the ticket was obvious or
genuinely arguable. Under the new one it moves more between runs, but it separates a spam email
(0.98) from a request two people would file differently (0.67). A stable number that tells you
nothing is worse than a noisier one that does.

**Nano is not the free lunch the bake-off implied.** `MODEL-BAKEOFF.md` measured accuracy once and
found nano equal to gpt-5 across ten tickets at six percent of the cost. Run the same ticket three
times and nano flips a category label and carries three times the confidence spread. Accuracy
measured once is not the same as stability, and the cheap model looks worse on the second one. The
recommendation stands, but with a condition: nano for volume, and keep the review queue, because it
is where an unstable label lands.

## What this does not show

Repeatable is not the same as correct, and it is not the same as calibrated. A system can be
perfectly consistent and consistently wrong; `docs/EVAL-*.md` is where accuracy lives. And a
stable 0.92 on a genuinely ambiguous ticket is still a bad 0.92 — see `DECISIONS.md` D34.
