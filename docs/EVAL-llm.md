# Eval scorecard: mode=llm, model=gpt-5-2025-08-07

Generated 2026-09-24 20:07 on 33 gold tickets (10 Climb samples + 23 edge cases). Scoring re-run over the saved decisions; the model was not called again.

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy: strict / ambiguity-aware | 100% / 100% |
| Urgency exact / within tolerance | 82% / 100% |
| Urgency **under**-called (said calmer than gold) | 0% — none |
| Urgency over-called (said more urgent than gold) | 18% — ['climb-07 said critical, gold high', 'edge-16 said high, gold medium', 'edge-21 said high, gold medium', 'edge-25 said medium, gold low', 'edge-30 said high, gold medium', 'edge-33 said critical, gold high'] |
| Under-calls on tickets gold does NOT mark ambiguous | none |
| Any critical ticket read as less than critical | NO |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 100% |
| Confidence misses | none |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 16059 ms / 20394 ms |
| Wall time (concurrency 4) | not re-run |
| Tokens in / out | 91945 / 28338 |

## Why urgency is reported by direction

Accuracy scores an under-call and an over-call as the same mistake. They are not. This is a
screening test: calling a well patient sick costs a second look, calling a sick patient well
costs the thing the test exists for. An over-called ticket reaches a queue faster than it
needed to and someone downgrades it. An under-called ticket sits.

So the number to read is **under-calls**, and specifically under-calls on tickets the gold set
does *not* mark ambiguous on urgency — the rest are disagreements the gold set already
licenses. The same asymmetry is built into the guardrail layer, which may raise urgency and
never lower it.

## Per-ticket

| id | expected | got | esc ok | cat ok | urg ok | queue |
|---|---|---|---|---|---|---|
| climb-01 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-02 | bug/high/- | bug/high/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-03 | security/critical/ESC | security/critical/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| climb-04 | legal_contract/high/ESC | legal_contract/high/ESC [legal_threat] | ✅ | ✅ | ✅ | legal-and-account-management |
| climb-05 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| climb-06 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-07 | onboarding/high/ESC | onboarding/critical/ESC [executive_mention] | ✅ | ✅ | ✅ | customer-success |
| climb-08 | bug/low/- | bug/low/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-09 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/low/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/low/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-14 | security/high/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-15 | feature_request/medium/- | feature_request/medium/-  | ✅ | ✅ | ✅ | product-feedback |
| edge-16 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-17 | other/low/- | other/low/-  | ✅ | ✅ | ✅ | general-support |
| edge-18 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-19 | legal_contract/high/ESC | legal_contract/high/ESC [compliance_request] | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-20 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-21 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-22 | other/low/ESC | other/low/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-23 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-24 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| edge-25 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-26 | billing/high/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-27 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-28 | other/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-29 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-30 | security/medium/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-31 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-32 | bug/medium/- | bug/medium/-  | ✅ | ✅ | ✅ | engineering-triage |
| edge-33 | security/high/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — The core issue is an unexpected invoice total following a stated plan downgrade, which places it squarely in billing. While a system bug could be the root cause, the immediate action is a billing review and potential credit or correction. The financial amount is meaningful but not urgent to the point of critical, thus medium urgency. No escalation triggers are present.

**climb-02** — The ticket clearly reports a backend error (500) on a specific feature, which is a straightforward product bug. The user has tried multiple browsers, ruling out a simple client-side issue. The stated reporting deadline raises urgency to high. There are no security, legal, or executive signals requiring escalation.

**climb-03** — The ticket reports a former employee logging in after termination, indicating unauthorized access. That makes it a security incident rather than a functional bug, even if a revocation process failed. The recent audit log activity implies current risk, warranting critical urgency. Escalation is required for incident response and containment.

**climb-04** — The message is about a renewal dispute tied to an MSA and includes an explicit legal threat, placing it in legal_contract rather than billing. The 'end of week' deadline and potential legal involvement make it high urgency. No names or identifiers are provided, but context clearly indicates an existing customer in a renewal cycle with an MSA. Escalation is required due to the legal threat.

