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

**Which model and why?** `claude-opus-5`, adaptive thinking, medium effort, structured outputs via
`messages.parse`. Quality on implicit-urgency inference is the point; cost is cents per ticket.
Model and effort are env vars; `scripts/eval.py` reports tokens and p95 so a swap is measurable.

**Prompt injection?** Ticket text is wrapped in `<ticket>` tags and declared as data. `edge-23` is an
injection attempt asserting the ticket still lands in a real queue and is never "resolved."

**Prompt caching?** The system prompt is a stable cached prefix. Opus 5's minimum cacheable prefix
is 512 tokens and the prompt is near that, so the audit record logs `cache_read_input_tokens` to show
whether it actually hits rather than assume.

**How do you know the model isn't hallucinating a customer?** The schema says name is null unless
literally in the text, and the gold set scores "correctly null" on 9 of 10 Climb samples.

## Evaluation

**How did you test it?** 30-row gold set: the 10 Climb tickets plus 20 edge cases I wrote (false-
positive traps, positive exec mention, phishing, IDOR, GDPR, outage, non-English, injection, spam).
Each row lists which fields are ambiguous so scoring doesn't punish defensible alternatives.
Escalation recall is never ambiguous for must-escalate rows.

**What are the numbers?** See `docs/EVAL-rules.md` and `docs/EVAL-llm.md`. `scripts/compare_evals.py`
diffs them row by row.

**What would you do with more time?** Larger gold set from real tickets with two labelers and
inter-rater agreement; a held-out split so prompt tuning can't overfit; a confidence threshold that
routes low-confidence tickets to a human review queue instead of guessing.

## Infrastructure

**How is it deployed?** Container on Cloud Run via Terraform: Artifact Registry, Secret Manager for
the key, a service account scoped to read that one secret, health probes on `/health`. Not applied
from my machine (no gcloud/terraform installed); stated in the README.

**How does it scale?** Cloud SQL behind the same `audit.py` interface once there is more than one
instance; Pub/Sub or Cloud Tasks in front of intake so it's async and retried; Message Batches API for
backfills. Batch concurrency is a 4-thread pool today.

**Audit?** Every decision is a SQLite row plus a JSON log line. The record includes the model's raw
answer, the final answer, rules fired with matched text, overrides, token usage, latency, and the
mode. "Why did this route here" is answerable after the fact from the record alone.

**Security of the service itself?** Demo tier is public. Real traffic gets IAP or an API gateway in
front, a tenant column on the audit table from the auth context, and the key stays in Secret Manager.
