# Eval scorecard: mode=llm, model=gpt-5-2025-08-07

Generated 2026-09-22 10:01 on 30 gold tickets (10 Climb samples + 20 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy (ambiguity-aware) | 100% |
| Urgency exact / within tolerance | 83% / 100% |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 100% |
| Confidence misses | none |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 19354 ms / 29465 ms |
| Wall time (concurrency 4) | 176.2 s |
| Tokens in / out | 62559 / 41773 |

## Per-ticket

| id | expected | got | esc ok | cat ok | urg ok | queue |
|---|---|---|---|---|---|---|
| climb-01 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
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
| edge-25 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-26 | billing/high/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-27 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-28 | other/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-29 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-30 | security/medium/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — The ticket clearly concerns billing: a large unexpected charge after a supposed plan downgrade. There’s no sign of legal or security issues. Given the dollar amount and potential for ongoing incorrect billing, a high urgency is appropriate. Routing to billing will let the team verify the plan change in July and correct or refund the last invoice if needed.

**climb-02** — The user reports a reproducible 500 error on the analytics dashboard's CSV export, indicating a product bug. The issue has persisted since yesterday and blocks reporting due Friday, setting high urgency. There are no signals of security, legal, or compliance concerns, so no escalation is needed. Routing to the bug queue with high priority allows engineering to address a time-sensitive outage affecting reporting.

**climb-03** — The ticket describes unauthorized access by a former employee using credentials that should have been revoked, which is a clear security incident. The timing ('this morning') indicates immediacy and potential ongoing risk, warranting critical urgency. No company or contact is named, but the admin console and audit log references suggest an org admin reporting the issue. Given the nature of the incident, escalation to security response is required to contain and investigate.

**climb-04** — The customer disputes renewal terms against a prior verbal agreement and cites the MSA, indicating a contract issue. The explicit threat to involve their legal team for breach makes this a legal/contract matter that requires escalation. The stated deadline of end of week sets a high urgency. No identifiable names or IDs are provided, but the context indicates an existing enterprise customer in renewal negotiations.

**climb-05** — The message is off-topic, mentions crypto/mining jokingly, and asks for free credits, which fits spam rather than a support request. There is no account context, no product issue, and no urgency indicators. No escalation triggers are present. Route as spam with low urgency.

**climb-06** — The ticket is clearly about being charged twice and seeking a refund, which fits billing. No identities are provided, so names are null; we infer they are an existing customer due to the invoice and card-on-file reference. Urgency is medium because it involves real monetary impact but lacks deadlines or broader scope. No escalation triggers are present since this is not a security, legal, or compliance matter and no executives are mentioned.

**climb-07** — The message centers on delayed onboarding for an enterprise account and requests immediate progress today. No names or identifiers are provided, but the context clearly indicates an existing enterprise customer in onboarding. Urgency is high due to the same-day expectation and CEO involvement. Escalation is required because an executive (their CEO) and our leadership team are explicitly mentioned.

**climb-08** — The content clearly describes malfunctioning behavior of an existing feature, which is a product bug. There is no identification data, so we infer they are a current user based on the UI references. Urgency is low due to the casual request and limited scope to a single user's preference. No escalation triggers are present.

**climb-09** — The ticket describes cross-tenant data exposure during a data export, which is a security incident rather than a generic bug. Such exposure can affect multiple customers and may still be accessible, so it is treated as critical. It should be escalated immediately for security response and containment. The sender is unidentified, but the context shows they are an existing customer actively using the export feature.

**climb-10** — The ticket reports a reproducible defect tied to a price threshold that is double-charging end customers. That is clearly a product bug rather than a billing question about their own account. The issue is ongoing today and affects multiple customers and transactions, making it critical. No indicators of security, data exposure, legal, or compliance concerns are present, so no special escalation is triggered.

**edge-11** — This is a straightforward billing documentation request centered on obtaining an invoice copy. The only legal mention is archival by their legal department, not a dispute or regulatory demand, so it remains billing and does not require escalation. There is no deadline or active impact, so urgency is low. No customer identity details are provided beyond being a paying customer with a legal function.

**edge-12** — The ticket expresses positive feedback about a specific product feature and contains no request or issue, so it fits best under 'other' and is low urgency. It likely comes from an existing customer based on the familiarity with the feature. Because an executive is referenced, it should be escalated per policy for awareness. No security, legal, or billing elements are present.

**edge-13** — The ticket is a routine password reset problem: the user forgot their password and didn't receive the reset email. That fits 'other' over 'bug' since it's a single-user deliverability/access issue. Urgency is medium because access is blocked for one user without broader or financial impact. No escalation triggers are present (no security, data exposure, legal, compliance, or executive mention).

**edge-14** — The user is notifying Climb of phishing emails from a lookalike domain targeting their staff’s Climb credentials, which is a clear security incident. Multiple recipients and credential prompts raise urgency even without a confirmed compromise. This is not a product bug or spam; it is a security matter requiring human follow-up. Escalation is appropriate to coordinate incident response and potential domain takedown.

**edge-15** — The user describes repeated HTTP 429 responses from the Events API during nightly syncs and asks for either a higher limit or a bulk endpoint. That frames the issue as a request to change limits or provide a new ingestion mode, not a defect. The recurrence elevates urgency above low, but absence of deadlines or severe impact keeps it at medium. No escalation triggers are present.

**edge-16** — The customer from Acme Corp reports a mismatch between billed seats and active users and wants the invoice adjusted before auto-charge. This is clearly a billing issue rather than a product bug. The explicit date introduces a deadline and the discrepancy implies financial impact, setting high urgency. No indicators trigger security, legal, compliance, or executive escalation.

**edge-17** — The ticket provides no identifying or contextual information beyond a generic request. Without specifics, it routes as 'other' for triage rather than a domain category like billing or bug. Urgency is set to low due to the absence of deadlines, impact, or severity cues. No escalation criteria are present, so it can be handled in normal support flow with a follow-up for details.

**edge-18** — The user reports being charged twice for their August subscription and asks for a refund, which squarely places this in billing. Financial impact is present but limited to one account with no deadline, so urgency is medium. No escalation triggers are mentioned. Routing to billing/refunds will address the customer's request.

**edge-19** — The ticket asks for GDPR Article 17 data erasure across an entire organization, signaling a regulatory request rather than a product or billing issue. The 30‑day timeline and broad scope raise urgency to high. Because GDPR compliance is involved, it must be escalated to the compliance/legal workflow. The sender is not identified by name, but context indicates an existing organization account subject to GDPR.

**edge-20** — The customer reports a full dashboard outage affecting all of their users since 8am, preventing work. That makes this a product bug/outage with critical urgency due to scope and ongoing impact. They identify themselves as an enterprise account but do not provide names or identifiers, so I inferred the customer type from that statement. There are no cues of security, data exposure, legal, compliance, or executive involvement, so no special escalation is triggered.

**edge-21** — The ticket centers on invoices not matching the subscribed plan, which places it squarely in billing. The customer indicates this has happened three months in a row, implying ongoing overcharge and urgency above routine. There is no mention of security, legal, or compliance factors to trigger escalation. Routing to billing with high urgency best addresses the customer’s issue.

**edge-22** — The ticket is a straightforward scheduling request to arrange an executive-to-executive conversation about long-term roadmap, so it fits best under other rather than a feature request or bug. With no deadline or impact, urgency is low. However, it should be escalated because it involves a VP and our CTO, triggering executive-mention handling. The sender’s organization is not identified; context suggests an enterprise prospect seeking roadmap alignment.

**edge-23** — The ticket contains no identifiable customer details and reads as an attempt to manipulate workflow and force a refund, not a genuine support request. This aligns with spam rather than a billing issue. With no indicators of security, legal, compliance, or executive involvement, no escalation is required. Route as spam with low urgency to prevent action on an illegitimate refund demand.

**edge-24** — The ticket describes an IDOR that allows access to other tenants' account data, making this a clear security incident with data exposure risk. Because the exposure is likely broad and reproducible, urgency is critical. The sender identifies as a security researcher seeking responsible disclosure, so routing to security with escalation is necessary. No company details are provided, so the best available identification is an external researcher reporting a vulnerability.

**edge-25** — The customer is asking about contract renewal and pricing to add seats, which is a billing topic. There is no mention of malfunction or new feature needs, so it is not a bug or feature request. Urgency is set to medium because it impacts commercial planning but lacks a stated deadline or immediate impact. No escalation triggers are present since there are no security, legal, compliance, or executive cues.

**edge-26** — The message centers on a duplicate charge and a refund timeline, which is a straightforward billing issue. The explicit Friday deadline and chargeback threat increase urgency but do not trigger any of the escalation criteria. No names or identifiers are provided, so the customer is inferred only as an existing paying user. Routing to billing with high urgency enables timely refund handling to prevent a bank dispute.

**edge-27** — The report describes duplicate charges during checkout, which is a malfunction in the product rather than a billing question about their account. It is ongoing and impacts payments to the customer's end users, so the urgency is critical. No escalation triggers like security, data exposure, legal/compliance, or executive mentions appear. Route to the bug queue with highest priority for investigation and mitigation.

**edge-28** — The ticket asks for a SOC 2 Type II report needed by procurement to proceed with renewal, indicating an existing customer in a purchasing cycle. This is a compliance documentation request best routed as Other, not Security or Legal/contract. Because the renewal is blocked but no hard deadline is given, medium urgency is appropriate. There are no indicators of security incidents, data exposure, legal threats, regulatory demands, or executive involvement that would trigger escalation.

**edge-29** — The message is pure marketing outreach with phrases like "5-star SEO agency" and "free audit," and lacks any reference to our product, account, or support need. That makes it spam, not a support inquiry. There is no urgency because it poses no operational or financial impact. No escalation triggers apply since there are no security, legal, or executive elements.

**edge-30** — The ticket asks to verify that a departed engineer no longer has access and that API keys are revoked, which is a security access review. This carries elevated risk if not addressed promptly, so urgency is high. It should be escalated under security_incident because it concerns credential and access revocation verification. No evidence suggests data exposure, legal or compliance actions, or executive involvement.