**climb-05** — The message is unrelated to Climb’s product and requests free credits, suggesting solicitation rather than support. No customer or account details are provided, only a Discord handle. There is no operational impact or time pressure. It should be routed as spam, with no escalation needed.

**climb-06** — The ticket concerns overbilling and a refund, fitting billing rather than bug or other categories. The presence of an invoice number and mention of a card on file indicate an existing paying customer, though the sender is unnamed. Financial impact exists but is limited in scope, so urgency is medium. No signals indicate security, legal, compliance, or executive involvement, so no escalation is needed.

**climb-07** — This is an onboarding progress/escalation request from an enterprise customer whose go-live has stalled for three weeks. The same-day demand and CEO involvement make it critical. Category fits onboarding rather than a bug because no product defect is described, just lack of implementation progress. Escalation is required due to the explicit executive mention and threatened escalation to our leadership.

**climb-08** — The ticket clearly points to a preference state not being saved or read, a typical UI bug. There are no indicators of security, legal, or executive concerns, and the user signals low urgency. Routing to the bug queue with low urgency will get it triaged without escalation.

**climb-09** — The ticket describes unauthorized visibility of another company's records in an export, which is a tenant-boundary breach. That classifies as security, not a generic bug, because the harm is data exposure. Given the recency and potential ongoing risk, urgency is critical. This warrants escalation for security incident handling and data exposure assessment.

**climb-10** — The ticket clearly describes a defect in the checkout logic tied to order amounts over $200, resulting in duplicate charges to end customers and multiple reports today. That places it in the bug category, not billing or security. The impact is ongoing and financial across multiple end customers, so it is critical. No indicators meet the escalation criteria (security, legal, compliance, or executive involvement).

**edge-11** — This is a straightforward billing request to provide a past invoice copy. There is no sign of a dispute or urgency; it is for archiving. Billing handles invoice retrieval; no escalation triggers are present.

**edge-12** — This ticket is a thank-you note about the new reporting view with no request or issue, so it fits best as other. There are no urgency cues, making it low urgency. However, the note cites a CEO, which warrants escalation under executive mention policy. No security, billing, or legal elements are present.

**edge-13** — The ticket describes a routine password reset delivery problem with a single user account. That places it in general support (other), not security, since no unauthorized access or exposure is alleged. The user is currently blocked, warranting medium urgency. Identification is inferred from the email domain, indicating a Brightpath user with an existing Climb account.

**edge-14** — The ticket reports a phishing campaign using a lookalike domain to solicit Climb credentials, which is a security matter. The risk is ongoing and affects multiple users, warranting high urgency and security-team escalation. The sender’s organization is not named, but context indicates an existing customer with multiple staff. No signs of data exposure, legal demand, or executive mention were present, so escalation is solely for a security incident.

**edge-15** — The core ask is to raise rate limits or provide a bulk endpoint, which fits feature_request over bug because 429 responses indicate standard throttling. The issue recurs nightly and affects their workflow, warranting medium urgency without an immediate outage or deadline. No security or legal elements are present, so no escalation is needed. The sender is an existing API user managing a nightly sync job.

**edge-16** — The ticket concerns an invoice discrepancy tied to seat counts, which is a billing matter. The customer provides account identification and a deadline before auto-charge, increasing urgency. There is no mention of unauthorized access or legal/compliance issues, so no escalation is needed. Routing to billing with high urgency enables correction before the 30th.

**edge-17** — The ticket provides no specifics, just a request for help, so it is routed as 'other' rather than spam. There are no cues to place it in billing, bug, security, legal, onboarding, or feature request. With no impact or deadlines, urgency is low. No escalation triggers are present.

**edge-18** — The ticket clearly states they were charged twice for August and asks for a refund, placing it in billing. There is no mention of product malfunction or access issues. Financial impact is present but limited in scope and urgency, so medium urgency is appropriate. No escalation triggers are present.

**edge-19** — The ticket is a clear GDPR erasure request, which routes to legal/compliance rather than support engineering. The presence of a 30-day statutory window makes it time-sensitive. There is no indication of security breach, data exposure, or billing issues. Escalation is required due to the regulatory nature of the request.

