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

## Block 6: final run-through comments (2026-09-25)  (DONE)

Austin's words are quoted so nothing is paraphrased away.

- [x] **"we probably should have more extraction cases and failed extraction"**
      *Failed:* three real failures recorded by `scripts/record_failures.py`. Each is a genuine
      model call that timed out, not a mock, then fell back to keyword rules. Data menu, "3 failed
      extractions". They show the range: climb-03 still escalates on a keyword, climb-01 still
      routes, and kf-02 (a legal threat written with "solicitors") loses its escalation but lands in
      human-review for a person. The failure notice now sits right under the ticket text, not at the
      bottom, and the Escalate box no longer claims "not a legal matter" on a fallback ticket.
      *Extraction:* `data/extraction_cases.jsonl`, ten tickets on names, contacts and identifiers,
      two of them traps (a company named that is not the customer). Model: 10 of 10 names, 5 of 5
      identifiers. Keyword rules: 6 of 10 and 2 of 5. `docs/EXTRACTION-llm.md`, `EXTRACTION-rules.md`.
- [x] **Support-hour comparison, "cite it or something"** Deleted. It was uncited and I made it up.
- [x] **"what 38% and 50k"** Deleted from the cost page and from your beat 7 script, so you are not
      saying anything on stage you would have to look up.
- [x] **"what do you mean cached token"** Deleted from the cost page.
- [x] **Escalation recall "should be clickable to show them"** "11 of 11" on the cost page opens every
      ticket that should escalate, across the gold set, the adversarial set and the no-keyword set,
      with whether a keyword also fired. The dashboard links straight to it.
- [x] **"why do we do keyword rules only for escalation" / "did you make the change to ask the model
      if it doesn't hit keyword rules"** It already works that way, and the table made it look like it
      didn't. The model reads every ticket first (`pipeline.py` line 91); the keywords run after it as
      an extra check (line 115). Removed the "keyword rules only" row from the model table; it was the
      no-API-key fallback, not a choice. Proof: 21 of 21 escalations caught, 8 of them with no
      keyword at all.
- [x] **"just the table is fine comparing them, the rest is superfluous"** The cost page is the table.
- [x] **"remove AI writing with the - in them"** No spaced em dashes left in anything visible on the
      three pages. Paired dashes became commas, single ones colons, and every changed line was read;
      the joins that read badly were rewritten by hand.

Also found on the way:
- [x] The presenter requirement table pointed at beat numbers from before the renumbering, and said
      the Terraform has four resources (it has eight).

Earlier in this run-through, already done:
- [x] "intake is good except don't say the same thing three times" (D100)
- [x] "how it works sucks, it can be dropped for now" (D100)
- [x] The comparison card on the dashboard, measured not estimated: "I don't need that math" (D99)

## Still open

- [ ] No git remote. The only unmet deliverable, and it needs your GitHub account — `preflight.sh`
      fails on exactly this one check.
- [ ] Terraform validates but has never been applied. Needs a GCP project.
