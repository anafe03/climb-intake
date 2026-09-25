# UI changes requested — working list

Austin's feedback, 2026-09-24. Doing the first block now; escalate and route after.

## Block 1 — who / what kind / how urgent / dashboard  (DONE)

- [x] Put the ticket text at the top of every pop-out, so you never lose the thing being explained
- [x] "Why this ticket read that way" goes **first** in every pop-out, before any reference material
- [x] Drop the AI-ish lead-in lines:
      - "One of eight categories. Spam is a real answer, not a failure to classify."
      - "Never stated in the ticket. Always inferred, which is the part a keyword matcher cannot do."
      - "Two separate things: what the text states outright, and what we can infer from context…"
- [x] Confirm "Why it was designed this way" is gone everywhere (removed in D57 — verify the
      container is serving it)
- [x] **Who sent it**: show which confidence rung this ticket landed on and what decided it, the way
      the category pop-out already does
- [x] **How urgent**: list the levels most severe first, not least
- [x] **Dashboard**: order the urgency breakdown by severity (Critical, High, Medium, Low), not by count

## Block 2 — escalate, route, and the duplication  (DONE)

- [x] **Card subtitles repeat the pop-out.** The "Who sent it" card prints the full basis
      ("Inferred, not stated. From …") and then the pop-out prints it again. The card should show
      the answer and the score; the evidence belongs in the pop-out only.
- [x] **The safety net line is too terse.** "A keyword rule matched and agreed — nothing changed"
      plus a rule name does not explain what a guardrail rule *is* or why it ran. Expand it.
- [x] **Answer "why does security escalate as well as route to the security team?"** properly. The
      current answer leans on "the brief asks for a flag", which is true but thin. Say when the
      escalation desk adds something and when it is belt-and-braces.
- [x] **The audit record needs field-level explanation** — what each field is and where it is used,
      on click rather than as a wall.
- [x] Same treatment as block 1: reason first, reference after, no lead-in prose
- [x] Decide whether the five escalation topics need their own rubric popup — **no**. A topic
      is binary, so there is no ladder to show. Each one now lists the keywords the guardrail
      greps for instead, which is what a reader actually wants there (D63).

## Block 3 — questions to settle in the docs  (DONE)

- [x] **Is a split better practice than one confidence number?** Write the answer down: what we have
      is a self-reported share, not a calibrated probability, and the distinction matters.
- [x] **Docker**: [DEPLOY.md](DEPLOY.md) is the runbook — three commands, what each Dockerfile
      choice buys, how secrets reach the container, what changes for real traffic, and a
      what-to-check-when-it-breaks table. The Terraform was OpenAI-blind; fixed (D66).

## Block 4 — the order, and the landing view  (1 of 6 left)

Austin, reading it as a demo: "the decision should always be first, then the criteria and evidence
for that decision." Correct, and it invalidated the rule from block 1 — reason-first was an
improvement but still put a rubric ahead of the answer.

- [x] **Every pop-out reads: ticket -> the decision -> the evidence -> the rubric.** The answer is
      styled as the answer, not left as a footnote at the bottom (D67).
- [x] **Queues opens by default** and sits first in the toolbar (D68).
- [x] **Dashboard is only the numbers**; Queues is only the tickets. They were showing the same
      list twice under two names. Every dashboard number filters through to Queues (D69).
- [x] **The safety net says what it is before what it did** — twenty-odd regexes in `app/rules.py`,
      no model, run over the original ticket text, allowed only to raise the flag and lift urgency
      to a floor (D70).
- [x] **The five urgency signals explain themselves** — what each one means and which way it moves
      the level, plus why tone is deliberately not among them (D70).
- [x] **Show consistency on repeat reads, live.** Austin: "i want to show this is consistent for
      each ticket when read multiple times." `scripts/repeatability.py` and `docs/REPEATABILITY.md`
      measure this offline, but a panel cannot see it. Proposed: a **Read it again** button in the
      ticket dialog that re-runs the same text and shows the two answers side by side, with the
      fields that matched marked. Re-running in front of them beats citing a number from a doc.
      **Built.** `POST /tickets/{id}/recheck`, plus a button in section 3 of the dialog. Only the
      fields that change routing are scored; confidence and wording are shown moving rather than
      marked wrong (D71). A live run held all five routing fields identical while customer
      confidence went 0.50 / 0.35 / 0.30.
