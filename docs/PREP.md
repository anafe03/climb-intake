# Prep checklist for a 15-minute presentation

Work down this list. It is ordered so that each step makes the next one shorter. Total reading is
about 45 minutes; the rehearsal is 30.

---

## 1 · Get the machine into demo state (5 min)

- [ ] Credits are on the OpenAI account. Everything below assumes the model is reachable.
- [ ] **`colima restart` if the VM has been up more than a day.** Its network degrades with uptime and
      the symptom is tickets silently falling back to keyword rules (D53). Preflight warns about this.
- [ ] `docker compose up -d` and then `./scripts/preflight.sh`
- [ ] Everything reads PASS except **git remote**. If anything else fails, fix that first — the
      checks exist because each one broke at least once.
- [ ] In the app, press **Clear all**, then **Load 10 samples**. Wait for it to finish.
- [ ] Header badge reads a model name, not "keyword rules only", and no ticket shows a
      **keyword rules** badge. If any do, the model was unreachable when they were classified.

## 2 · Read, in this order (45 min)

Read these **in order**. Each one assumes the last.

- [ ] **`docs/STATUS.md`** (3 min) — what is done, what is not, what is blocked on you. Read it first
      so you know the shape of what you are about to read.
- [ ] **The brief itself** (2 min) — reread their requirements with fresh eyes. Everything else is
      an answer to it.
- [ ] **`README.md`** (8 min) — what a reviewer sees first. *Check: does the first paragraph tell you
      what this is in one breath?*
- [ ] **<http://localhost:8080/architecture>** (8 min) — the pipeline diagram, why guardrails only
      push one way, the four ways a person gets involved, the bug/security boundary.
      *Check: could you redraw the pipeline on a whiteboard from memory?*
- [ ] **`docs/HOW-IT-WORKS.md`** (8 min) — deterministic vs model, who assigns confidence, execution
      order. *Check: can you answer "is it a model or is it rules" in two sentences?*
- [ ] **`docs/EVAL-llm.md`** — read the **summary table and the per-ticket table**, skim the
      rationales (5 min). *Check: can you say what the weakest number is without looking?*
- [ ] **`docs/MODEL-BAKEOFF.md`** (2 min) and **`docs/REPEATABILITY.md`** (3 min) — read them
      together; they disagree, and the disagreement is the point.
- [ ] **`docs/PANEL-QA.md`** (6 min) — the questions with short answers.
- [ ] **`docs/DECISIONS.md`** — **do not read all 45.** Read the "Which calls were mine" table at the
      top, then these six: **D1** (two layers), **D26** (reversing the customer decision), **D34/D37**
      (confidence as a share), **D43** (the gold ticket that broke the recall claim), **D45**
      (confidence scoring the wrong thing). About 8 minutes.

## 3 · Click through it yourself (10 min)

Do this before rehearsing. You are checking that it makes sense to *you*.

- [ ] Type `why was i charged 500 bucks`, then `why was i charged 5000 dollars`. Confirm the urgency
      moves. **If it does not, do not lead with this.**
- [ ] Open the security-researcher ticket. Open **all five boxes**. Read each one.
      *Check: does each explain its own field, or do you have to hold context from another box?*
- [ ] Switch to **Queue board**. *Check: can you see why each ticket is where it is?*
- [ ] Filter to **Escalated**. Count them. Know the number.
- [ ] Open **Full audit record** on one ticket and look at it properly.
      *Check: can you point at the model's answer and the shipped answer separately?*
- [ ] Open a ticket, press **→** a few times to step through. Press **Esc**.

## 4 · Rehearse (30 min)

- [ ] Open **<http://localhost:8080/notes>** in a second window and set it to **15 minutes**.
- [ ] Run it out loud, timed, once. Expect to overrun.
- [ ] Run it again, cutting. The 15-minute cut has a "trim to" note on each beat saying what to drop.
- [ ] Practise saying the weak parts out loud. They land better volunteered:
      - "Urgency exact is 77–88% and moves run to run."
      - "The Terraform has never been applied."
      - "The gold set is 33 tickets I wrote, so it encodes my judgment of the right answer."
      - "The alternatives feature improved discrimination and doubled variance — both numbers are in
        the repeatability doc."

## 5 · The morning of

- [ ] `./scripts/preflight.sh` again. Networks change overnight.
- [ ] Clear and reload the samples so timestamps read "just now".
- [ ] Three tabs: the app, `/notes`, `/architecture`. Notes on your screen, not the shared one.
- [ ] A terminal ready in the repo directory for the API beat.
- [ ] Know these five numbers cold:

| | |
|---|---|
| Escalation recall, both modes | 100% |
| False escalations | none |
| Gold tickets | 33 |
| Model cost vs the cheapest that works | 16x |
| What you have not verified | the Terraform apply |

---

## If you only have time for one thing

Open the app, type the two charge tickets, and open the five boxes on a security ticket. That is the
assignment: unstructured text in, a defensible decision out, with the reasoning attached.
