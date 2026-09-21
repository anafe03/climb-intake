# Load test: intake path under concurrent writes

Question: does the single-container design (FastAPI + SQLite audit log) hold up when many tickets
arrive at once, and does every accepted ticket land in the audit log exactly once?

Method: `scripts/loadtest.py` fires N `POST /tickets` in parallel from a thread pool against the
running server in **rules mode**, so the numbers measure the service and the audit write, not model
latency. Row counts are checked before/after via `/queues.total`. Local machine, 2026-09-21.

## Before: default SQLite journal, schema DDL on every connection

| n | concurrency | rps | p50 | p95 | p99 | max | errors | rows |
|---|---|---|---|---|---|---|---|---|
| 300 | 16 | 550 | 6.0 ms | 99.7 ms | 455 ms | 488 ms | 0 | exact |

No errors, because sqlite3's default 5 s lock timeout absorbs contention. But the p99 is 75x the
p50: writers queue on the rollback-journal lock and each connection also re-ran the `CREATE TABLE IF
NOT EXISTS` script.

## After: WAL journal, `synchronous=NORMAL`, 10 s busy timeout, schema DDL once per process

| n | concurrency | rps | p50 | p95 | p99 | max | errors | rows |
|---|---|---|---|---|---|---|---|---|
| 300 | 16 | 809 | 5.2 ms | 66.6 ms | 165 ms | 262 ms | 0 | exact |
| 600 | 32 | 604 | 43.8 ms | 99.3 ms | 149 ms | 189 ms | 0 | exact |

p99 down ~2.8x at the same load. At 32 concurrent writers the median rises (one writer at a time is
SQLite's ceiling) but the tail stays flat, which is the property that matters for an intake endpoint.

## What this does and doesn't show

- The audit write is exactly-once under concurrency: `rows == accepted requests` in every run.
- In LLM mode the bottleneck moves to the model call (seconds, not ms) and to Anthropic rate limits;
  the batch endpoint's 4-thread pool is sized for that, not for this.
- SQLite is a single-writer store. The scale path is Cloud SQL behind the same `audit.py` interface,
  and an async queue (Pub/Sub or Cloud Tasks) in front of intake so bursts are absorbed and retried.
  This test tells us when that's needed: not at hundreds of tickets per second on one box.

Reproduce:

```bash
uv run uvicorn app.main:app --port 8080     # rules mode: leave ANTHROPIC_API_KEY blank
curl -X DELETE localhost:8080/tickets
uv run python scripts/loadtest.py --n 300 --c 16
```
