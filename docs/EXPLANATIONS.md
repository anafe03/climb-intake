# Strategy, design and FAQs

## Consistency

*Rules always give the same answer. The model might not, so we tested it.*

### What needs testing

The keyword checks and routing are plain rules: same text in, same answer out. The model isn't. The same
ticket can come back a little different, so that's what we control and measure.

### How the model is kept consistent

- **Prompt schema.** Fixed answers only: one of 8 categories, one of 4 urgency levels, yes/no, a score. No
  hallucinated answers.
- **Every answer checked against the schema** before it's used. If the call fails or the answer doesn't
  fit (timeout, error, refusal, bad format), the keyword check reads the ticket instead.
- **One worked example** in the prompt, aimed at medium vs high urgency, where answers wobbled.
- **Written rules** for every decision, and the model quotes the words it used.
- **Low reasoning effort.** Same accuracy, about half the cost.

### Where the keyword check can change the AI's answer

| Decision | Can it overrule the AI? | Why |
|---|---|---|
| Escalation | Yes, only to add a flag | Flagging too much is the safe mistake. |
| Urgency | Yes, only upward | Too urgent is the safe mistake. |
| Category | No, fallback only | No safe answer; one ticket can't go to two teams. |
| Who sent it | No, fallback only | A wrong company isn't safer than a right one. |
| Where it goes | Not needed | A fixed table. |

### The test: the same ticket, five times

The 10 Climb tickets, 5 reads each, with and without the example.

| | Without the example | With it |
|---|---|---|
| Category, escalation, queue or company changed | 0 of 10 | 0 of 10 |
| Urgency changed | 2 of 10 | 1 of 10 |

- Urgency only ever moved one level, in one run of five.
- The free-text parts (the reasons, the guess at who sent it) are reworded each run. That's why only the
  fixed answers decide where a ticket goes.
- With the example, urgency on the main test set went from 82% to 88% exactly right.

### In production

- Re-run a sample of real tickets on a schedule and alert if answers start flipping.
- Re-run the full test before any prompt or model change ships.
- Have an expert label the tickets that flip. They become the next examples.

## Cost

*About $10 per 1,000 tickets, and why not something cheaper.*

Every decision records its own cost from the tokens actually used. All 61 labelled test tickets, four setups:

| Model | Escalations caught | False escalations | Urgency too low | Per 1,000 tickets |
|---|---|---|---|---|
| gpt-5 | 21 of 21 | 1 | 1 (borderline) | $9.68 |
| gpt-5-mini | 21 of 21 | 3 | 3 (all borderline) | $1.82 |
| gpt-5-mini, minimal effort | 21 of 21 | 8 | 2 (all borderline) | $1.30 |
| gpt-5-nano | **19 of 21** | 1 | **9, including 4 clearly critical** | $0.37 |

The dashboard shows what the tickets on screen cost, so its number differs a little from this average:
tickets that need more thinking cost more to read.

- **gpt-5 is what I run.** Every escalation caught, fewest mistakes.
- **Nano is out, however cheap.** It missed 2 escalations and read 4 clearly critical tickets as less urgent,
  including the checkout charging customers twice.
- **Less thinking made mini worse, not just cheaper.** Minimal effort took its false escalations from 3 to 8.

### A small model first, a bigger one when it matters

Default to the cheap model; send a ticket to the bigger one only when it looks risky. Two versions, measured
on the 33 main test tickets:

| Version | Result |
|---|---|
| The keyword check decides which model reads each ticket: risky words go to gpt-5, the rest to mini. Each ticket is read once. | **38% cheaper.** One extra false escalation and one urgency call too low. |
| Mini reads every ticket, and gpt-5 re-reads the ones mini flags or is unsure about. | **29% more expensive.** |

The second costs more because every risky ticket is paid for twice, and the risky ones are the expensive
ones: a re-read ticket cost about 1.73 cents against a 0.91 cent average.

**Why I have not switched.** 38% of about $9 is about $3.50 a month at 1,000 tickets, and about $170 a month
at 50,000. That is roughly where I would consider it. The 38% is measured; the 50,000 is my judgement. At
scale the first lever is batching non-urgent tickets, before changing the model.

The model comparison and the small-then-big versions were run before the worked example was added.

## Robustness (fallbacks)

*Nothing is dropped.*

