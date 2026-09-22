# Climb Intake — ticket extraction & routing

An intake service that reads messy, freeform customer requests and decides what to do with them.
For each ticket it extracts **customer, category, urgency, and an escalation flag**, routes it to a
simulated downstream queue, flags anything that needs a human (security, legal/contract, executive
mentions), and logs the full decision with its reasoning for audit.

```
ticket text ──▶ Claude (structured output) ──▶ guardrail rules ──▶ routing table ──▶ queue(s)
                        │                            │                                  │
                        └── rationale ───────────────┴── rules fired / overrides ───────┴──▶ audit log (SQLite + JSON log line)
```

Two layers on purpose. The model infers what regexes can't (urgency from scope, tone, recurrence).
The rules layer runs on the raw text afterwards and can only **raise** escalation or **lift** urgency,
never lower. Missed escalations are the one failure the assignment calls unacceptable, so recall does
not depend on a probabilistic component alone. See [docs/DECISIONS.md](docs/DECISIONS.md).

## Run it locally

```bash
cp .env.example .env          # paste your ANTHROPIC_API_KEY; leave blank for rules-only mode
uv venv && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8080
open http://localhost:8080
```

With Docker:

```bash
docker compose up --build      # http://localhost:8080
```

The image installs from the committed `requirements.lock` rather than resolving version ranges, so
two builds weeks apart produce the same image, and it runs as a non-root user with the audit
database on a named volume.

<details><summary>If you're on Apple silicon without Docker Desktop</summary>

`brew install docker` may hit a Tier 3 configuration with no bottle and try to compile the CLI from
source. Take the static binary instead, and give Colima explicit DNS or registry pulls will stall:

```bash
brew install colima docker-compose
VER=$(curl -s https://download.docker.com/mac/static/stable/aarch64/ \
      | grep -oE 'docker-2[0-9]\.[0-9.]+\.tgz' | sort -V | tail -1)
curl -fsSL "https://download.docker.com/mac/static/stable/aarch64/$VER" | tar xz
install -m 0755 docker/docker ~/.local/bin/docker
colima start --cpu 2 --memory 4 --disk 20 --dns 1.1.1.1 --dns 8.8.8.8
```
</details>

Either an Anthropic or an OpenAI key works (`LLM_PROVIDER=auto` prefers Anthropic; the prompt,
schema, rules, and audit are provider-neutral, only the transport differs). Without any key the
service runs in **rules-only** mode and says so on `/health` and in the UI
header. Every endpoint still works; category and urgency are keyword heuristics instead of model
inference.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/tickets` | Classify one ticket. Body `{"text": "...", "source"?: "...", "external_id"?: "..."}` |
| `POST` | `/tickets/batch` | `{"tickets": [ {...}, ... ]}` |
| `POST` | `/tickets/upload` | Multipart file: `.json` (array of strings or objects), `.jsonl`, `.csv` (`text` column, optional `id`), or `.txt` (blank-line separated) |
| `POST` | `/tickets/load-samples?fixture=samples\|demo` | Ingest the 10 Climb samples, or a 32-ticket demo set spanning every category and escalation reason |
| `GET` | `/tickets` | Recent decisions, optional `?queue=` filter |
| `GET` | `/tickets/{id}` | Full decision: final fields, model's raw output, rules fired, overrides, usage |
| `GET` | `/tickets/{id}/explain` | Same decision as plain text |
| `GET` | `/queues` | Queue names, counts, and total distinct decisions |
| `GET` | `/health` | Mode (`llm` / `rules`) and model |
| `DELETE` | `/tickets` | Clear the audit log (demo convenience) |

The web view supports per-decision deep links: `http://localhost:8080/?t=<decision id>` opens
straight to that ticket's explanation, so a routing decision can be linked in a Slack thread or a
ticket comment. Interactive docs at `/docs`. Tickets with an `external_id` are idempotent on `(source, external_id)`:
a retry returns the original decision.

```bash
curl -s localhost:8080/tickets -H 'content-type: application/json' \
  -d '{"text":"Our CEO is asking why onboarding still is not done. Need progress today."}' | jq .
```

## Decision schema

```jsonc
{
  "id": "…", "created_at": "…", "mode": "llm | rules | llm_fallback_rules", "model": "claude-opus-5",
  "extraction": {
    "customer": {"name": null, "contact_name": null, "identifiers": ["invoice #88213"]},
    "category": "billing | bug | security | legal_contract | onboarding | feature_request | spam | other",
    "category_confidence": 0.92,
    "urgency": "low | medium | high | critical",
    "urgency_signals": ["due Friday"],
    "escalate": true,
    "escalation_reasons": ["security_incident | data_exposure | legal_threat | compliance_request | executive_mention"],
    "summary": "…", "rationale": "…"
  },
  "llm_extraction": { /* the model's answer before rule overrides, for audit */ },
  "rule_hits": [{"rule": "legal.threat", "matched": "legal team", "effect": "escalate: false -> true"}],
  "overrides": ["legal.threat forced escalate=true (matched 'legal team')"],
  "queue": "legal-and-account-management", "escalation_queue": "human-escalation-desk",
  "latency_ms": 1840, "usage": {"input_tokens": 1210, "output_tokens": 190}
}
```

## Routing

