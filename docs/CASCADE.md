# Does the cascade pay?

`scripts/cascade_eval.py` · 33 gold tickets · triage **draft** · cheap `gpt-5-mini`, expensive `gpt-5` · 2026-09-24 19:56

Read cheap first, then pay for a second opinion where the cheap answer looks dangerous. The
trigger is **stakes plus doubt**, not doubt alone: the bake-off's worst finding was `nano`
under-calling three critical tickets *confidently*, so a confidence-only rule would have
waved exactly the wrong tickets through.

| | cascade | `gpt-5` every ticket |
|---|---|---|
| Missed escalations | none | none |
| False escalations | none | none |
| Urgency under-called | **1** (edge-13) | none |
| A critical read as lower | NO | NO |
| Category accuracy | 100% | 100% |
| Total cost, 33 tickets | $0.3891 | $0.3015 |
| Cost per ticket | 1.179¢ | 0.914¢ |
| **Saving** | **-29%** | — |

## How much of the work stayed cheap

- **19 of 33** tickets (58%) went to the expensive model.
- **14** were handled by the cheap one.
- The second read **changed the answer on 6** of the 19 it looked at.

The last number is the one to watch. If the expensive model almost never disagrees, the
trigger is too wide and the cascade is paying for confirmation it does not need. If it
disagrees often, the draft model is not good enough to ship unreviewed on anything.

### Why this loses money

The naive arithmetic says a draft plus a 58% re-read rate should save about 22%. It does not,
because the tickets the cascade chooses to re-read are *by construction* the hard ones — they
escalate, or they are urgent — and a hard ticket costs nearly double the average on the
expensive model. Measured here: **1.73¢ for a re-read ticket against a 0.91¢ average.** The
draft then becomes pure overhead on the majority of the spend. Adverse selection, and it is
invisible until you price the tickets individually rather than multiplying an average.

## Why the trigger is what it is

| A draft is re-read when | because |
|---|---|
| it escalated | a wrong escalation call is expensive in both directions |
| it said high or critical | the cheap models' worst failure was under-calling critical tickets |
| its category confidence was under 0.50 | the same threshold that sends a ticket to human-review |

Everything else ships on the draft. The rule deliberately re-reads more than a
confidence-only rule would: the saving is smaller and it protects against the failure that
actually hurts.

Prices from `app/pricing.py`.
