# Strategy and design

## Consistency

*Rules always give the same answer. The model might not, so we tested it.*

### What needs testing

The keyword checks and routing are rules. They always give the same answer. The model can vary. That is
what we control and measure.

### How the model is kept consistent

- **Prompt schema.** Fixed answers only: one of 8 categories, one of 4 urgency levels, yes/no, a score. No
  hallucinated answers.
- **Every answer checked against the schema** before it's used. If the call fails or the answer doesn't
  fit (timeout, error, refusal, bad format), the keyword check reads the ticket instead.
- **One-shot prompting.** The prompt includes one worked example, a full ticket and its answer, aimed at
  medium vs high urgency, where answers wobbled.
- **Written rules** for every decision, and the model quotes the words it used.
- **Low reasoning effort.** Same accuracy, about half the cost.

### Where the keyword check can change the AI's answer

| Decision | Can it overrule the AI? | Why |
|---|---|---|
| Escalation | Yes, only to add a flag | Flagging too much is the safe mistake. |
| Urgency | Yes, only upward | Too urgent is the safe mistake. |
| Category | No, fallback only | No safe answer. |
| Who sent it | No, fallback only | A wrong company isn't safer than a right one. |
| Where it goes | Not needed | A fixed table. |

### Variation testing: the same ticket through the LLM five times

The 10 Climb tickets, 5 reads each, with and without the example.

| | Without the example | With it |
|---|---|---|
| Category, escalation, queue or company changed | 0 of 10 | 0 of 10 |
| Urgency changed | 2 of 10 | 1 of 10 |
| Category confidence moves by | 0.10 on average | 0.10 on average |
| Who-sent-it confidence moves by | 0.18 on average, 0.45 at most | 0.17 on average, 0.40 at most |

### In production

- Re-run the full test before any prompt or model change ships.
- Have an expert label the tickets that flip. They become the next examples.

## Cost

*About $10 per 1,000 tickets, and why not something cheaper.*

Measured on all 61 test tickets. The dashboard shows the tickets on screen instead, so its number differs a little.

| Model | Escalations caught | False escalations | Urgency too low | Per 1,000 tickets |
|---|---|---|---|---|
| gpt-5 | 21 of 21 | 1 | 1 (borderline) | $9.68 |
| gpt-5-mini | 21 of 21 | 3 | 3 (all borderline) | $1.82 |
| gpt-5-mini, minimal effort | 21 of 21 | 8 | 2 (all borderline) | $1.30 |
| gpt-5-nano | **19 of 21** | 1 | **9, including 4 clearly critical** | $0.37 |

### Cheap model first, better model second

Cheap model by default, the bigger one only for risky tickets. Two ways, tested on the 33 main tickets:

| Version | Result |
|---|---|
| Keywords pick the model | **38% cheaper.** Risky words go to gpt-5, the rest to mini. One extra false escalation, one urgency call too low. |
| Mini first, gpt-5 re-checks | **29% more expensive.** Risky tickets get paid for twice. |

**Why I haven't switched.** Mini first costs more, so no. Keywords picking the model saves 38%, about $3.50
a month at 1,000 tickets. Not worth the extra mistakes yet.

## Robustness

*Nothing is dropped.*

- **The model times out, errors or is down.** The keyword check reads the ticket and it is marked as such.
  Escalation words still flag it to a person. If the keyword check is not sure of the team, it goes to human
  review.
- **The model returns something that does not fit the format.** The call goes through the OpenAI SDK's
  `responses.parse` with the answer schema (`app/models.py`) attached, so the API is told the exact shape
  and the reply is parsed straight into it. Anything that does not fit raises a validation error.
  `app/pipeline.py` catches that with the API errors, runs the keyword check instead, and records the error
  on the ticket. Tested with a mocked bad answer.
- **The model is unsure of the category.** Under 50% sure, a person decides.
- **The connection drops.** Retried a few times first, because those fail fast and usually recover.

## Testing and accuracy

*Built to find failures, not to pass.*

| Set | What it is for | Result |
|---|---|---|
| 33 main tickets | the 10 from Climb plus 23 edge cases I wrote | every escalation caught, none false; urgency 88% exact, never too low |
| 12 trick tickets | written to break it | no missed escalations; 4 flagged without need, 1 of which gold counts as wrong |
| 6 no-keyword tickets | escalations with none of the keyword words | the model caught all 5 that needed it |
| 10 extraction tickets | names, contacts, account numbers, two traps | 10 of 10 names, 5 of 5 numbers |
| 10 Climb tickets, 5 runs each | does the model repeat itself | see Consistency |

## Going forward

*What I would do next.*

- Real tickets, labelled by people who didn't write the prompt, with a held-back set for testing.
- Keep the keyword check as the fallback. Swap its company-name patterns for a named entity recognition model.
- A scheduled consistency check in production, with an expert reviewing tickets that flip.
- Group tickets by customer once there's a login.

## Who sent it

*Named if the ticket says so, otherwise a clearly marked guess.*

### How we decide

The LLM decides. The keyword check is only a fallback: it runs when the LLM is down and never overrules it.

### The LLM

The name is filled in only when the ticket states it. Anything less is a scored guess:

| Score | What the ticket gave it |
|---|---|
| 0.95 to 1.00 | The company is named. A fact, not a guess. |
| 0.75 to 0.94 | Not named, but a work email domain or account number points to one company. |
| 0.40 to 0.74 | Only the kind of customer: team size, plan, product or job title. |
| 0.10 to 0.39 | Only that they are a customer, from an invoice or account reference. |
| 0.00 | Nothing to go on. It says “not stated”. |

### The keyword check

Runs only if the LLM does not answer. It finds a company in two places:

- **Right after "from", "at" or "on behalf of"**, starting with a capital: "this is Dana *from Acme Logistics*".
- **A sign-off line** starting with a dash: "— Priya Raghavan, *Meridian Health*".

Otherwise it makes a labelled guess. Examples:

| Example | Its guess | Score |
|---|---|---|
| a work email, like `dana@acme.com` | someone at acme.com | 0.8 |
| a team size, like "50 users" | a customer with a sizeable team | 0.5 |
| a plan name, like "Team plan" | a customer on that plan | 0.45 |
| enterprise words, like "workspace" or "Databricks" | an enterprise customer | 0.45 |
| a personal email (gmail, outlook) | an individual user | 0.3 |
| only an invoice or account number | an existing customer | 0.3 |
| nothing | not stated | 0.0 |

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
