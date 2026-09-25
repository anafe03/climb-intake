# Does it give the same answer twice?

The 10 tickets Climb provided, each read 5 times, before and after adding one worked example to the
instructions. 100 reads in total. Nothing here is graded against a right answer; the only question is
whether the same ticket gets the same answer.

| | Before the worked example | After |
|---|---|---|
| Tickets where the category changed | 0 of 10  | 0 of 10  |
| Tickets where urgency changed | 2 of 10 (climb-06, climb-07) | 1 of 10 (climb-01) |
| Tickets where escalation changed | 0 of 10  | 0 of 10  |
| Tickets where the queue changed | 0 of 10  | 0 of 10  |
| Tickets where the stated customer changed | 0 of 10  | 0 of 10  |
| Category confidence, how far it moves | 0.10 on average, 0.15 at most | 0.10 on average, 0.20 at most |
| Who-sent-it confidence, how far it moves | 0.18 on average, 0.45 at most | 0.17 on average, 0.40 at most |

## What moved

- **Urgency, by one level, one run in five.** Before: the double-billing ticket (climb-06) was medium four
  times and high once; the CEO onboarding ticket (climb-07) was critical four times and high once. After the
  worked example both came back the same all five times, and a different ticket (climb-01, the $4,200
  invoice) was high once and medium four times. Always the neighbouring level, never two levels apart.
- **The confidence scores move, the answers do not.** Category confidence moves about 0.10. Who-sent-it
  confidence moves most on the spam ticket, where there is nothing to identify the sender and the score
  wandered between 0.25 and 0.70. The answer itself ("not stated") never changed.
- **Category, escalation, the queue and the stated customer never changed**, in any of the 100 reads.

## How to read it

We checked this by eye: 50 reads either side is enough to see the pattern, not enough to prove the worked
example helped. It moved the two tickets it was aimed at and nothing got worse, and the main scorecard on
the new instructions improved urgency from 82% to 88% exact with escalation unchanged.

## How this would scale in production

- Re-run a sample of real tickets on a schedule and track, per field, how often an answer flips and how far
  the confidence moves. Alert if either rises.
- Re-run the whole test after any change to the instructions or the model, before it ships.
- Send the tickets that flip to a subject-matter expert to review: they are the ones worth labelling, and
  they become new worked examples.

`scripts/consistency.py --label <name> --runs 5` produces this. Raw results in `data/measured/`.