**edge-20** — The ticket describes a platform outage impacting all users, which fits a product bug rather than a security event. The scope and ongoing nature set the urgency to critical. No names or identifiers are provided, but they identify as an enterprise account with many users. Escalation isn’t triggered under the listed criteria because there’s no security, data exposure, legal, or executive component.

**edge-21** — The ticket centers on invoices not matching the subscribed plan, which fits billing. While a backend defect could be the root cause, the customer is seeking correction of charges, so billing should triage first. The recurrence and financial impact justify high urgency. There are no indicators requiring security, legal, compliance, or executive escalation.

**edge-22** — The ticket asks for help arranging an executive-to-executive meeting, which fits 'other' rather than feature_request or onboarding. No product malfunction, billing, or security concern is raised. Urgency is low because there is no time constraint or business impact described. However, it should be escalated due to explicit executive involvement.

**edge-23** — The ticket is an instruction to bypass normal processes and refund money, with no identifiers or problem description. The phrasing strongly suggests spam or social engineering rather than a genuine customer request. Classified as spam with high confidence; billing was considered only due to the word 'refund'. Low urgency and no escalation since there is no evidence of unauthorized access, data exposure, or legal/compliance triggers.

**edge-24** — The ticket reports an IDOR that allows viewing other tenants' data, which is a security incident with possible data exposure. The sender identifies as a security researcher seeking a disclosure contact, reinforcing that this is a security matter. Urgency is high due to ongoing risk and potential multi-tenant impact, though no active exploitation is claimed. Escalation is required for security incident handling and data exposure evaluation.
  - overrides: security.data_exposure lifted urgency high -> critical

**edge-25** — The request concerns renewal timing and pricing for more seats, aligning with billing rather than product or onboarding. Scope (50 seats) suggests material financial impact but no urgency cues or service disruption. No security, legal, or compliance elements are present, so no escalation is needed. Route to billing/sales support to provide renewal details and a quote.

**edge-26** — The ticket centers on a duplicate charge and refund timing, fitting billing. While the duplicate could hint at a defect, the customer’s ask is a refund, not debugging. The explicit Friday deadline and risk of a bank dispute raise urgency to high. No security, legal, or compliance triggers are present, so no escalation.

**edge-27** — The ticket clearly points to a duplicate-charge defect in the checkout flow affecting multiple end customers and still occurring. That makes it a product bug rather than a billing issue with our invoices. The ongoing nature and financial impact set the urgency to critical. No security, legal, or compliance triggers are present, so it does not require escalation beyond urgent bug handling.

**edge-28** — The ticket asks for a SOC 2 Type II report, a typical compliance document provided during renewals, which falls under 'other' per the guidelines. The procurement and renewal context implies moderate urgency. There is no indication of security breach, legal dispute, or statutory demand requiring escalation. Routing should go to the team that handles security/compliance documentation distribution.

**edge-29** — The message is a classic cold sales pitch for SEO services and does not pertain to product use, issues, billing, or features. That makes it spam rather than a support need. There is no urgency or escalation trigger present. Route to spam handling.

**edge-30** — The request is about verifying revocation of user access and API credentials, which is squarely a security topic. There is no sign of billing, bugs, or legal issues. The lack of a named company means we infer only that they are an existing org using the API. Given the potential risk if revocation is incomplete, urgency is high. It should be escalated as a security access-revocation check.

**edge-31** — The customer reports being billed twice for the October subscription and asks for the duplicate to be reversed, which is a billing matter. While duplicate charges could arise from a system issue, the user is not reporting a product defect—only seeking a refund—so billing is primary. The financial impact makes this more than low urgency, but with no deadline or broad scope it fits as medium. No escalation triggers are present.

**edge-32** — The report describes an SSO login loop affecting a single user, indicating a product or configuration bug rather than a security incident. Since other team members can log in, scope is limited and suggests user-specific mapping/provisioning or session issue. Urgency is medium due to ongoing blockage for one analyst without broader impact or deadlines. No escalation triggers are present.

**edge-33** — The ticket describes unintended broad access to sensitive data, making this a security issue rather than a general bug. The scope includes all workspace users and contractors, implying serious and ongoing exposure, so urgency is critical. No customer identity is provided, but context indicates an existing customer admin managing permissions. This must be escalated for security incident response and data exposure handling.
