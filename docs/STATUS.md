# Where this is, and what is left

Updated 2026-09-22. `./scripts/preflight.sh` is the live version of the top half of this page.

## Done and verified

| | Evidence |
|---|---|
| All 10 Climb samples classify correctly | The 6 design-note cases are asserted by ticket number in preflight |
| Extract customer, category, urgency, escalation | Plus a scored sender inference and per-field reasoning |
| Route to simulated downstream queues | 12 queues, YAML table, visible on the **Queue board** |
| Escalation with low tolerance for misses | 100% recall in **both** modes, zero false escalations, 33 gold tickets |
| View showing how and why | Web app, `/tickets/{id}`, `/tickets/{id}/explain`, per-field pop-outs |
| Audit every decision with its reasoning | SQLite + JSON log lines; keeps model output *and* shipped output |
| Containerized, runs locally | Built, run, health green, non-root, audit survives restart |
| IaC | Terraform for Cloud Run, `tofu validate` passes |
| README with a deploy plan | Including the Apple-silicon install path that actually works |
| 47 tests | Unit, API, mocked model path, gold in keyword mode, concurrency |
| Cost/performance across models | `docs/MODEL-BAKEOFF.md` — nano matches gpt-5 at 6% of the cost |
| Repeatability | `docs/REPEATABILITY.md` — labels stable, confidence ±0.03 |
| Presenter material | `/notes` (15/30 min), `DEMO.md`, `HOW-IT-WORKS.md`, `PANEL-QA.md`, 36 decisions |

## Done but NOT verified live

- ~~**Multi-class category confidence**~~ — now measured. It works: the score separates an ambiguous
  ticket (0.67) from an obvious one (0.98), which the old prompt did not. It also doubled run-to-run
  variance. Both numbers are in `REPEATABILITY.md`; quote both.
- **Terraform.** Validates against the real provider schema, never applied. Say this before they ask.

## Blocked on you

1. **Push to a GitHub remote.** The only unmet deliverable. `git remote add origin … && git push -u origin main`.
2. **Revoke both API keys after the interview.** The Anthropic and OpenAI keys both appeared in a chat transcript.

## Worth doing next, in order

1. **Run the bake-off over all 33 gold tickets, not 10.** Ten tickets means one disagreement moves a
   column by ten points. About 90 calls.
2. **Split the gold set.** It has been used to tune prompts, so its numbers are optimistic. Reporting
   only an untouched half would be the honest version. Costs nothing but a re-run.
3. **Decide the production model.** Bake-off and repeatability disagree: nano matches gpt-5 on
   accuracy at 6% of the cost, but flips a label on repeat. Probably nano plus the review queue.

## Deliberately not doing

- **Async intake.** Measured and argued for (D24, `LOADTEST.md`) but out of scope for a take-home;
  describing the measurement is stronger than a half-built worker.
- **Cloud SQL, IAP, a real job queue.** Named as the scale path with the reason and the ordering.
- **More sample tickets.** 31 gold + 32 demo already covers every category, urgency and escalation
  reason, plus the traps. More would pad the number without adding coverage.
