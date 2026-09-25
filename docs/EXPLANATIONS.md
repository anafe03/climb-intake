# How it works, and why

The strategy, design and reasoning behind the service, and the questions people ask. The app shows the
answers; this explains them. Each section below is one card on the Explanations tab.

## Who sent it

*Named if the ticket says so, otherwise a clearly marked guess.*

### How it decides

- A company name is filled in **only** if the ticket states it. That is a fact.
- Otherwise it makes a best guess, marks it as a guess, gives it a score, and lists the words the guess
  is based on. A guess can never end up in the name field.
- If the model is down, the keyword fallback reads sign-offs, email addresses and account and invoice
  numbers. There is deliberately no pattern for company names: there is no fixed list of them, so a
  pattern would just guess. Named entity recognition is the right tool for that and the next step.

### The full scale

| Score | What it means |
|---|---|
| 0.95 to 1.00 | The company is named in the ticket. A fact, not a guess. |
| 0.75 to 0.94 | A work email or an account number pins the company without naming it. |
| 0.40 to 0.74 | Scale, plan, product or a stated role: the shape of the customer. |
| 0.10 to 0.39 | Only that they are a customer of some kind. |
| 0.00 | Nothing identifies them, and it says so rather than invent one. |

### Questions

- **How do you know it is not making up a customer?** A name is only filled in when the ticket says it.
  Everything else is a labelled guess with its evidence.
- **Then why guess at all?** "Unknown" tells the person picking up the ticket nothing. "A paying customer
  using the export feature" helps, and it is marked as a guess.
- **How often does it get it right?** Every time on the 33 main test tickets, including the ones where the
  right answer is "not stated". On 10 tickets written just for names and account numbers, including two
  traps (a company mentioned that is not the customer, and two companies in one ticket): 10 of 10 names
  and 5 of 5 numbers. Keyword rules alone: 6 of 10 and 2 of 5.
- **Is the score a probability?** No. It is the model's own rating against the scale above. Nobody has
  checked it against real outcomes.
- **Would it know two tickets came from the same company?** Not yet. The sample tickets do not say who
  sent them. It is the first thing to add once tickets come with a login.

## What kind of request

*One of eight categories, and how sure it is.*

### The eight categories

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

### How sure it is

| Score | What it means |
|---|---|
| 0.90 to 1.00 | Only one category fits. |
| 0.70 to 0.89 | Clear, though a neighbouring category is arguable. |
| 0.50 to 0.69 | Defensible, and a reasonable person could pick the other one. |
| Below 0.50 | Not sure enough to send to a team. A person decides instead. |

It also names the runner-up and why it lost. The split between them is the model's own estimate, not a
measured probability.

### Questions

- **What if a ticket fits two teams?** It names the second-best, how close it was, and why it lost. Under
  50% sure, a person decides.
- **Why is spam its own category?** Because otherwise real problems get lost in the same pile as junk.
- **How often is it right?** 32 of the 33 main test tickets. The other, a request for a SOC 2 report,
  could fairly go to either of two teams. Keyword rules alone: 27 of 33.
- **If it nearly always picks the right team, how does it still make mistakes?** Each ticket gets three
  separate answers, graded separately. The cheapest model sent "checkout is charging customers twice" to
  the bug team, which is right, and called it high instead of critical, which is wrong.
- **Who chose 0.50?** I did. It is the one number that changes where a ticket goes, and it sits in a
  settings file a support lead can change without an engineer.

## How urgent

*Four levels, worked out from facts, not tone.*

### The four levels

| Level | What it means |
|---|---|
| Critical | Money moving wrongly, or many people blocked, right now. |
| High | A stated deadline, or real impact on one customer. |
| Medium | A real request with no deadline and contained impact. |
| Low | Cosmetic, or explicitly "whenever you get a chance". |

### What it is read from

Nobody writes "this is medium", so urgency is worked out from five things:

- **A deadline**, stated or implied.
- **Money at stake**, and whose. Their customers' money is worse than their own.
- **How far it spreads**: one person, the whole account, or their customers.
- **Whether it keeps happening.**
- **Whether harm is still happening** as they write.

How angry someone sounds is deliberately not on the list.

### Which way it is wrong

The safe way. On the 33 main test tickets, when urgency was wrong it was always called *more* urgent
than it was (12%), never less. Across all 61 test tickets there was one exception, and it was
borderline. A ticket that arrives too early costs a person a moment to move it down. One that arrives
too late sits and waits. Like a doctor: a needless check-up costs a little, sending a sick person home
costs a lot.

### Questions

- **Does high urgency mean it escalates?** No. Urgency is how fast; escalation is whether someone senior
  needs to know. "Checkout is charging customers twice" pages an engineer but nobody senior. "Our CEO
  loves the new report" is low urgency but goes to someone senior.
- **Could an angry customer make a ticket look more urgent?** No. "This is ridiculous. Third month in a
  row the invoice doesn't match!!!" is medium, because it keeps happening, not because of the shouting.
- **How often is it exactly right?** 88% on the 33 main tickets, 76% with keyword rules alone. The weakest
  number, and why the direction matters more.
- **Did you go easy on the grading?** Some tickets could fairly be low or medium, and count either way.
  The "never too calm" result holds even counting only the tickets with one clear answer.

## Escalation

*The model reads every ticket; a keyword check backs it up; either one is enough.*

### How it decides

Every ticket is read by the model first, which decides whether any of the five topics apply. Then a
keyword check runs as a safety net: about twenty plain word patterns, no model, run over the **original
ticket text** rather than over what the model said about it, so a word the model glossed over still gets
seen. It is allowed to do exactly two things: raise the escalation flag, and lift urgency to a minimum.
It can never lower either, and it never touches the category.

| | Keywords say yes | Keywords say no |
|---|---|---|
| **Model says yes** | Both agree: "a former employee logged in with old credentials". Escalated. | Only the model saw it: "Sam finished up with us in June and can still get in". Escalated. |
| **Model says no** | Only the keywords saw it: "we have *not* had a data breach". Escalated, a false alarm on purpose. | Neither: "can you check our last invoice?" Not escalated. |

The model reads meaning, so it catches what a word list cannot: a British customer instructing
*solicitors*, "the woman who runs our company", the same breach written in Spanish. The keywords never
change, so they still work if the model is updated, its instructions change, or it goes down. A missed
escalation is the expensive mistake, so the design leans towards flagging too much.

### The five topics, and what the keyword check watches for

| Topic | What it covers | Keyword check watches for |
|---|---|---|
| Security incident | someone got in who should not have, credentials not revoked, phishing, a reported hole | unauthorised, credentials, former employee, compromised, phishing, MFA, audit log, vulnerability, CVE, IDOR, exploit |
| Data exposure | they saw someone else's data, or theirs was exposed | another customer's records, exposed data, data leak, leaked, permissions issue, visible to everyone |
| Legal threat | lawyers, breach of contract, a contract dispute | legal team, lawyer, attorney, lawsuit, litigation, in breach of, MSA, arbitration, cease and desist |
| Compliance request | GDPR, CCPA and similar requests with a legal deadline | GDPR, CCPA, HIPAA, DSAR, data subject, right to erasure, regulator |
| Someone senior | a CEO, VP, founder or board named on either side | CEO, CFO, CTO, CISO, founder, VP, chief officer, the board, general counsel |

About twenty patterns in all. An escalated ticket is **copied** to the escalation desk, never moved, so
the team that owns it still sees it.

### Where it breaks

It never missed an escalation in testing. It over-escalates when the words of an incident appear
without the incident: a *denied* breach, a *hypothetical* security hole, someone else's lawyer, "a total
breach of trust" said as an expression.

The worst one: *"To be clear, we have NOT had a data breach. Procurement just needs your SOC 2 report."*
The model got it right, no flag. The keywords saw "data breach", ignored the "not", and flagged it. I am
not fixing it: teaching the keywords when "breach" does not count means a rule that can wrongly ignore
a real breach. A wrong flag costs someone a minute.

