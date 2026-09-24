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

## Block 2 — escalate and route  (NEXT)

- [ ] Same treatment: reason first, reference after, no lead-in prose
- [ ] Decide whether the five escalation topics need their own rubric popup
