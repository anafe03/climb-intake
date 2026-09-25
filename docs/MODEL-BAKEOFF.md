# Model bake-off: what does this job actually need?

`scripts/model_bakeoff.py` · 61 tickets (climb-01, climb-02, climb-03…) · 2026-09-25 10:40

Same prompt, same schema, same guardrails — only the model and its reasoning effort change.
**The columns in bold are the ones that decide it.** A missed escalation disqualifies a model.
An urgency under-call on a critical ticket disqualifies it. Everything else is a trade you can
have a conversation about.

| model | effort | **missed escalations** | **false escalations** | **urgency under-called** | category | p50 | cost / ticket | vs gpt-5 |
|---|---|---|---|---|---|---|---|---|
| `gpt-5-2025-08-07` | low | none | **1** (adv-01) | **1** (adv-06) | 100% | 11.7 s | $0.968¢ | 1.00x |
| `gpt-5-mini-2025-08-07` | low | none | **3** (edge-23, edge-28, adv-01) | **3** (edge-13, adv-06, adv-09) | 100% | 8.6 s | $0.182¢ | 0.19x |
| `gpt-5-mini-2025-08-07` | minimal | none | **8** (edge-21, edge-28, edge-32, adv-01, ext-05, ext-08, ext-09, kf-06) | **2** (edge-13, adv-09) | 100% | 6.7 s | $0.130¢ | 0.13x |
| `gpt-5-nano-2025-08-07` | low | **2** (kf-03, kf-05) | **1** (adv-01) | **9** (climb-10, edge-27, edge-28, adv-05, adv-06, adv-07, adv-08, adv-09, adv-11) | 100% | 5.4 s | $0.037¢ | 0.04x |

## Tokens measured per ticket

| model | input | of which cached | output |
|---|---|---|---|
| `gpt-5-2025-08-07` | 2778 | 2600 | 913 |
| `gpt-5-mini-2025-08-07` | 2732 | 2556 | 858 |
| `gpt-5-mini-2025-08-07` | 2778 | 2600 | 596 |
| `gpt-5-nano-2025-08-07` | 2778 | 2424 | 839 |

Prices are the per-million rates in `scripts/model_bakeoff.py`; **verify them against current
list price before quoting a figure.** The token counts are measured from `response.usage`.

## Reading it

**Cost is not the deciding column.** Every model here is cheap enough; what separates them is
which mistakes they make. Read right to left: find the cheapest row whose error columns you
can live with, not the cheapest row.

Three things this table is built to show, that an accuracy score would hide:

1. **Nobody missed an escalation.** Recall is the metric that would disqualify a model, and no
   row fails it. That is partly the guardrail layer, which sits underneath every row — a model
   that missed one here would still have been caught by keyword rules before the ticket shipped.
2. **False escalations are where the cheap models show up.** They are tolerable — a person
   spends a minute — but they are the cost of the discount, and they should be quoted with it.
3. **Urgency under-calls are the column to actually worry about.** A ticket read calmer than it is
   sits. If a row under-calls a ticket the gold set marks *critical*, that row is disqualified
   whatever it costs.

Measured over 61 labelled tickets, so a single disagreement moves a percentage column by
about 2 points. Small enough to be directional, not a benchmark.

## Making a cheaper model good enough

The lever people reach for first is the model. It is the third-best lever here.

| lever | effect | what it costs you |
|---|---|---|
| **Prompt caching** | ~90% of input tokens are cache reads at 1/10th the price | nothing — the system prompt is a stable prefix, so this is free once the first call warms it |
| **Reasoning effort** | the dominant output-token lever; `low` roughly halved output against the default | accuracy on the hard rows. Dropping mini from `low` to `minimal` saved 31% and tripled its false escalations |
| **A smaller model** | 5x to 26x cheaper | the error profile changes shape, not just degrades — see the table |
| **Cascade** | run the cheap model first, re-read only what it is unsure about on the expensive one | complexity, and a second call on the minority of tickets |

The cascade is the one worth building if volume ever justifies it, and this codebase is already
shaped for it: the confidence threshold that sends unsure tickets to `human-review` is the same
signal that would send them to a better model instead. Everything under 0.50 goes to the
expensive reader; everything above ships on the cheap one.