- **The model times out, errors or is down.** The keyword check reads the ticket and it is marked as such.
  Escalation words still flag it to a person. If the keyword check is not sure of the team, it goes to human
  review.
- **The model returns something that does not fit the format.** Caught by the schema check, handled the
  same way.
- **The model is unsure of the category.** Under 50% sure, a person decides.
- **The connection drops.** Retried a few times first, because those fail fast and usually recover.

## Testing and accuracy

*Built to find failures, not to pass.*

| Set | What it is for | Result |
|---|---|---|
| 33 main test tickets | the 10 Climb provided plus 23 edge cases I wrote | every escalation caught, no false ones; urgency 88% exact, never too calm |
| 12 trick tickets | written to break it | no missed escalations; 4 over-escalations |
| 6 no-keyword tickets | escalations with none of the keyword words | the model caught all 5 that needed it |
| 10 extraction tickets | names, contacts, account numbers, two traps | 10 of 10 names, 5 of 5 numbers |
| 10 Climb tickets, 5 runs each | does the model repeat itself | see Consistency |

The trick, no-keyword and extraction sets were run before the worked example was added.

**Who wrote the tests.** I wrote 23 of the 33 main test tickets, and that has a limit: if I already knew a
way it breaks, I would have fixed it. So the hardest failures to test for are the ones I have not thought
of. That is why the trick tickets were written to break it on purpose, why the 10 Climb tickets are the fairest
test (it got all 10 right), and why the next step is real tickets labelled by other people.

## Going forward

*What I would do next.*

- Real tickets labelled by two people who did not write the instructions, and a held-back set never used for
  tuning.
- Keep the keyword check as the fallback and safety net. Replace its company-name patterns with a named
  entity recognition model, so names are found anywhere in a sentence when the LLM is down.
- A scheduled consistency check in production, with an expert reviewing the tickets that flip.
- Tickets from the same customer grouped together once there is a login.
- Batch the non-urgent tickets to cut cost before touching the model choice.

## Who sent it

*Named if the ticket says so, otherwise a clearly marked guess.*

### How we decide

The LLM decides. The keyword check is only a fallback: it runs when the LLM is down and never overrules it.

### The LLM

- Fills in a company name **only** if the ticket states it, wherever it appears.
- Otherwise it guesses, marks it as a guess, scores it, and lists the words it used. A guess never goes in
  the name field.

| Score | What it means |
|---|---|
| 0.95 to 1.00 | The company is named in the ticket. A fact, not a guess. |
| 0.75 to 0.94 | A work email or an account number pins the company without naming it. |
| 0.40 to 0.74 | Scale, plan, product or a stated role: the shape of the customer. |
| 0.10 to 0.39 | Only that they are a customer of some kind. |
| 0.00 | Nothing identifies them, and it says so rather than invent one. |

### The keyword check

Runs only if the LLM does not answer. It finds a company in two places:

- **Right after "from", "at" or "on behalf of"**, starting with a capital: "this is Dana *from Acme Logistics*".
- **A sign-off line** starting with a dash: "— Priya Raghavan, *Meridian Health*".

Otherwise it makes a labelled guess from clues:

| Clue in the ticket | Its guess | Score |
|---|---|---|
| a work email, like `dana@acme.com` | someone at acme.com | 0.8 |
| a team size, like "50 users" | a customer with a sizeable team | 0.5 |
| a plan name, like "Team plan" | a customer on that plan | 0.45 |
| enterprise words, like "workspace" or "Databricks" | an enterprise customer | 0.45 |
| a personal email (gmail, outlook) | an individual user | 0.3 |
| only an invoice or account number | an existing customer | 0.3 |
| nothing | not stated | 0.0 |

### Questions

- **Why can't the keyword check overrule the LLM here?** There is no safe direction for a company name: a
  wrong company is not more cautious than a right one. So it is a fallback only.
- **Why can't the keyword check find a company name anywhere in a sentence?** Word patterns in those two
  places were the best choice for a fallback. Patterns cannot recognise every name: there is no list of every
  company to check against. A named entity recognition model could, and that is the next step. From a
  business side it is not the riskiest part: a missed name slows a reply, a missed escalation costs real money.
- **How do you know it is not making up a customer?** A name is only filled in when the ticket says it.
  Everything else is a labelled guess with its evidence.
- **Why guess at all?** "Unknown" tells the person picking up the ticket nothing. "A paying customer using the
  export feature" helps, and it is marked as a guess.
