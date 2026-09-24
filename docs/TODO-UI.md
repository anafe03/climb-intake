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

## Block 2 — escalate, route, and the duplication  (IN PROGRESS)

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
- [ ] Same treatment as block 1: reason first, reference after, no lead-in prose
- [ ] Decide whether the five escalation topics need their own rubric popup

## Block 3 — questions to settle in the docs

- [x] **Is a split better practice than one confidence number?** Write the answer down: what we have
      is a self-reported share, not a calibrated probability, and the distinction matters.
- [ ] **Docker**: Austin wants help with the deployment side.
