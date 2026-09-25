# How it works — presentation notes

A reference to read before presenting and to glance at if a question lands. Each section is written
as the answer, not as a description.

---

## "Is it deterministic, or a model, or both?"

**Both, and the split is the design.** Every field has an owner, and the two kinds of component are
doing different jobs:

- **The model reads.** It handles the parts where judgment is required and a word list fails —
  inferring urgency from scope and recurrence, telling a spam email from a real one, working out who
  is writing when nobody says.
- **Deterministic code decides the things that must not be probabilistic.** Escalation floors,
  routing, idempotency, and the audit trail are all ordinary Python and YAML.

The one-line version: *the model produces a reading, deterministic rules produce the decision.*

### Who produces each field

| Field | Produced by | Can deterministic code override it? | Where |
|---|---|---|---|
| `customer.name` | model, verbatim only | no | `app/llm.py` |
| `customer.best_guess` / `confidence` / `basis` | model (or the keyword fallback) | no | `app/llm.py`, `app/rules.py` |
| `category` + `category_confidence` | model | no | `app/llm.py` |
| `urgency` | model | **yes — can only be raised** | `app/rules.py` |
| `escalate` + `escalation_reasons` | model | **yes — can only be raised** | `app/rules.py` |
| every `*_reason` text | model | no | `app/llm.py` |
| `queue` / `escalation_queue` | **pure lookup, no model** | n/a | `app/routing.yaml` |
| audit record, idempotency | **pure code** | n/a | `app/audit.py` |

The asymmetry in that third column is the whole safety argument. Rules may raise an escalation or
lift an urgency; there is no code path that lowers either. A missed escalation is the one failure the
brief calls unacceptable, so recall does not depend on a probabilistic component alone.

---

## "Who gives the confidence score?"

**It depends which of the two modes produced the ticket, and the UI always says which.**

### Are these probabilities?

**No.** They are the model's own stated confidence, self-reported and not validated against outcomes.
They are useful for ordering tickets and for the 0.50 routing threshold, and they are stable — the
same ticket scored five times moves by about ±0.03. They are not calibrated probabilities, and
calling them that would be a claim I have not earned. Turning them into probabilities means binning
predictions by score and measuring accuracy per bin against labelled data; with 31 gold rows that
curve would be noise.

Category confidence is framed as a **share of opinion**: if ten support leads read this ticket, how
many file it where the system did. The remainder is reported in `category_alternatives`, each with a
clause saying what argues for it and what rules it out — which is also what keeps the primary honest,
since a model forced to name the runner-up cannot price it at zero for free.

### Is a split better than one number?

Asked directly: should the category carry one confidence score, or a split across the categories
that were in contention?

**The split, and not because it looks more sophisticated.** Three reasons, in order of how much they
matter:

1. **It makes the primary number honest.** A model asked only "how confident are you" can answer 0.9
   for free. A model that must also name the runner-up and give it a share has to actually consider
   the alternative before pricing it. That change alone moved an ambiguous ticket from 0.92 to 0.67
   — see `DECISIONS.md` D34 and D37.
2. **It is more actionable for a person.** "Bug 0.6" tells a reader to be careful. "Bug 60%, Billing
   40%" tells them *what to be careful about*, and which queue it might belong in instead.
3. **It costs almost nothing.** Two extra short fields on a call that is already being made.

**What it is not: a probability distribution.** The shares sum to about 1.0 and look like one, which
is precisely the risk. They are the model's self-reported opinion, never validated against outcomes.
Calling them probabilities would claim calibration this system has not earned. The UI labels them as
a share — *if ten support leads filed this ticket, roughly this is how they would split* — because
that is a claim the number can actually support.

**When one number would be enough:** if nothing downstream branched on the runner-up and no human
ever read it. Here a human does read it, and `human-review` branches on the primary falling below
0.50, so the shape of the uncertainty is worth knowing.

### Model mode (`mode: llm`) — the score is the model's, guided by an explicit ladder

The number is the model's own self-assessment. It is not calibrated post-hoc and it is not computed
by us. What we control is the instruction, which pins the scale so the number means the same thing
from ticket to ticket. Verbatim from the system prompt:

```
1.0        the company is named in the text
0.75-0.9   a company email domain, or an account id that identifies them
0.4-0.7    strong contextual signal — scale, plan, product surface, industry, named role
0.1-0.3    weak — only that they are an existing customer of some kind
0.0        genuinely nothing; leave best_guess null
```

**And we test that it obeys it.** `data/gold.jsonl` carries expected confidence bands, scored
asymmetrically in `tests/gold.py`:

- **The ceiling is a safety check, enforced in every mode.** The system must never claim more
  certainty than the text supports. The scorecard reports overclaiming on its own line and it must
  read `none`.
- **The floor is a quality check, enforced only on the model path**, because the keyword fallback
  genuinely cannot read "I'm a security researcher" and reporting 0.00 there is correct.

Current scorecards: 100% calibration in both modes, no overclaiming.

### Keyword mode (`mode: rules`) — the score is a hardcoded constant

No model is involved. `app/rules.py` assigns fixed numbers by which cue matched:

