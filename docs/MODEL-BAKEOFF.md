# Model bake-off: what does this job actually need?

`scripts/model_bakeoff.py` · 33 tickets (climb-01, climb-02, climb-03…) · 2026-09-24 19:31

Same prompt, same schema, same guardrails — only the model and its reasoning effort change.
**The columns in bold are the ones that decide it.** A missed escalation disqualifies a model.
An urgency under-call on a critical ticket disqualifies it. Everything else is a trade you can
have a conversation about.

| model | effort | **missed escalations** | **false escalations** | **urgency under-called** | category | p50 | cost / ticket | vs gpt-5 |
|---|---|---|---|---|---|---|---|---|
| `gpt-5-2025-08-07` *(reused)* | low | none | none | none | 100% | 16.1 s | $0.914¢ | 1.00x |
| `gpt-5-mini-2025-08-07` | low | none | **1** (edge-28) | **1** (edge-13) | 100% | 9.9 s | $0.184¢ | 0.20x |
| `gpt-5-mini-2025-08-07` | minimal | none | **3** (edge-21, edge-23, edge-32) | **1** (edge-13) | 100% | 5.5 s | $0.127¢ | 0.14x |
| `gpt-5-nano-2025-08-07` | low | none | **1** (edge-23) | **3** (climb-10, edge-20, edge-27) | 100% | 7.0 s | $0.035¢ | 0.04x |

## Tokens measured per ticket

| model | input | of which cached | output |
|---|---|---|---|
| `gpt-5-2025-08-07` | 2786 | 2607 | 859 |
| `gpt-5-mini-2025-08-07` | 2786 | 2525 | 855 |
| `gpt-5-mini-2025-08-07` | 2786 | 2607 | 581 |
| `gpt-5-nano-2025-08-07` | 2786 | 2525 | 818 |

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

Measured over 33 gold tickets, so a single disagreement moves a percentage column by
about 3 points. Small enough to be directional, not a benchmark.

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