- **How often is it right?** Every time on the 33 main test tickets. On 10 tickets written for names and
  account numbers, with two traps: 10 of 10 names and 5 of 5 numbers. The keyword check alone: 6 of 10 and 2 of 5.
- **Is the score a probability?** No. It is the LLM's rating against the scale above, not checked against
  real outcomes.
- **Would it know two tickets came from the same company?** Not yet. That comes once tickets carry a login.

## What kind of request

*One of eight categories, and how sure it is.*

### How we decide

The LLM decides. The keyword check is only a fallback: it runs when the LLM is down and never overrules it.
Under 0.50 sure, a person decides instead of a team.

### The LLM

Picks exactly one category, names the runner-up and why it lost, and scores how sure it is.

| Category | What it covers |
|---|---|
| Billing | charges, invoices, refunds, plan changes, pricing, seats, renewals with no legal threat |
| Bug | something in the product is broken or behaving wrongly |
| Security | unauthorised access, credentials, data exposure, vulnerabilities, phishing |
| Legal / contract | contract disputes, breach claims, legal threats, regulatory demands |
| Onboarding | implementation, setup, go-live progress for an account |
| Feature request | asking for something the product does not do yet, limit increases, roadmap |
| Spam | nonsense, solicitations, trolling. A real answer, not a failure to decide. |
| Other | a real request that fits none of the above |

| Score | What it means |
|---|---|
| 0.90 to 1.00 | Only one category fits. |
| 0.70 to 0.89 | Clear, though a neighbouring category is arguable. |
| 0.50 to 0.69 | Defensible, and a reasonable person could pick the other one. |
| Below 0.50 | Not sure enough to send to a team. A person decides instead. |

### The keyword check

Runs only if the LLM does not answer. It checks in a fixed order and takes the first match:

1. security or data-exposure words: security
2. legal or compliance words: legal / contract
3. two or more spam signals (crypto, discord, free credits, SEO, "click here"): spam
4. bug words (error, broken, crash, down) against billing words (invoice, charged, refund, plan, seats):
   whichever there are more of
5. onboarding words (set up, go-live, migration), then feature words (can you add, roadmap)
6. otherwise: other

Its scores are deliberately low, so anything it is unsure of goes to a person.

### Questions

- **Why can't the keyword check overrule the LLM here?** There are eight answers and none of them is the
  safe one. If the keywords say bug and the LLM says billing, you cannot send one ticket to two teams. And
  the keyword check counts words; the LLM reads the ticket.
- **What if a ticket fits two teams?** The LLM names the second-best and why it lost. Under 50% sure, a
  person decides.
- **Why is spam its own category?** Otherwise real problems get lost in the same pile as junk.
- **How often is it right?** 32 of the 33 main test tickets. The other, a SOC 2 report request, could fairly
  go to either of two teams. The keyword check alone: 27 of 33.
- **Who chose 0.50?** I did. It sits in a settings file a support lead can change without an engineer.

## How urgent

*Four levels, worked out from facts, not tone.*

### How we decide

The LLM decides. The keyword check runs on every ticket and can only **raise** urgency, never lower it,
because too urgent is the safe mistake. When the LLM is down, the keyword check decides alone.

### The LLM

Works urgency out from five facts: a deadline, money at stake, how far it spreads, whether it keeps
happening, and whether harm is still happening. How angry someone sounds is deliberately not one of them.

| Level | What it means |
|---|---|
| Critical | Money moving wrongly, or many people blocked, right now. |
| High | A stated deadline, or real impact on one customer. |
| Medium | A real request with no deadline and contained impact. |
| Low | Cosmetic, or explicitly "whenever you get a chance". |

### The keyword check

- **On every ticket:** an escalation word sets a floor. Security incident: high. Data exposure: critical.
  Legal threat: high. Compliance request: high. Someone senior: no change.
- **When the LLM is down:** outage words ("is down", "all our users") or many customers double-charged:
  critical. A deadline (today, by Friday, ASAP): high. "No rush": low. Otherwise medium.

### Questions

- **Why can the keyword check overrule the LLM here, but not for category?** Urgency has a safe direction:
  up. Too urgent costs someone a moment; too calm means the ticket waits.
- **Which way is it wrong?** The safe way. On the 33 main tickets, when urgency was wrong it was too high (12%
  of tickets), never too low. Across all 61 test tickets, one exception, and it was borderline.