| Cue | Score |
|---|---|
| a company name matched by the regex | 1.00 |
| a non-free work email domain | 0.80 |
| stated scale ("140 of our analysts") | 0.50 |
| enterprise product language, or a named plan | 0.45 |
| a personal email domain, or only an account reference | 0.30 |
| nothing matched | 0.00 |

This path runs when there is no API key, or when the model call fails or times out. The badge in the
header and the `mode` field in every audit record say which one produced the ticket.

---

## "What about the checklist in the popup — is that computed?"

Partly, and it is labelled so. In the "Who sent it" panel, a **filled dot marks a fact the code can
verify** — a company name is present, or confidence is 0.00. The middle rungs of the ladder are the
model's own judgment, so rather than regex-guessing which rung it used, the panel shows **the
evidence it actually cited** in `basis`. The explanatory line under the list says exactly this.

This matters because the alternative — pattern-matching the model's prose to tick boxes — would look
more rigorous and mean less. If asked, the honest answer is: *the ladder is the instruction we gave
it; the basis is what it reported back; we only tick what we can independently check.*

---

## "What runs in what order?"

```
POST /tickets
  │
  ├─ 1. idempotency fast-path        deterministic   (source, external_id) already decided?
  ├─ 2. mode selection               deterministic   key present → model, else keyword rules
  ├─ 3. extraction                   MODEL           one structured-output call, 30s deadline
  │                                                  on error/timeout/refusal → fall through to rules
  ├─ 4. guardrail layer              deterministic   regex over the RAW text, may only raise
  ├─ 5. routing                      deterministic   category + urgency → YAML lookup
  └─ 6. audit                        deterministic   SQLite row + JSON log line, unique index
```

Step 4 runs against the original ticket text, not the model's output. That is deliberate: if the
model misread the ticket, the guardrail still sees what the customer actually wrote.

---

## Questions you should expect

**"Why not do it all with the model?"** Because escalation recall is a safety property and a model
call is probabilistic, can be refused, and can time out. `tests/test_gold_rules_mode.py` proves the
deterministic layer alone catches 100% of must-escalate tickets with no network.

**"Why not do it all with rules?"** Because urgency is never stated. Ticket 10 describes a checkout
bug double-charging many customers with no alarm words in it. On urgency the keyword layer scores 76%
exact against the model's 82%, and 82% strict on category against the model's 100%. Neither
under-calls. The sharper answer is the adversarial set: rules alone miss three escalations out of
twelve there, and the model misses none.

**"So the model can be wrong and you'd still ship it?"** It can be wrong and we ship a *corrected*
answer. `tests/test_llm_path_mocked.py` mocks a model that calls a legal threat "billing, no
escalation" and asserts the shipped decision is escalated and high urgency, with the override
recorded. The audit keeps both answers.

**"What if two rules disagree?"** They compose, and the summary reports the net effect rather than
the churn. A spam email containing "GDPR-compliant" trips the compliance rule and is then undone by
the spam rule; the panel says "rules fired, then cancelled out" and still shows the full sequence.

**"How do you know the confidence number means anything?"** It is scored against expected bands in
the gold set, with overclaiming reported separately as a safety line. When I first wrote those bands
two "failures" turned out to be my spec error, not the model's — that is written up in `DECISIONS.md`
D29.

**"Is the score used for anything, or is it decoration?"** It is used. Category confidence below 0.50
on a non-escalated ticket routes to `human-review` instead of a guessed team queue. Sender confidence
is currently surfaced rather than gated on, because in production that field would come from the
authenticated sender and this inference becomes the cross-check.

**"What would you change with more time?"** A larger gold set drawn from real tickets with two
labellers and inter-rater agreement; a held-out split so prompt tuning cannot overfit; and
asynchronous intake, which the latency measurement in `LOADTEST.md` turned from a preference into a
requirement.

---

## Numbers worth having memorised

| | keyword rules only | model + rules |
|---|---|---|
| Escalation recall | 100% | 100% |
| False escalations | none | none |
| Category accuracy | 100% | 100% |
| Urgency exact / within tolerance | 76% / 97% | 82% / 100% |
| Sender-confidence calibration | 100% | 100% |
| Overclaimed sender confidence | none | none |
| p50 latency per ticket | under 5 ms | 16.1 s |

**These are a single run, not an average.** Escalation recall, category accuracy and the confidence
checks have been stable across every run. Urgency exact has moved between 77% and 83% run to run, on
tickets where gold pins one level and the model picks the neighbouring one — `climb-06`, a calmly
worded double-billing refund, is the usual mover. Re-run `scripts/eval.py` to see the current figure
rather than quoting one from memory.

33 gold tickets: the 10 provided, plus 23 edge cases written to trap the failure modes — false
positives like "send this invoice to our legal department", a positive executive mention, a prompt
injection, a password reset that looks security-adjacent but isn't.

Full tables in `EVAL-llm.md` and `EVAL-rules.md`, regenerated by `scripts/eval.py`.
`scripts/preflight.sh` fails if the numbers quoted here drift from the last eval run.