### Questions

- **Is escalation just keyword matching?** No. 8 of the 21 escalations in testing had no keyword at all;
  only the model could have caught them.
- **Why keep the keywords, then?** They never change, and they still work when the model is down: on
  their own they catch every escalation in the 33 main test tickets.
- **How often does it flag something it should not?** Never on the 33 main tickets, including traps like
  a SOC 2 request and an invoice sent to a legal department. 4 times on the 12 trick tickets.
- **Why flag a security ticket that already goes to the security team?** So it can be counted. In the
  security queue, a breach and a compliance question look the same. The flag answers "did we miss any?"
- **Does high urgency mean it escalates?** No; see How urgent.

## Where it goes

*A lookup, not a judgement.*

### How a ticket is routed

1. **The category decides the team** (table below).
2. **Critical billing and bug tickets** go to that team's on-call queue instead, so someone is paged.
3. **If it is under 50% sure of the category** and it is not escalated, it goes to human review.
4. **If it escalates**, a copy goes to the escalation desk, on top of its own team.

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

### Questions

- **Is this a real queue?** A stand-in, as the brief asks. Connecting it to Zendesk, Jira or PagerDuty is
  one connector; the sorting would not change.
- **Why copy a flagged ticket instead of moving it?** If it moved, the owning team would never see it.
  Hand-offs are where things get dropped.
- **Who changes where tickets go?** A support lead, in a settings file, without an engineer.

## Keeping it consistent

*What I did to make the answers repeatable, and the proof.*

A model is not deterministic the way a rule is: the same ticket can come back slightly differently.
These are the controls, roughly in order of how much they matter.

1. **A fixed answer format.** One of eight categories, one of four levels, yes or no, a number. It cannot
   invent a ninth category or answer in prose.
2. **Validate every answer, catch every failure.** Each answer is checked against the format before it is
   used. A timeout, error, refusal or malformed answer is caught, and the keyword rules handle the ticket
   instead, marked as such. It happened for real once in the 61-ticket model comparison, and fell back
   cleanly.
3. **Written rules for every field**, with the model told to quote the words that led to each answer.
4. **One worked example** in the instructions: a complete ticket and answer, written fresh so it is not one
   of the tickets being tested, aimed at the medium versus high line where answers wobbled.
5. **The keyword fallback** for escalation cases the model misses.
6. **Low reasoning effort.** Classifying against written rules does not need long thinking. I checked it
   cost no accuracy before keeping it.
7. **Testing built to find failures**, not to pass (see Testing).

### Does it give the same answer twice?

Each of the 10 Climb tickets, read 5 times, before and after adding the worked example: 100 reads.

| | Before the worked example | After |
|---|---|---|
| Category changed | 0 of 10 tickets | 0 of 10 |
| Escalation changed | 0 of 10 | 0 of 10 |
| Queue changed | 0 of 10 | 0 of 10 |
| Stated customer changed | 0 of 10 | 0 of 10 |
| Urgency changed | 2 of 10 | 1 of 10 |
| Category confidence moves by | 0.10 on average | 0.10 on average |
| Who-sent-it confidence moves by | 0.18 on average, 0.45 at most | 0.17 on average, 0.40 at most |

- When urgency changed, it was by one level, one run in five.
- The confidence scores move; the answers do not. The biggest swing is the crypto spam ticket: nothing
  identifies the sender, so the score wanders, but the answer ("not stated") never changes.
- I checked this by eye. 50 reads either side shows the pattern; it does not prove the worked example
  helped. It fixed the two tickets it was aimed at, one other ticket wobbled once, and the main scorecard
  improved urgency from 82% to 88% exact with escalation unchanged.

### In production

- Re-run a sample of real tickets on a schedule; track, per field, how often an answer flips and how far
  confidence moves. Alert if either climbs.
