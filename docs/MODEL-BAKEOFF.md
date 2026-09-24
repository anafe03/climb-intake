# Model bake-off: what does this job actually need?

`scripts/model_bakeoff.py` · 10 tickets (climb-01, climb-02, climb-03…) · 2026-09-24 11:01

Same prompt, same schema, same guardrails — only the model changes. **Escalation recall is the
metric that decides this.** A cheaper model is only interesting if it never misses one; every
other number is a trade you can discuss.

| model | escalation recall | missed | category | urgency exact | p50 | cost / ticket | vs top |
|---|---|---|---|---|---|---|---|
| `gpt-5-2025-08-07` | **100%** | none | 100% | 80% | 28.4 s | $1.717¢ | 1.00x |
| `gpt-5-mini-2025-08-07` | **100%** | none | 100% | 90% | 15.8 s | $0.328¢ | 0.19x |
| `gpt-5-nano-2025-08-07` | **100%** | none | 100% | 90% | 21.0 s | $0.121¢ | 0.07x |

## Tokens measured per ticket

| model | input | of which cached | output |
|---|---|---|---|
| `gpt-5-2025-08-07` | 2794 | 2688 | 1670 |
| `gpt-5-mini-2025-08-07` | 2794 | 2419 | 1561 |
| `gpt-5-nano-2025-08-07` | 2514 | 1882 | 2917 |

Prices are the per-million rates in `scripts/model_bakeoff.py`; **verify them against current
list price before quoting a figure.** The token counts are measured from `response.usage`.

## Reading it

At this volume the absolute cost is noise — the interesting number is the ratio, and what you
give up for it. The honest way to use this table is: find the cheapest model that still shows
100% escalation recall and no missed escalations, run that in production, and keep the
expensive one for the human-review queue where the classifier already said it was unsure.

Two caveats worth saying out loud: this is 10 tickets, so a single disagreement moves a column
by 10 points, and the guardrail layer sits underneath every row — a model that misses an
escalation here would still have been caught by the keyword rules before the ticket shipped.
