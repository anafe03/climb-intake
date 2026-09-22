# Eval scorecard: mode=llm, model=gpt-5-2025-08-07

Generated 2026-09-22 12:37 on 31 gold tickets (10 Climb samples + 21 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy (ambiguity-aware) | 100% |
| Urgency exact / within tolerance | 77% / 97% |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 100% |
| Confidence misses | none |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 15316 ms / 19230 ms |
| Wall time (concurrency 4) | 126.6 s |
| Tokens in / out | 64649 / 45350 |

## Per-ticket

| id | expected | got | esc ok | cat ok | urg ok | queue |
|---|---|---|---|---|---|---|
| climb-01 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-02 | bug/high/- | bug/high/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-03 | security/critical/ESC | security/critical/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| climb-04 | legal_contract/high/ESC | legal_contract/high/ESC [legal_threat] | ✅ | ✅ | ✅ | legal-and-account-management |
| climb-05 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| climb-06 | billing/medium/- | billing/high/-  | ✅ | ✅ | ❌ | billing-support |
| climb-07 | onboarding/high/ESC | onboarding/critical/ESC [executive_mention] | ✅ | ✅ | ✅ | customer-success |
| climb-08 | bug/low/- | bug/low/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-09 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/low/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/low/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-14 | security/high/ESC | security/critical/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-15 | feature_request/medium/- | feature_request/medium/-  | ✅ | ✅ | ✅ | product-feedback |
| edge-16 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-17 | other/low/- | other/low/-  | ✅ | ✅ | ✅ | human-review |
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

## Rationales (model output, verbatim)

**climb-01** — The ticket reports an unexpected $4,200 charge after a claimed downgrade to the Team plan and asks for verification and correction, which clearly places it in billing. The described impact is financial but contained to this customer and without a stated deadline, so medium urgency fits. There are no security, legal, compliance, or executive cues, so no escalation is needed. The customer identity is not stated, but references to a plan and invoice support the best-guess characterization.

**climb-02** — The ticket describes a reproducible server error on an existing feature, so it is a bug. The user tried multiple browsers and the issue has persisted since yesterday, indicating an ongoing problem. The mention of a reporting deadline elevates urgency to high. There are no indicators requiring security, legal, or executive escalation.

**climb-03** — The ticket describes an ex-employee successfully logging in with credentials that should have been revoked, confirmed by audit logs. That makes this a clear security incident, not a general bug or billing issue. The recency and potential for ongoing risk set the urgency to critical. Escalation is required so a human can immediately secure the account and investigate scope and impact.

**climb-04** — The message centers on a disagreement over renewal terms and cites the MSA and breach, making it a legal/contract matter. The stated end-of-week deadline and threat to engage legal increase urgency. No company or individual is named, but the context clearly indicates an existing customer in renewal discussions. Given the explicit legal threat, escalation to a human owner is required.

**climb-05** — The content is clearly unrelated to Climb’s services and lacks any account context, making it spam. The request for “500 free credits” and references to crypto/mining indicate it’s not a legitimate support need. With no deadlines or impact, urgency is low. There are no security, legal, compliance, or executive signals, so no escalation is required.

**climb-06** — The presence of an invoice number, duplicate billing across two months, and a refund request clearly frames this as a billing matter. Financial impact over multiple months raises urgency to high to prevent further overcharges and resolve promptly. There are no indicators of security, data exposure, legal threats, or compliance demands, so no escalation is needed. The sender is unidentified, but context shows they are an existing paying customer with a card on file.

**climb-07** — This is an onboarding progress complaint for an enterprise account, explicitly citing delays and requesting action today. The presence of a CEO and threatened escalation to our leadership triggers executive-mention escalation. The today deadline and executive pressure justify critical urgency. No billing, security, or legal issues are indicated; the substance is implementation progress.

**climb-08** — The ticket describes an existing feature (dark mode) failing to persist, which is a product bug. The user signals low urgency with 'whenever you get a chance' and the issue seems cosmetic and single-user. There are no indicators of security, legal, or executive concerns, so no escalation is needed. Routing to bug handling with low priority is appropriate.

**climb-09** — The ticket describes cross-tenant data appearing in an export, which is a clear security/data exposure event rather than a routine bug. Such incidents can impact multiple customers and may still be occurring, so it is marked critical. Immediate escalation is required to security/incident response. The sender is unidentified, but context indicates they are an existing user performing a data export.

**climb-10** — The customer reports a reproducible checkout defect tied to an order value threshold, resulting in duplicate charges for end customers. This clearly classifies as a product bug rather than a billing question. The issue is ongoing, frequent, and financially harmful, so urgency is critical. There are no indicators of security, data exposure, legal, compliance, or executive issues, so no special escalation is required beyond urgent bug handling.

**edge-11** — The ticket concerns obtaining an invoice copy, which squarely fits billing. There is no urgency signal beyond record-keeping, so it is low priority. Nothing indicates a security, legal, or compliance issue that would require escalation. The customer appears to be an existing paying account, inferred from the request for last month's invoice and a legal department handling vendor records.

**edge-12** — The ticket contains only positive feedback referencing a specific product area, so it routes to 'other' rather than a problem or request category. No urgency is implied because there is nothing to fix or deliver. However, the explicit CEO mention triggers an executive-mention escalation for visibility. No other escalation triggers apply.

**edge-13** — The ticket is a straightforward access issue: the user cannot log in because the password reset email did not arrive and asks for it to be resent. This maps to general support rather than security or billing. It affects a single user with no deadline, so medium urgency is appropriate. The email domain provides a likely organization but no explicit company or contact name was given.

**edge-14** — The message reports brand-impersonation phishing targeting multiple employees with the goal of collecting Climb credentials, which is a clear security incident. The scope (“several of our staff”) and potential for account compromise make it critical. No company name or contact is provided, but context implies an existing organizational customer with multiple users. This should be escalated to security for immediate investigation and remediation steps.

**edge-15** — The substance is a request to increase capacity or add a bulk ingestion option to stop 429s during a nightly sync, which is a feature/limit increase rather than a defect. The issue recurs nightly, creating ongoing impact but without acute deadlines or broad outages, so urgency is medium. No security, legal, or executive cues are present, so no escalation is needed. The sender is unidentified, but context indicates an existing customer integrating with the events API for batch syncing.

**edge-16** — The customer explicitly identifies themselves and provides an account ID, making attribution certain. The substance is an invoice seat-count discrepancy and a request to adjust billing, which fits billing. The upcoming auto-charge date creates a time-bound financial risk, so urgency is high. There are no security, legal, compliance, or executive cues, so no escalation is needed.

**edge-17** — The ticket provides no context beyond 'help', so we cannot identify the sender or the issue. Given the lack of details, it fits 'other' rather than a specific category. With no impact or deadlines mentioned, the urgency is set to low. There are no indicators requiring escalation under security, legal, compliance, data exposure, or executive mention.

**edge-18** — The ticket concerns a duplicate subscription charge and a refund request, placing it squarely in billing. The sender provides no identifying names or numbers, only describing the duplicate August charge. Financial impact justifies medium urgency, but there is no deadline or broader outage. There are no signs of security, legal, compliance, or executive issues, so no escalation is needed.

**edge-19** — The ticket is a clear GDPR Article 17 data deletion request, which places it in legal/compliance rather than security or general support. The mention of a 30-day window and GDPR indicates a statutory deadline, justifying high urgency. Escalation is required due to the compliance nature of the request. The sender does not identify their organization or contact, but the wording implies an existing org-level customer with multiple users.

**edge-20** — The ticket describes a complete dashboard outage impacting all users, which is a product defect, so it is categorized as a bug. The scope and ongoing impact make the urgency critical. There are no signs of security, legal, compliance, or executive issues, so no special escalation is triggered. The sender identifies as an enterprise account, allowing a confident inference that they are an existing enterprise-plan customer.

**edge-21** — The ticket reports repeated invoice totals not matching their plan, which is a billing problem. The recurrence over three months implies ongoing financial harm, so it should be treated with high urgency. There is no indication of security, legal, or compliance issues requiring escalation. Route to billing support to investigate and correct charges and ensure future invoices align with the plan.

**edge-22** — The content is a request to coordinate an executive-to-executive meeting and does not involve billing, bugs, or security. With no deadline and a far-future topic (2027 roadmap), urgency is low. Executive titles on both sides trigger escalation under the executive-mention policy so an appropriate human can schedule. The sender is unnamed, so I inferred only that an engineering leader at a company is initiating the request.

**edge-23** — The message is a system-directed instruction plus a large refund request with no identifiers or product context, which matches spam rather than a customer request. I considered billing due to the refund mention but rejected it because there is no account, invoice, or relationship cited. Urgency is low because no real incident or impact is described. No escalation triggers apply given the absence of unauthorized access, data exposure, legal/compliance demands, or executive involvement.

**edge-24** — The ticket clearly describes an IDOR that exposes other tenants’ data, a severe security issue. This places it in the security category and warrants critical urgency due to ongoing risk and broad scope. No customer identity is provided, so we infer an external security researcher based on the self-description and request for a security contact. Escalation is required for both security incident handling and potential data exposure.

**edge-25** — The message clearly concerns commercial terms: renewal timing and pricing for additional seats, placing it in billing. The scope (50 seats) suggests a meaningful commercial impact but no operational incident, setting urgency to medium. There are no security, legal, or compliance signals, so no escalation is required. The sender’s identity is not stated; context supports that they are an existing contracted customer planning to expand.

**edge-26** — The message is squarely about a duplicate charge and refund, so it routes to billing. The explicit deadline and threat of a bank dispute increase urgency to high. There are no indicators of security, data exposure, formal legal action, or compliance demands, so no escalation is required. The sender is not identified; inference is limited to them being an existing paying customer based on the billing language.

**edge-27** — The phrasing clearly indicates a malfunction in the checkout flow that is double-charging end customers, which fits the bug category. Impact is high and ongoing, justifying critical urgency. There is no mention of unauthorized access, exposure, or legal/compliance aspects, so no escalation per policy. Routing should prioritize an immediate bug investigation for the checkout/payment path.

**edge-28** — The substance is a compliance document request tied to an upcoming renewal, not a product issue or billing dispute. That maps to 'other' per the rubric for compliance docs. The renewal mention raises urgency to medium due to potential commercial impact, but there’s no hard deadline. No escalation triggers are present since it’s not a security incident or legal request with statutory deadlines.

**edge-29** — The message is a clear advertisement for SEO services, not a support request about our product. That places it in spam rather than other categories. With no user impact or deadlines, urgency is low. No escalation triggers (security, data exposure, legal/compliance, executive mention) are present.

**edge-30** — The user is asking for confirmation that a former employee no longer has access, which is a security access control issue. Offboarding language and mention of API keys indicate potential risk if revocation were incomplete, driving high urgency. Given policy, security-related access revocation checks must be escalated. No company or individual names are provided, so identity is inferred only from contextual cues.

**edge-31** — The ticket reports being charged twice for the October subscription and asks to reverse the duplicate, which is a clear billing issue. The sender is identified from the signature as Carlos Mendoza at Grupo Andino. Financial impact exists but is limited in scope and not time-critical, so urgency is medium. There are no indicators that would trigger a security, legal, compliance, data exposure, or executive escalation.