- Re-run the full test before any change to the instructions or the model ships.
- Have a subject-matter expert review the tickets that flip. They are the most worth labelling, and they
  become the next worked examples.

## Cost and model choice

*About $10 per 1,000 tickets, and why not something cheaper.*

Every decision records its own cost from the tokens actually used. All 61 labelled test tickets, four
setups:

| Model | Escalations caught | False escalations | Urgency too low | Per 1,000 tickets |
|---|---|---|---|---|
| gpt-5 | 21 of 21 | 1 | 1 (borderline) | $9.68 |
| gpt-5-mini | 21 of 21 | 3 | 3 (all borderline) | $1.82 |
| gpt-5-mini, minimal effort | 21 of 21 | 8 | 2 (all borderline) | $1.30 |
| gpt-5-nano | **19 of 21** | 1 | **9, including 4 clearly critical** | $0.37 |

- **gpt-5 is what I run.** Every escalation caught, fewest mistakes.
- **Nano is out, however cheap.** It missed 2 escalations and read 4 clearly critical tickets as less
  urgent, including the checkout charging customers twice.
- **Less thinking made mini worse, not just cheaper.** Minimal effort took its false escalations from 3 to 8.
- Picking the team is not in the table because every model got it right, so it cannot help choose.

### A small model first, a bigger one when it matters

Default to the cheap model, and send a ticket to the bigger one only when it looks risky. I built two
versions and measured both on the 33 main test tickets:

| Version | Result |
|---|---|
| The free keyword check decides which model reads each ticket: risky words go to gpt-5, the rest to mini. Each ticket is read once. | **38% cheaper.** One extra false escalation and one urgency call too low. |
| Mini reads every ticket, and gpt-5 re-reads the ones mini flags or is unsure about. | **29% more expensive.** |

The second costs more because every risky ticket is paid for twice, and the risky ones are the
expensive ones: a re-read ticket cost about 1.73 cents against a 0.91 cent average.

**Why I have not switched.** 38% of about $9 is about $3.50 a month at 1,000 tickets, and about $170 a
month at 50,000. That is roughly where I would start to consider it. The 38% is measured; the 50,000 is
my judgement. At scale the first lever would be batching non-urgent tickets, before changing the model.

The model comparison, the small-then-big versions, the trick tickets, the no-keyword test and the
extraction test were run before the worked example was added to the instructions.

## When something fails

*Nothing is dropped.*

- **The model times out, errors or is down.** The keyword rules read the ticket and it is marked as such.
  Escalation words still flag it to a person. If the keyword rules are not sure of the team, it goes to
  human review.
- **The model returns something that does not fit the format.** Caught, handled the same way.
- **The model is unsure of the category.** Under 50% sure, a person decides.
- **The connection drops.** Retried a few times first, because those fail fast and usually recover.

## Testing

*Built to find failures, not to pass.*

| Set | What it is for | Result |
|---|---|---|
| 33 main test tickets | the 10 Climb provided plus 23 edge cases I wrote | every escalation caught, no false ones; urgency 88% exact, never too calm |
| 12 trick tickets | written to break it | no missed escalations; 4 over-escalations |
| 6 no-keyword tickets | escalations with none of the keyword words | the model caught all 5 that needed it |
| 10 extraction tickets | names, contacts, account numbers, two traps | 10 of 10 names, 5 of 5 numbers |
| 10 Climb tickets, 5 runs each | does it repeat itself | see Keeping it consistent |

**Who wrote the answers.** I did, for 23 of the 33 main tickets. That is a weakness: I also wrote the
instructions, so agreement proves less than it looks. The 10 Climb tickets are the fair test, and it got
all 10 right.

## With more time

*What I would do next.*

- Real tickets labelled by two people who did not write the instructions, and a held-back set never used
  for tuning.
- Named entity recognition for company names.
- A scheduled consistency check in production, with an expert reviewing the tickets that flip.
- Tickets from the same customer grouped together once there is a login.
- Batch the non-urgent tickets to cut cost before touching the model choice.