[app/routing.yaml](app/routing.yaml) maps category to queue with per-urgency overrides (critical bugs
go to `engineering-oncall`). Escalated tickets are additionally copied to `human-escalation-desk`.
Non-escalated tickets with category confidence below 0.5 go to `human-review` instead of a guessed
team queue.

## Evaluation

The gold set ([data/gold.jsonl](data/gold.jsonl)) is the 10 Climb samples plus 20 authored edge
cases: false-positive traps, positive executive mentions, phishing, IDOR disclosure, GDPR, outages,
non-English, prompt injection, vendor spam. Rows list which fields are `ambiguous` so scoring doesn't
punish defensible alternatives. Escalation recall is never ambiguous for must-escalate rows.

```bash
uv run pytest                                   # unit + API + rules-mode gold (no network)
CLASSIFIER_MODE=rules uv run python scripts/eval.py   # scorecard -> docs/EVAL-rules.md
uv run python scripts/eval.py                   # with a key: scorecard -> docs/EVAL-llm.md
TEST_CLASSIFIER_MODE=llm uv run pytest tests/test_gold_llm_mode.py -s
```

Measured on the gold set (gpt-5 vs the rules-only fallback):

| | keyword rules only | model + rules |
|---|---|---|
| Escalation recall | 100% | 100% |
| False escalations | 0 | 0 |
| Category accuracy | 100% | 100% |
| Urgency exact / tolerant | 77% / 97% | 77% / 100% |
| Sender-confidence calibration | 100% | 100% |
| Overclaimed sender confidence | none | none |
| p50 latency per ticket | ~0 ms | 17.6 s |

Full scorecards in [docs/EVAL-llm.md](docs/EVAL-llm.md) and [docs/EVAL-rules.md](docs/EVAL-rules.md),
including every model rationale. `scripts/compare_evals.py` diffs two runs row by row.
`scripts/loadtest.py` measures the intake path under concurrent writes; results and the SQLite WAL
change they motivated are in [docs/LOADTEST.md](docs/LOADTEST.md). The rules-only layer alone scores 100% escalation recall with zero
false escalations on the gold set; that is the safety-net claim and it is tested in CI.

## Audit log

Every decision is written to SQLite (`AUDIT_DB_PATH`) and emitted as a single JSON line on stdout
(`{"event": "routing_decision", ...}`) so a cloud log sink ingests it with no extra plumbing. The
record keeps the model's raw output, the final output, every rule that fired with the matched text,
token usage, and latency.

## Deploy plan (GCP Cloud Run)

Infrastructure is in [infra/terraform](infra/terraform). It stands up:

1. Artifact Registry repo for the image
2. Secret Manager secret holding `ANTHROPIC_API_KEY`
3. Cloud Run v2 service (1 vCPU, 512 MiB, min 0 / max 3 instances, health check on `/health`)
   with the secret injected as an env var and a service account scoped to read that one secret
4. Public invoker binding (demo only; put IAP or an API gateway in front for real traffic)

```bash
gcloud auth login && gcloud config set project $PROJECT
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/$PROJECT/climb-intake/intake:v1 . && docker push $_
cd infra/terraform
terraform init
terraform apply -var project_id=$PROJECT -var image=us-central1-docker.pkg.dev/$PROJECT/climb-intake/intake:v1 -var anthropic_api_key=$ANTHROPIC_API_KEY
terraform output url
```

Honest status: the Terraform is written against the current `google` provider resources but has
**not been applied** from this machine (no gcloud/terraform installed here). Expect to iterate on
`terraform plan` once.

Scale path, in order: Cloud SQL (Postgres) behind the same `audit.py` interface once there is more than
one instance; Cloud Tasks or Pub/Sub in front of `/tickets` so intake is async and retried; the
Message Batches API for backfills. AWS equivalent is App Runner + Secrets Manager + ECR with the same
three resources.

## Presenting this

[docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) answers the architecture questions directly — which
fields the model produces, which are deterministic, who assigns the confidence score in each mode,
and what runs in what order. [docs/DEMO.md](docs/DEMO.md) is a three-minute live walkthrough.
[docs/DECISIONS.md](docs/DECISIONS.md) is the running log of every non-obvious choice.

## Interface notes

The web view is one list of decisions. Click any ticket to open the full breakdown in a dialog:
the request as it arrived, the four extracted fields with the evidence behind each, the queue it was
routed to, the reasoning, and whether any guardrail rule changed the answer. Arrow keys step between
tickets without closing it, and every decision is linkable at `/?t=<decision id>`.

Sort by most recent, most urgent, longest or quickest to read, or category; filter to the tickets that
need a human. Each row shows how long that ticket took to classify, which makes the model-vs-rules
latency difference visible without reading the eval. Colours come from climb.ai's published CSS
tokens; the typefaces there are licensed, so this uses a system stack.

## Layout

```
app/
  main.py        FastAPI routes + static UI
  pipeline.py    mode selection -> extraction -> rules -> routing -> audit
  llm.py         Claude structured-output call + system prompt
  rules.py       escalation guardrails + rules-only fallback classifier
  routing.py/.yaml
  audit.py       SQLite + JSON log line
  models.py      Pydantic schemas
  static/index.html
data/            sample_tickets.json, gold.jsonl
tests/           unit, API, gold (rules mode, and llm mode when a key is present)
scripts/eval.py  scorecard generator
docs/            DECISIONS.md, EVAL-*.md
infra/terraform  Cloud Run deploy
```