- **Does high urgency mean it escalates?** No. Urgency is how fast; escalation is whether someone senior
  needs to know. Double-charged checkout pages an engineer but nobody senior.
- **Could an angry customer make a ticket look more urgent?** No. "Third month in a row the invoice doesn't
  match!!!" is medium because it keeps happening, not because of the shouting.
- **How often is it exactly right?** 88% on the 33 main tickets, 76% with the keyword check alone. Our
  weakest number, but never wrong in the dangerous direction.

## Escalation

*The LLM reads every ticket; a keyword check backs it up; either one is enough.*

### How we decide

Both run on every ticket. If **either** says escalate, it escalates. The keyword check can add a flag and
never remove one, because a missed escalation is the expensive mistake.

| | Keywords say yes | Keywords say no |
|---|---|---|
| **LLM says yes** | "a former employee logged in with old credentials". Escalated. | "Sam finished up with us in June and can still get in". Escalated. |
| **LLM says no** | "we have *not* had a data breach". Escalated, a false alarm on purpose. | "can you check our last invoice?" Not escalated. |

### The LLM

Reads the ticket for meaning and decides whether any of the five topics apply. That is what catches a
British customer instructing *solicitors*, "the woman who runs our company", or a breach written in Spanish,
none of which a word list would find.

An escalated ticket is **copied** to the escalation desk, never moved, so the owning team still sees it.

### The keyword check

About twenty word patterns across five topics, run over the original ticket text, not the LLM's summary,
so a word the LLM glossed over still gets seen.

| Topic | Keyword check looks for |
|---|---|
| Security incident | unauthorised, credentials, former employee, compromised, phishing, MFA, vulnerability, CVE, exploit |
| Data exposure | another customer's records, exposed data, data leak, leaked, visible to everyone |
| Legal threat | legal team, lawyer, attorney, lawsuit, litigation, in breach of, MSA, arbitration, cease and desist |
| Compliance request | GDPR, CCPA, HIPAA, DSAR, data subject, right to erasure, regulator |
| Someone senior | CEO, CFO, CTO, CISO, founder, VP, chief officer, the board, general counsel |

### Questions

- **Is escalation just keyword matching?** No. 8 of the 21 escalations in testing had no keyword at all; only
  the LLM caught them.
- **Why keep the keywords, then?** They never change, and they still work when the LLM is down: alone they
  catch every escalation in the 33 main test tickets.
- **Where does it break?** It over-escalates when incident words appear without an incident: "we have NOT had
  a data breach". The LLM got that right; the keywords ignored the "not". I am not fixing it: a rule that
  ignores "breach" can ignore a real one. A wrong flag costs someone a minute.
- **How often does it flag something it should not?** Never on the 33 main tickets. 4 times on the 12 trick
  tickets.
- **Why flag a security ticket that already goes to security?** So it can be counted. The flag answers "did
  we miss any?"

## Where it goes

*A lookup, not a judgement.*

### How we decide

A fixed table, so the same answers always go to the same queue. It takes the category, urgency and
escalation already decided, in this order:

1. **The category decides the team.**
2. **Critical billing and bug tickets** go to that team's on-call queue, so someone is paged.
3. **Under 50% sure of the category**, and not escalated: human review.
4. **Escalated:** a copy goes to the escalation desk, on top of its own team.

| Queue | Who works it |
|---|---|
| Billing | billing team; its on-call queue when money is moving wrongly |
| Engineering | product bugs; its on-call queue when it is critical |
| Security | security team, always paged |
| Legal and account management | legal plus the account owner |
| Customer success | the account team |
| Product feedback | feature requests, no deadline |
| Spam review | checked at a glance and discarded |
| General support | the front line, for everything else |
| Human review | a person decides, when the reading was unsure |
| Escalation desk | a person must see it, on top of its own team |

### The LLM

Not used here. No model sits in this step, so routing never changes from one run to the next.

### The keyword check

Not used here either. Its only effect is through the answers it may already have changed: a raised urgency or an
added escalation flag.

### Questions

- **Is this a real queue?** A stand-in, as the brief asks. Connecting Zendesk, Jira or PagerDuty is one
  connector; the sorting would not change.
- **Why copy a flagged ticket instead of moving it?** If it moved, the owning team would never see it.
  Hand-offs are where things get dropped.
- **Who changes where tickets go?** A support lead, in a settings file, without an engineer.
