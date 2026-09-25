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
| 62 tests | Unit, API, mocked model path, gold in keyword mode, concurrency, pricing, replay |
| Cost/performance across models | `/optimization` and `docs/MODEL-BAKEOFF.md` — nano is 26x cheaper and **disqualified**: it read three critical tickets as high |
| Where it breaks | `docs/STRESS-llm.md` — 12 adversarial tickets. No missed escalations; four over-escalations, all where incident vocabulary appears without an incident |
| Repeatability | `docs/REPEATABILITY.md` — labels stable, confidence ±0.03 |
| Presenter material | `/notes` (14 beats, 15/30 min), `/optimization`, `DEMO.md`, `HOW-IT-WORKS.md`, `PANEL-QA.md`, 96 decisions |

## Done but NOT verified live

- ~~**Multi-class category confidence**~~ — now measured. It works: the score separates an ambiguous
  ticket (0.67) from an obvious one (0.98), which the old prompt did not. It also doubled run-to-run
  variance. Both numbers are in `REPEATABILITY.md`; quote both.
- **Terraform.** Validates against the real provider schema, never applied. Say this before they ask.

## Blocked on you

1. **Push to a GitHub remote.** The only unmet deliverable. `git remote add origin … && git push -u origin main`.
2. **Revoke both API keys after the interview.** The Anthropic and OpenAI keys both appeared in a chat transcript.

## Worth doing next, in order

1. ~~Verify `low` reasoning effort does not cost recall~~ — **done, D55.** 100% recall, no false
   escalations, output tokens halved from ~1,500 to 863.
2. **Run the bake-off over all 33 gold tickets, not 10.** Ten tickets means one disagreement moves a
   column by ten points. About 90 calls.
3. **Split the gold set.** It has been used to tune prompts, so its numbers are optimistic. Reporting
   only an untouched half would be the honest version. Costs nothing but a re-run.
4. ~~**Decide the production model.**~~ **Decided: `gpt-5` at low effort.** The full-gold-set
   bake-off (D81) retired the earlier "nano is as good" reading, which came from 10 tickets with no
   false-positive traps. Nano reads three critical tickets as high. Mini is the credible cheap
   option at a fifth of the cost and one false escalation; the keyword-triaged cascade is 38%
   cheaper and ships off by default. All of it is on `/optimization`.

## Deliberately not doing

- **Async intake.** Measured and argued for (D24, `LOADTEST.md`) but out of scope for a take-home;
  describing the measurement is stronger than a half-built worker.
- **Cloud SQL, IAP, a real job queue.** Named as the scale path with the reason and the ordering.
- **More sample tickets.** 33 gold + 32 demo + 12 adversarial + 6 keyword-free already cover every
  category, urgency and escalation reason, plus the traps. More of the same would pad the number
  without adding coverage. More tickets *I did not write* would be worth real money — see below.
