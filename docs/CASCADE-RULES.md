# Does the cascade pay? — triaging with the keyword layer

`scripts/cascade_eval.py` · 33 gold tickets · triage **rules** · cheap `gpt-5-mini`, expensive `gpt-5` · 2026-09-24 19:56

Triage before spending anything. The keyword layer has already read every ticket for free,
so it decides which reader each one needs: a ticket that trips an escalation pattern, or that
reads as high urgency on keywords alone, goes to the expensive model. Everything else goes to
the cheap one. **One model call either way** — there is no draft to pay for.

| | cascade | `gpt-5` every ticket |
|---|---|---|
| Missed escalations | none | none |
| False escalations | **1** (edge-28) | none |
| Urgency under-called | **1** (edge-13) | none |
| A critical read as lower | NO | NO |
| Category accuracy | 100% | 100% |
| Total cost, 33 tickets | $0.1871 | $0.3015 |
| Cost per ticket | 0.567¢ | 0.914¢ |
| **Saving** | **38%** | — |

## How much of the work stayed cheap

- **17 of 33** tickets (52%) went to the expensive model.
- **16** were handled by the cheap one.

The cheap model's error profile comes with it on the half it handles: on this set that is one
false escalation (the SOC 2 document request) and one urgency disagreement, low versus medium.
No escalation was missed and no critical ticket was under-called — the two failures that
would rule the arrangement out.

## Why the trigger is what it is

| A ticket gets the expensive reader when | because |
|---|---|
| a keyword escalation pattern matched | these are the security, legal and executive tickets |
| keyword urgency read high or critical | the cheap models' worst failure was under-calling critical tickets |

The triage costs nothing: the same regexes run on every ticket anyway, as the guardrail layer.
Using them to choose a reader is the only free lever in the system.

Prices from `app/pricing.py`.
