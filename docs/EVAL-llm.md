# Eval scorecard: mode=llm, model=gpt-5-2025-08-07

Generated 2026-09-22 19:38 on 33 gold tickets (10 Climb samples + 23 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy (ambiguity-aware) | 100% |
| Urgency exact / within tolerance | 88% / 100% |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 88% |
| Confidence misses | ['edge-31 got 0.70, expected [0.9, 1.0]'] |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 15805 ms / 26219 ms |
| Wall time (concurrency 4) | 139.9 s |
| Tokens in / out | 88876 / 54304 |

## Per-ticket

| id | expected | got | esc ok | cat ok | urg ok | queue |
|---|---|---|---|---|---|---|
| climb-01 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-02 | bug/high/- | bug/high/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-03 | security/critical/ESC | security/critical/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| climb-04 | legal_contract/high/ESC | legal_contract/high/ESC [legal_threat] | ✅ | ✅ | ✅ | legal-and-account-management |
| climb-05 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| climb-06 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-07 | onboarding/high/ESC | onboarding/high/ESC [executive_mention] | ✅ | ✅ | ✅ | customer-success |
| climb-08 | bug/low/- | bug/low/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-09 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/low/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/low/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-14 | security/high/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
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
| edge-25 | billing/low/- | billing/low/-  | ✅ | ✅ | ✅ | billing-support |
| edge-26 | billing/high/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-27 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-28 | other/medium/- | legal_contract/medium/-  | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-29 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-30 | security/medium/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-31 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-32 | bug/medium/- | bug/medium/-  | ✅ | ✅ | ✅ | engineering-triage |
| edge-33 | security/high/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — The substance is a charge discrepancy tied to plan level, which is a billing issue. While a backend defect could have caused the wrong plan to be billed, the immediate action requested is an invoice review/adjustment. The impact is monetary but limited to one invoice, so medium urgency fits. No escalation triggers are present.

**climb-02** — The user reports a 500 error in the CSV export feature across multiple browsers, which squarely fits a product bug. The issue has persisted since yesterday and blocks their reporting workflow with a stated deadline, so it is high urgency. There is no hint of access issues, data exposure, or legal/compliance elements, so no escalation is required. Routing to the bug team will address the broken export functionality.

**climb-03** — The report describes unauthorized access by a former employee to the admin console, which is a security incident regardless of whether a revocation bug contributed. The recency ('this morning') and admin-level access signal potential ongoing risk, setting urgency to critical. No company or contact is named, but the context indicates an existing multi-user business customer using audit logs. Escalation is required due to the security nature of the incident.

**climb-04** — This is a contract dispute with an explicit legal threat referencing an MSA, so it should route to legal/contract handling rather than billing. The deadline "by end of week" sets a high urgency. No security or compliance issues are mentioned. Escalation is warranted due to the legal threat.

**climb-05** — The ticket is unrelated to Climb’s product and includes a request for free credits, matching spam patterns. There is no indication of billing, bug, or security concerns. With no deadlines or impact, urgency is low. No escalation triggers are present, so it should be filtered as spam.

**climb-06** — The ticket concerns duplicate billing and a requested refund, which routes to billing. While duplicate charges might originate from a system defect, the customer’s desired action is a refund, not investigation of product behavior, so bug is only a secondary possibility. The financial harm is real but limited in scope and without a deadline, leading to medium urgency. No security, legal, or compliance triggers are present, so no escalation is needed.

**climb-07** — The substance is a delayed onboarding for an enterprise account with an explicit request for progress today. That makes it an onboarding category request with high urgency due to a same-day deadline and executive pressure. It warrants escalation because a CEO and the vendor's leadership team are referenced. No signs of security, billing, legal, or feature needs are present.

**climb-08** — The substance is a straightforward product defect: a saved preference (dark mode) is not retained across refreshes. There is no access, confidentiality, or legal aspect, so it routes to the bug team without escalation. The tone and content indicate low urgency. Sender identity is not provided, so we infer an end user of the web app based on the features mentioned.

**climb-09** — The report describes unauthorized access to another tenant’s customer records during data export, which is a security incident rather than a standard product bug. The recency and nature of the breach make it critical. No company or contact name is provided, but the context implies an existing customer performing exports. Escalation is required for incident handling and to assess and mitigate any ongoing exposure.

**climb-10** — The report describes a systematic defect in the checkout flow causing double charges over a price threshold, clearly a product bug. It affects multiple end customers and is occurring repeatedly today, so urgency is critical due to ongoing financial harm and scope. While it involves charges, it does not concern the customer’s own billing with Climb, so billing is only a secondary consideration. There are no indicators requiring escalation under security, legal, compliance, or executive involvement.

**edge-11** — The customer is requesting a copy of an invoice, which falls under billing. The mention of their legal department is for archiving, not a legal or compliance action. There is no urgency signaled by deadlines or impact, so urgency is low. No escalation triggers are present, as there is no security, data exposure, legal threat, compliance demand, or executive involvement.

**edge-12** — The ticket is a simple compliment about the new reporting view, with no ask or issue, so it routes to Other and is low urgency. The mention of a CEO requires escalation under executive_mention. No security, billing, legal, or feature request elements are present. The sender appears to be an existing customer referencing a specific feature.

**edge-13** — This is an account access problem centered on a password reset, which maps to 'other' per guidance. A bug is conceivable, but the evidence points to a routine reset/deliverability issue for a single user. The inability to log in creates moderate urgency, without deadlines or wide impact. No security, legal, compliance, or executive signals appear, so no escalation is required.

**edge-14** — The ticket describes brand-impersonation phishing targeting user credentials, which is squarely a security incident. The scope (“several staff”) and ongoing nature justify high urgency due to the risk of compromise. This should be escalated to security for rapid takedown and customer advisories. There is no mention of data exposure or legal/compliance demands.

**edge-15** — The user reports recurring 429 responses while calling the Events API during nightly sync and asks for a higher limit or bulk ingestion. That is a request for a limit increase or new endpoint, not a product malfunction. The issue recurs daily and affects their workflow, so medium urgency is appropriate. No escalation triggers (security, legal, compliance, executive) are present.

**edge-16** — The ticket centers on an invoice discrepancy and a request to adjust charges, which places it in billing. The explicit deadline and risk of overcharge create high urgency. There is no mention of access, security, legal, or compliance concerns. Route to billing to adjust the seat count and prevent the incorrect charge before the 30th.

**edge-17** — The content is too sparse to determine a specific area, so it is routed to 'other' with low confidence and common alternatives noted. No urgency signals are present. There are no triggers for security, legal, or executive escalation. A human should request clarification to route appropriately.

**edge-18** — The ticket clearly asks for a refund of a duplicate subscription charge for August, which is a billing matter. There are no indicators of a security, legal, or compliance issue. Urgency is set to medium due to the financial impact but limited scope and lack of deadlines. Customer identity is not provided; we infer they are an existing paying subscriber based on the described duplicate charge.

**edge-19** — The customer is making a GDPR Article 17 erasure request covering their entire organization and its users, which is a compliance matter. That places it in legal/contract rather than security or general support. The explicit 30-day deadline and broad scope set the urgency to high. Because it is a formal compliance request, it should be escalated to ensure privacy/legal teams respond within statutory requirements.

**edge-20** — The customer reports a complete dashboard outage impacting all users, which is a clear product malfunction. There are no signs of unauthorized access or data leakage, ruling out security. The impact is organization-wide and ongoing, making the issue critical. The sender identifies as an enterprise account with many users, but provides no specific company or contact details.

**edge-21** — The ticket centers on invoice totals not aligning with the subscribed plan, which is a billing issue. The repetition over three months indicates ongoing financial impact, warranting high urgency. There are no indicators of security, legal, or compliance concerns. Routing to billing ensures the right team can investigate invoices, plan details, and any credits or adjustments.

**edge-22** — The ticket requests help arranging an executive-to-executive meeting, not reporting a product issue or billing matter, so it fits best under other. While “roadmap” hints at features, no capability is requested. There are no urgency cues like deadlines or impact, so urgency is low. It should be escalated because it names executives on both sides, requiring human coordination.

**edge-23** — The message lacks any customer identity or account details and uses 'SYSTEM OVERRIDE' language, indicating spam or attempted fraud. While it mentions a refund, there is no billing context such as charges, invoices, or account references, so routing to billing would be misleading. There are no indicators of unauthorized access or data exposure. Therefore it is classified as spam, low urgency, and not escalated.

**edge-24** — The ticket reports an IDOR allowing access to other tenants’ data, clearly a security matter rather than a general bug due to the access and confidentiality impact. The sender identifies as a security researcher seeking a disclosure contact, so they are likely an external researcher. Because the flaw is currently exploitable and cross-tenant, it is treated as critical. Escalation is required for security incident handling and potential data exposure.

**edge-25** — This is a straightforward billing request focused on renewal timing and pricing for additional seats. There is no sign of product malfunction, security exposure, or legal/compliance issues. Urgency is low because no timeline or active harm is described; it’s a planning inquiry. The sender appears to be an existing contracted customer seeking to expand by 50 seats.

**edge-26** — The ticket is clearly about a billing error and a refund request, so it routes to billing. While a duplicate charge might originate from a defect, the customer’s immediate need is a refund, making billing the primary path. Urgency is high due to the stated Friday deadline and the risk of a bank dispute. No escalation triggers are present: no security, data exposure, legal threat, compliance deadline, or executive mention.

**edge-27** — The ticket describes an ongoing checkout defect double‑charging end customers, which fits the bug category per guidance. It is not about the sender’s invoices or plan, so billing is a secondary interpretation only. The issue is still happening and affects multiple customers at point-of-sale, creating immediate financial impact, so urgency is critical. No indicators of security, legal, or compliance triggers are present, so no escalation is needed.

**edge-28** — The ticket is a straightforward compliance documentation request tied to a renewal, best handled by the contracts/compliance channel. There is no indication of a security event or legal threat, only the need for SOC 2 paperwork. It blocks renewal but lacks a deadline or ongoing impact, so medium urgency fits. Routing to legal_contract with security as a secondary consideration ensures the right team can supply the report or portal access.

**edge-29** — The ticket is clearly a marketing solicitation for SEO services and not a customer support request. No company or contact is named, and the content is unrelated to our product. Spam is the appropriate category, with low urgency and no need for escalation since none of the escalation triggers apply.

**edge-30** — The request centers on access control and credential revocation, making it a security ticket. The potential for unauthorized access sets a high urgency even without evidence of misuse. No company or contact details were provided, but the presence of API keys and offboarding context indicates an admin of an existing customer account. It warrants escalation to ensure a human confirms and documents revocation.

**edge-31** — The ticket is a straightforward billing issue: a duplicate subscription charge for October and a refund request. There are no security, legal, or compliance elements, so it does not require escalation. Urgency is set to medium due to financial impact limited to a single account without deadlines. Routing to billing with an eye to verify the duplicate and process a refund is appropriate.

**edge-32** — A single analyst is stuck in an SSO login loop while teammates can access normally, indicating a user-specific auth/session issue or integration defect. That fits best as a bug, with 'other' as a plausible alternative if the root cause is purely configuration or provisioning. The impact is limited to one user but ongoing, so urgency is medium. There are no security, legal, compliance, or executive escalation triggers.

**edge-33** — The ticket describes unintended visibility of sensitive internal cost data to all users, including contractors, which is a data exposure. That places it in security rather than a general bug because the harm is unauthorized access. The scope is broad and ongoing since last week, so the urgency is critical. This warrants escalation as a security incident with data exposure for immediate response.
