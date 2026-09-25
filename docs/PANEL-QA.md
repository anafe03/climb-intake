# Panel Q&A prep

Likely questions, with answers grounded in the code. Keep answers to three sentences and point at
a file or a number. Cross-reference [DECISIONS.md](DECISIONS.md) for the longer reasoning.

## Architecture

**Walk me through what happens when a ticket comes in.**
`POST /tickets` → `pipeline.process`. If a key is present, one Claude call with a Pydantic schema
returns customer, category, urgency, escalation, and a rationale. Then `rules.apply_escalation_rules`
runs regexes over the raw text and can only add escalation reasons or lift urgency. `routing.route`
maps category + urgency to a queue from YAML. The decision, including the model's pre-override
answer and every rule hit, is written to SQLite and emitted as a JSON log line.

**Why not just let the model decide escalation?**
Because a missed escalation is the one failure the brief calls unacceptable, and a model call is
probabilistic, can be refused, can time out. Recall is a safety property so it gets a deterministic
floor. `tests/test_gold_rules_mode.py` proves the floor alone catches 100% of must-escalate gold rows.

**Why not just rules?**
Rules can't infer urgency. Ticket 10 (checkout double-charging many customers) has no alarm words;
severity comes from scope + money + recurrence + ongoing. The gold set has a terse rewrite of it
(`edge-27`) to show the same inference without the numbers.

**What happens when the model gets it wrong?**
Rules override upward and the audit record keeps both answers. `tests/test_llm_path_mocked.py::
test_model_misses_legal_threat_rules_catch_it` mocks a model that says "billing, no escalation" for a
legal threat and asserts the shipped decision is escalated, high urgency, with the override listed.

**What happens when Anthropic is down?**
Mode flips to `llm_fallback_rules`, the ticket still routes, the error string is in the audit record,
`/health` and the UI badge show degraded mode. Tested with a mocked `APIConnectionError` and a mocked
refusal.

**Why is escalation separate from urgency?**
Escalation is topic (security, legal, exec) meaning "a human must see this." Urgency is speed. A CEO
thank-you escalates at low urgency. A full outage is critical but routes to on-call, not the
escalation desk. Executive mentions floor urgency at medium, not high, for this reason.

## Model choices

**Which model and why?** `gpt-5` at **low** reasoning effort, structured outputs via
`responses.parse`. Anthropic is supported on the same interface and either key works. Low effort
roughly halved output tokens and cost with no loss on the gold set (D55). The full answer — every
model scored and priced together, and why `gpt-5-nano` is disqualified at 26x cheaper — is on the
`/optimization` page. Model, provider and effort are all env vars, and a swap is measurable in one
command: `scripts/model_bakeoff.py`.

**Prompt injection?** Ticket text is wrapped in `<ticket>` tags and declared as data. `edge-23` is an
injection attempt asserting the ticket still lands in a real queue and is never "resolved."

**Prompt caching?** The system prompt is a stable cached prefix, and the audit record logs
`cache_read_input_tokens` so the hit rate is measured rather than assumed. Measured: **~90% of input
tokens are cache reads**, at a tenth of the price. It is the cheapest of the four cost levers and
the only free one.

**How do you know the model isn't hallucinating a customer?** The schema says name is null unless
literally in the text, and the gold set scores "correctly null" on 9 of 10 Climb samples.

**How would support actually use the "why" view?** Every decision has a shareable URL
(`/?t=<id>`), and the same content is available as JSON (`/tickets/{id}`) and as plain text
(`/tickets/{id}/explain`) for anyone who would rather curl it than click.

## Evaluation

**How did you test it?** 33-row gold set: the 10 Climb tickets plus 23 edge cases I wrote (false-
positive traps, positive exec mention, phishing, IDOR, GDPR, outage, non-English, injection, spam).
It splits 11 must-escalate / 22 must-not, and the must-not half is where a false positive would show.
Each row lists which fields are ambiguous so scoring doesn't punish defensible alternatives: 20 rows
are marked ambiguous on urgency, 8 on category, 5 on escalate. Escalation recall is never ambiguous
for must-escalate rows.

**What are the numbers?** Both modes hit 100% escalation recall with zero false escalations on the
33-row gold set. The model wins on urgency (88% exact vs 76%) and on category (97% strict vs 82%).
**Neither mode ever under-calls urgency** — every miss is in the safe direction, and no critical
ticket was ever read as less. It costs 0.9¢ and about 16 s per ticket against microseconds and
nothing. Full tables in `docs/EVAL-llm.md` and `docs/EVAL-rules.md`.

**100% sounds too good.** It is, and the honest move is to go looking rather than quote it.
`docs/STRESS-llm.md` is twelve tickets written to break it. Still no missed escalations — but four
over-escalations, all of the same shape: the vocabulary of an incident without the incident. A
*denied* breach, a *hypothetical* vulnerability, someone else's lawyer, "a total breach of trust".
The best one to show is `adv-01`, where the model was right and the keyword guardrail overrode it.

**Where is the model worse than your regexes?** Nowhere on the gold set — but on the demo set it
escalated a pipeline failure as an executive mention off the phrase "board readout Thursday", with no
rule involved. The model is the more liberal escalator, not the guardrail. Worth knowing which
component to tune if false positives ever became the problem.

**What would you do with more time?** Larger gold set from real tickets with two labelers and
inter-rater agreement; a held-out split so prompt tuning can't overfit; a confidence threshold that
routes low-confidence tickets to a human review queue instead of guessing.

## Infrastructure

**How is it deployed?** Container on Cloud Run via Terraform: Artifact Registry, Secret Manager for
the key, a service account scoped to read that one secret, health probes on `/health`. Not applied
from my machine (no gcloud/terraform installed); stated in the README.

**How slow is the model, really?** p50 about 12 s, but the tail runs past 40 s — and I checked whether
that was rate limiting by running the same tickets at concurrency 1, 4 and 8. At concurrency 1, with
nothing to rate limit, a ticket still took 41 s. The tail is the model. That is why intake should be
asynchronous, and why the per-attempt deadline is bounded with a fallback. `docs/LOADTEST.md`.

**How does it scale?** Cloud SQL behind the same `audit.py` interface once there is more than one
instance; Pub/Sub or Cloud Tasks in front of intake so it's async and retried; Message Batches API for
backfills. Batch concurrency is a 4-thread pool today.

**Does the audit log hold up under load?** Measured: 0 errors and exactly-once rows at 16 and 32
concurrent writers in rules mode; WAL mode cut p99 from 455 ms to 165 ms. `docs/LOADTEST.md`. SQLite
is single-writer, and the test says that ceiling is hundreds of rps on one box.

**What if the upstream system retries?** Idempotent on `(source, external_id)`: the retry gets the
original decision back, no duplicate in any queue.

**What about tickets the classifier isn't sure of?** Below 0.5 confidence and not escalated, they go
to a `human-review` queue rather than a guessed team. That's also the labeling stream for growing the
gold set.

**Audit?** Every decision is a SQLite row plus a JSON log line. The record includes the model's raw
answer, the final answer, rules fired with matched text, overrides, token usage, latency, and the
mode. "Why did this route here" is answerable after the fact from the record alone.

**Security of the service itself?** Demo tier is public. Real traffic gets IAP or an API gateway in
front, a tenant column on the audit table from the auth context, and the key stays in Secret Manager.