- [x] **Say why every ticket is not read several times** — it triples the bill for a number that
      does not change the routing. Answered in the dialog, under the button (D72).
- [x] **A clickable FAQ per classification type** — the three or four questions people ask about
      that field, collapsed, at the end of each pop-out, sourced from `docs/PANEL-QA.md` (D73).

## Found while doing the above

- [x] The routing walkthrough claimed "critical -> the on-call queue instead" on tickets that were
      never rerouted, because only `billing` and `bug` have a critical override (D64).
- [x] `/docs` was FastAPI's default page, linked from the app header. Now documented (D65).

## Block 5 — cost, model choice, and going looking for failure  (DONE)

- [x] **Show what it costs.** `app/pricing.py` is the one rate card; every decision carries
      `usage.cost_usd`; the ticket footer and a dashboard card show it (D80).
- [x] **Compare models with scores, not just price** — `/optimization`, its own nav item, opening
      with a recommendation. Nano is 26x cheaper and disqualified (D81, D94).
- [x] **Build the cascade instead of describing it.** The obvious version costs 29% *more*; the
      keyword-triaged version is 38% cheaper and ships off by default (D84, D85).
- [x] **Go looking for failures.** 12 adversarial tickets: no missed escalations, four
      over-escalations, all one shape (D91).
- [x] **Prove the model half earns its place** — six keyword-free escalations, all caught (D89).
- [x] **Score urgency by direction**, not accuracy: 0% under-called (D75).
- [x] Presenter notes: two new beats, renumbered 0–13, both scripts back under time.
- [x] Swept stale numbers out of PANEL-QA, STATUS, PREP, DEMO and HOW-IT-WORKS. STATUS still
      recommended nano, which the evidence now disqualifies.

## Block 6: final run-through comments (2026-09-25)

Austin's words are quoted so nothing is paraphrased away.

- [ ] **"we probably should have more extraction cases and failed extraction"**
      The dashboard says "Failed extractions: 0" and nothing in the demo ever shows one happening.
      Add real failed-extraction cases (a genuine model failure that fell back to keyword rules, not a
      mock) so the card can show a nonzero and a click shows what fallback looks like. Add more
      extraction cases: customer names, contacts and identifiers, the fields the gold set barely tests.
- [ ] **"It costs 0.9¢ a ticket, about $9 per thousand, or roughly what one support hour costs per
      forty thousand tickets" / "wtf does this mean, cite it or something"**
      The support-hour comparison is uncited and I made it up. Delete it.
- [ ] **"the saving is a few dollars a month ... Revisit at about 50,000 tickets a month, where the
      38% saving becomes real money" / "wtf does this mean what 38% and 50k"**
      Unexplained jargon. Delete.
- [ ] **"what do you mean cached token, 90% of input tokens are cache reads at a tenth of the price"**
      Unexplained. Delete from the cost page.
- [ ] **Escalation recall "100%, 11 of 11 on the gold set, and no miss on the 12 adversarial
      tickets either" / "this should be clickable to show them"**
      Make it clickable. The click shows the actual tickets and whether each was caught.
- [ ] **"keyword rules only ... 100% none none none 0.0s $0 $0 free" / "why do we do keyword rules
      only for escalation" / "did you make the change to if it doesn't hit keyword rules to ask the
      model just in case it's not in the keywords" / "i dont understand this keyword rules only"**
      Answer plainly: the model reads every ticket; keywords are a second check on top, never
      instead. That row is the fallback when there is no API key, which is not a choice anyone makes
      in production, and putting it in a model comparison made it look like one. Remove it from the
      table. Show the proof that the model catches what keywords miss.
- [ ] **"most of the stuff in cost I don't understand, just the table is fine comparing them, the
      rest is superfluous"**
      Cut the cost page to the comparison table.
- [ ] **"remove superfluousness and AI writing with the - in them"**
      No em dashes in anything a person reads in the app. Plain sentences.

Earlier in this run-through, already done:
- [x] "intake is good except don't say the same thing three times" (D100)
- [x] "how it works sucks, it can be dropped for now" (D100)
- [x] The comparison card on the dashboard, measured not estimated: "I don't need that math" (D99)

## Still open

- [ ] No git remote. The only unmet deliverable, and it needs your GitHub account — `preflight.sh`
      fails on exactly this one check.
- [ ] Terraform validates but has never been applied. Needs a GCP project.
