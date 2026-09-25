# Eval scorecard: mode=llm, model=gpt-5-2025-08-07

Generated 2026-09-25 12:46 on 33 gold tickets (10 Climb samples + 23 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy: strict / ambiguity-aware | 97% / 100% |
| Urgency exact / within tolerance | 88% / 100% |
| Urgency **under**-called (said calmer than gold) | 0% — none |
| Urgency over-called (said more urgent than gold) | 12% — ['edge-16 said high, gold medium', 'edge-22 said medium, gold low', 'edge-30 said high, gold medium', 'edge-33 said critical, gold high'] |
| Under-calls on tickets gold does NOT mark ambiguous | none |
| Any critical ticket read as less than critical | NO |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 100% |
| Confidence misses | none |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 9787 ms / 12874 ms |
| Wall time (concurrency 4) | 84.5 s |
| Tokens in / out | 108808 / 28458 |

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
| edge-17 | other/low/- | other/low/-  | ✅ | ✅ | ✅ | general-support |
| edge-18 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-19 | legal_contract/high/ESC | legal_contract/high/ESC [compliance_request] | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-20 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-21 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-22 | other/low/ESC | other/medium/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
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

**climb-01** — The ticket concerns an unexpected $4,200 charge following a claimed plan downgrade, which squarely falls under billing. While a product bug could have caused the mismatch, the customer's ask is to verify and correct the invoice. Urgency is medium due to financial impact without a deadline or ongoing outage. No escalation triggers are present.

**climb-02** — The ticket reports a consistent 500 error on CSV export across browsers, indicating a product bug. No access or confidentiality issues are raised, so it is not a security matter. The stated reporting deadline elevates urgency to high. No escalation triggers are present.

**climb-03** — The ticket reports a terminated user logging in and generating audit-log events, which is a clear security incident. That sets the category and justifies escalation. The timing ('this morning') and nature of the access make the urgency critical. The sender is not named, but references to the admin console and audit logs indicate an existing enterprise admin contacting support.

**climb-04** — The ticket centers on a dispute over renewal terms with an explicit threat to involve legal and review the MSA, which makes it a legal/contract issue rather than billing. The presence of a firm end-of-week deadline sets a high urgency. No identifying names are provided, but references to an MSA, a sales rep, and a prior call indicate an existing customer approaching renewal. Legal threat requires escalation.

**climb-05** — The ticket is unrelated to Climb’s product and solicits free credits, matching the spam category. There is no identified customer or account and no actionable product, billing, or security issue. With no urgency or escalation triggers, it should be filtered as spam.

**climb-06** — The ticket concerns duplicate billing on a specific invoice and asks for a refund, placing it in billing rather than bug. Identity is not provided, so only an inferred description of the sender is possible. Urgency is medium due to financial impact without deadlines or ongoing incident. No escalation triggers are present.

**climb-07** — The message centers on delayed onboarding for an enterprise account and asks for immediate movement, so it routes to onboarding. The same-day expectation and CEO pressure set the urgency to high. Executive involvement requires escalation under the executive-mention rule. No indicators of billing, bug, security, legal, or feature request are present.

**climb-08** — The ticket describes a UI setting that resets on refresh, which is classic state persistence bug behavior. There's no access or data exposure component, so it's not security. The user explicitly signals low urgency. With no identifiers or names, the sender is inferred as a regular web app user reporting a minor defect.

**climb-09** — The ticket describes unauthorized visibility of another tenant’s records, which is a security incident, not a generic bug. The event happened this morning and could still be affecting exports, so urgency is critical. No sender identity is provided, so only a contextual best guess is possible. Due to confirmed exposure, immediate escalation is required for containment and investigation.

**climb-10** — The ticket describes a malfunction in checkout leading to duplicate charges, which is a product bug rather than a billing question. The impact is immediate and broad (pattern-based over $200, multiple occurrences and complaints), so urgency is critical. No cues indicate security, legal, compliance, or executive involvement, so no escalation under those paths. Customer identity is not stated; context indicates an active ecommerce merchant on our platform.

**edge-11** — The content focuses on receiving a prior invoice copy, which is a billing action. There is no urgency or impact described beyond record-keeping, so urgency is low. Nothing triggers escalation since there is no security, legal threat, or compliance demand. The sender is unidentified beyond being an existing customer with invoices.

**edge-12** — The ticket contains only product-related praise, so it fits 'other' rather than a support or feature category. No urgency applies because no action is requested. It should be escalated solely due to the CEO mention per policy. The sender is unidentified beyond being an existing user offering feedback.

**edge-13** — The ticket centers on a missing password reset email for a single user account. That places it under general account assistance (other), with bug as a plausible alternative if deliverability is failing system-wide. Urgency is medium because the user is blocked but there is no broader impact or deadline. No escalation triggers are present.

**edge-14** — The content clearly describes a phishing attempt involving credential harvesting, which is a security issue. Multiple staff were targeted, increasing urgency even without confirmed compromise. Escalation is necessary for a security response and brand abuse handling. No billing, bug, legal, or onboarding aspects are present.

**edge-15** — The ticket is about throughput limits on the Events API and asks for a limit increase or bulk capability, which fits feature_request better than bug. The sender appears to be an existing technical user running a nightly job. Urgency is medium due to recurring impact without a stated deadline or outage. No escalation triggers are present.

**edge-16** — The sender identifies as Dana from Acme Corp with account #A-1002. The substance is an invoice/seat-count billing correction, not a product failure. Urgency is driven by the explicit deadline and impending charge. None of the escalation triggers apply.

**edge-17** — The ticket provides no identifying or contextual information beyond 'help', so customer identification is not possible. With no product, billing, or security specifics, it routes to other as a generic inquiry, acknowledging spam as a secondary possibility. No urgency signals or escalation triggers are present.

**edge-18** — The ticket clearly describes a duplicate subscription charge and asks for a refund, which routes to billing. While a product defect could be the root cause, the immediate action sought is a billing correction. The scope is one customer and a past period with no urgent deadline, so medium urgency. No escalation triggers are present.

**edge-19** — The ticket invokes GDPR Article 17 and asks for deletion of all personal data for an organization and its users, which places it squarely in legal/compliance. The 30-day statutory deadline sets urgency to high. Escalation is required as a compliance request so legal/privacy can verify scope, identity, and fulfillment timelines.

**edge-20** — The ticket describes a product outage blocking all users on an enterprise account, which is a product bug rather than a security event. The scope and ongoing nature make it critical. No names or identifiers are provided, so the customer is inferred from context. None of the escalation triggers are present.

**edge-21** — The ticket clearly concerns billing: an invoice/plan mismatch. While a pricing calculation bug is possible, the immediate action is a billing review and correction. Urgency is set to medium due to ongoing financial impact without a stated deadline or broader scope. No escalation triggers are present.

**edge-22** — The ticket contains no company identifiers, only an executive meeting request about the roadmap, so it falls under 'other' rather than a feature request. There is no incident or deadline driving urgency, but executive involvement raises priority to medium. It should be escalated due to explicit executive mentions for appropriate coordination.

**edge-23** — The ticket contains system-override language and a large refund request without any identifying information or product reference, which fits spam. There is no evidence of a real billing issue or security matter. Per policy, spam is low urgency and does not require escalation.

**edge-24** — The ticket clearly describes unauthorized access to other tenants' data through predictable IDs, which is a security incident, not a functional bug. Such cross-tenant exposure is high-severity and likely ongoing, so urgency is critical. The sender does not identify a company or person, so only an inferred profile is provided. Escalation is necessary for security handling and potential data exposure.

**edge-25** — The ticket concerns contract renewal timing and pricing for more seats, which is squarely billing. No urgency cues or active impact are present, so urgency is low. There are no security, legal, or compliance elements to escalate. The sender is unidentified, but phrasing indicates an existing contracted customer planning a 50-seat expansion.

**edge-26** — The message centers on a duplicate charge and refund timing, which squarely places it in billing. While duplicate charges could be caused by a defect, the customer’s ask is for a refund, not troubleshooting. The explicit Friday deadline and financial harm make the issue high urgency. No escalation triggers are present.

**edge-27** — The report describes duplicate charges during checkout, which is a functional defect impacting end customers, fitting the bug category rather than billing or security. The issue is ongoing and potentially widespread across transactions, so urgency is critical. No escalation triggers are present: no unauthorized access, data exposure, legal threat, compliance deadline, or executive mention.

**edge-28** — The ticket requests a SOC 2 Type II report for procurement prior to renewal, indicating a compliance/contract context. That places it under legal_contract rather than a general inquiry. Urgency is medium because renewal depends on it but no deadline is stated. No escalation triggers are present since this is a standard document request without incident or statutory demand.

**edge-29** — The ticket content is a pure marketing solicitation unrelated to support. That places it in spam with high confidence. There is no urgency or escalation criterion triggered since no security, legal, or compliance elements are present.

**edge-30** — The ticket concerns access control and credential revocation after an employee departure, which places it in security. While no breach is claimed, the risk is ongoing until confirmed. Urgency is high because lingering access could allow unauthorized use. Escalation is required as an access-revocation/security incident.

**edge-31** — El ticket describe un cobro doble y solicita la reversión, encajando en facturación. Aunque podría originarse en un fallo del sistema, el objetivo inmediato es el reembolso/ajuste. La urgencia es media por el impacto financiero acotado y sin plazos. No aplica ninguna de las condiciones de escalación.

**edge-32** — The ticket describes an SSO loop affecting a single authorized user, which is a product/login bug rather than a security incident. Impact is ongoing but scoped to one person, setting urgency to medium. There are no escalation triggers like exposure, legal, compliance, or executive mentions. Routing to the bug team is appropriate.

**edge-33** — The ticket describes broad, potentially ongoing access to sensitive data by unintended users, which is a security incident and data exposure. No identities are provided, so company and contact remain null, with a contextual best guess based on the workspace and contractor references. The severity and scope justify critical urgency and escalation to the security response team. While a permissions bug may be involved, the routing should be to security due to the nature of the harm.
