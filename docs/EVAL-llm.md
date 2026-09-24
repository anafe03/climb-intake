# Eval scorecard: mode=llm, model=gpt-5-mini-2025-08-07

Generated 2026-09-24 11:16 on 33 gold tickets (10 Climb samples + 23 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy (ambiguity-aware) | 100% |
| Urgency exact / within tolerance | 76% / 100% |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 88% |
| Confidence misses | ['edge-29 got 0.20, expected [0.3, 1.0]'] |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 15096 ms / 18514 ms |
| Wall time (concurrency 4) | 131.0 s |
| Tokens in / out | 91945 / 50513 |

## Per-ticket

| id | expected | got | esc ok | cat ok | urg ok | queue |
|---|---|---|---|---|---|---|
| climb-01 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-02 | bug/high/- | bug/high/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-03 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-04 | legal_contract/high/ESC | legal_contract/high/ESC [legal_threat] | ✅ | ✅ | ✅ | legal-and-account-management |
| climb-05 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| climb-06 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| climb-07 | onboarding/high/ESC | onboarding/critical/ESC [executive_mention] | ✅ | ✅ | ✅ | customer-success |
| climb-08 | bug/low/- | bug/low/-  | ✅ | ✅ | ✅ | engineering-triage |
| climb-09 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/low/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/low/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | other/low/-  | ✅ | ✅ | ✅ | general-support |
| edge-14 | security/high/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-15 | feature_request/medium/- | feature_request/medium/-  | ✅ | ✅ | ✅ | product-feedback |
| edge-16 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-17 | other/low/- | other/low/-  | ✅ | ✅ | ✅ | general-support |
| edge-18 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-19 | legal_contract/high/ESC | legal_contract/high/ESC [compliance_request] | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-20 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-21 | billing/medium/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-22 | other/low/ESC | other/medium/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-23 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-24 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| edge-25 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-26 | billing/high/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-27 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-28 | other/medium/- | legal_contract/medium/-  | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-29 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-30 | security/medium/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-31 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-32 | bug/medium/- | bug/medium/-  | ✅ | ✅ | ✅ | engineering-triage |
| edge-33 | security/high/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — The message explicitly references an invoice amount and a past downgrade to the Team plan and asks for a check/adjustment, which is a billing issue. No account identifiers or company name are given, so I inferred an existing paying customer based on the plan and invoice language (moderate confidence). The amount is significant enough to be medium urgency but there are no signs of security, legal, or compliance concerns, so no escalation is needed.

**climb-02** — The ticket describes a reproducible 500 server error on a named product surface, so it's routed as a bug. There is no identifying customer information, so I provided a scored best guess that they're an existing production user based on the dashboard and deadline references. Urgency is set to high because the issue is ongoing and blocks an imminent reporting deadline. No escalation was raised because there are no signs of data exposure, unauthorized access, legal, compliance, or executive involvement.

**climb-03** — The ticket reports a former employee gaining access to the admin console and recent audit log activity, which is an access-control/security issue rather than just a functional bug. Because the access appears recent and could expose data or allow admin actions, this should be treated as a critical security incident and escalated for immediate investigation and remediation. The identification as an existing customer admin is inferred from the product surface and wording, though no company or contact is named.

**climb-04** — The ticket centers on renewal terms and explicitly threatens legal review and MSA breach, so it should be routed to legal/contract specialists. Billing is related because renewal terms can affect charges, but the explicit legal threat and contract language make legal_contract the primary category. The deadline and threat raise the urgency to high and require escalation to legal.

**climb-05** — The ticket is a short, informal message requesting free credits and making a joking claim about Climb mining crypto, with no account details or legitimate support need. That pattern matches spam/solicitations rather than billing, security, or product issues. No signs of harm, deadlines, or account identifiers mean low urgency and no escalation.

**climb-06** — The message explicitly requests a refund for a duplicate charge on a named invoice and references the card on file, which makes this a billing issue for an existing paying account. I inferred the sender is an account holder from the invoice and payment language. While a technical billing bug might have caused the duplicate charge, the customer's immediate need is a refund rather than a vulnerability or access incident, so route to billing with medium urgency and no escalation.

**climb-07** — The message is an urgent escalation about an ongoing onboarding that has not completed after three weeks and includes a same-day deadline and CEO involvement. That makes the correct routing to onboarding with a critical urgency and immediate human escalation to account/leadership. There is no mention of a security issue, data exposure, or legal contract, so those were not selected.

**climb-08** — The report describes a UI state persistence problem (dark mode resetting on refresh), which is a clear product bug. It is cosmetic and appears single-user in scope, so urgency is low and no escalation is needed. Route to the frontend/product bug team to investigate preference persistence (local storage, cookies, or server-side setting).

**climb-09** — The ticket reports that exported data included another company's customer records, which is an access/ confidentiality failure rather than a purely functional bug. Because the harm is exposure of other customers' data and it appears recent/ongoing ("this morning"), this should be treated as a critical security incident and escalated to incident response right away. There are no identifying details in the message, so the sender is inferred to be an existing customer who performed the export.

**climb-10** — The ticket describes a reproducible functional defect in the checkout that is causing duplicate charges and is actively affecting multiple customers. That makes this a product bug with significant financial impact, not a security or legal issue. The recurrence and multiple affected customers justify critical urgency; billing is a plausible alternative classification because money is involved, but the language points to a defect that engineering must fix.

**edge-11** — This is a straightforward billing routing request: they want an invoice copy sent to legal for records. There are no identifiers (invoice number, account name, or contact email) in the message, so the team will need to locate the invoice by the sender's account or ask for an account/invoice reference. No signs of a dispute, exposure, or regulatory/legal urgency were found, so no escalation is required.

**edge-12** — The ticket is a short thank-you note with no actionable request, so it does not fit billing, bug, security, or legal categories and is routed to 'other'. It is low urgency because there is no problem or deadline. However, because the sender references their CEO, this triggers an executive-level escalation so account or customer success should be notified.

**edge-13** — The user explicitly provided the login email, so I identified them by that address. The request is a straightforward password-reset support task, which fits 'other' rather than billing, legal, or feature request. While the missing reset email could indicate an email-delivery bug, there's no evidence of a wider outage or security issue, so I deprioritized 'bug' and did not escalate. Urgency is low because the report affects a single user with no stated deadline or broader impact.

**edge-14** — The message describes an ongoing phishing attempt that targets Climb credentials and impersonates the brand, which constitutes a security incident and needs Security team action. The sender gives no account identifiers, but the wording "our staff" suggests an account admin reporting on behalf of their organization, so I inferred the customer as an existing Climb customer (confidence 0.5). Because multiple staff were targeted and passwords were requested, urgency is high and escalation to Security is warranted; no evidence of data exposure or legal/compliance demands was provided.

**edge-15** — This is primarily a request to increase quota or provide a bulk API (feature_request) because the user asks specifically to 'raise our rate limit or get a bulk endpoint.' The message names the product surface ('events API') and a recurring scheduled job ('nightly sync around 2am'), which supports identifying them as an integration user. The issue is recurring so urgency is medium, but there is no sign of data exposure, legal threat, or executive involvement, so no escalation is required.

**edge-16** — The ticket explicitly names the company and account and requests an invoice correction ahead of a scheduled card charge, which is a billing concern. The presence of a seat count discrepancy could indicate an underlying product issue, but the immediate customer need is to adjust the invoice/payment. No signs of security, legal, or compliance concerns were present, and the payment deadline makes this high urgency.

**edge-17** — The ticket contains no substantive information to identify the customer or the problem, so it is routed as 'other' pending clarification. Onboarding and bug were considered because a short plea for help could be either, but the absence of any product, account, error, or billing language prevents confident classification. No urgency or escalation markers are present, so treat this as a low-priority request that needs a human follow-up to get details.

**edge-18** — The ticket plainly asks for a refund of a duplicate August subscription charge, which fits billing. There is no identifying account information provided, so I infer they are an existing paying subscriber from the wording. The issue should be routed to billing/payments for refund processing; if billing finds a system fault causing the duplicate charge, they can escalate to engineering as a bug.

**edge-19** — The message explicitly cites GDPR Article 17 and asks for deletion "of all personal data you hold for our organization and its users within 30 days," which is a regulatory compliance demand. That places it in legal/compliance rather than bug or security. The statutory deadline and legal phrasing justify escalating to the compliance/privacy/legal team and marking the urgency as high.

**edge-20** — The ticket describes an active, organization-wide outage of a product dashboard, which is a functional availability issue routed to the bug/operations team. It is high-impact and ongoing, so it is marked critical. There are no indications of unauthorized access, data leakage, legal or compliance demands, so this is not escalated to security or legal based on the information given.

**edge-21** — The ticket explicitly describes an invoice and plan mismatch over multiple months, which is a billing/invoicing problem. There is no company or account identifier provided, so I inferred they are an existing paying customer from the language but scored that inference modestly. The issue is ongoing and financially impactful, so it should be handled by billing with high priority; if an engineering root cause is found, billing can route to engineering as needed.

**edge-22** — The message is a straightforward request to arrange an executive-level meeting and contains no technical, billing, or legal content, so it routes to Other. Because a VP is explicitly named and they request our CTO, this should be escalated to the appropriate executive/sales/partnership contact for coordination. Urgency is medium because leadership involvement increases priority despite no stated deadline. Customer identity is not provided, so I inferred an external organization represented by a VP with low confidence and listed the textual cues used.

**edge-23** — The ticket is an unauthenticated command with no identifying or billing information and matches common patterns of spam or social-engineering attempts. While it mentions a refund (billing), it provides no invoice/account context or authorization, so routing to billing is not appropriate. No indicators of a real security incident, data exposure, legal threat, or executive escalation are present, so it should be handled as spam with low urgency.

**edge-24** — The reporter explicitly self-identifies as a security researcher and describes an IDOR that returns other tenants' data. That describes unauthorized access/data exposure rather than a purely functional bug, so the ticket should route to security and incident response. The report requests a security contact and thus needs prompt escalation and a responsible-disclosure workflow.

**edge-25** — This is a straightforward billing inquiry: the customer asks about renewal timing and wants pricing for additional seats. The language and seat count indicate an existing paying account, so route to billing/sales for a renewal date and a quote. There are no signs of legal dispute, security, or product malfunction, so no escalation is required.

**edge-26** — The message is a straightforward billing dispute: it asks for a refund and sets a deadline with a bank dispute threat, which makes it time-sensitive. No identifying account information or contract/litigation language is present, so route to billing support for a refund and quick response. I did not escalate because there is no indication of a security incident, data exposure, regulated compliance demand, or legal/attorney involvement.

**edge-27** — The ticket describes an ongoing, production checkout failure causing customers to be billed twice, which is best handled as a product bug because it is a defect in the payment/checkout flow resulting in incorrect charges. Because it is actively impacting end customers and causing financial harm, the incident is high-severity and should be prioritized for engineering and payments teams; billing teams may need to process refunds once the root cause is identified. No identifiers or account info were supplied, so the sender is inferred to be a merchant but must be identified by the triage team before remediation.

**edge-28** — The ticket is a straightforward request for compliance documentation from a procurement contact ahead of contract renewal, which maps to legal/contract/compliance handling. There is no indication of a security incident, data exposure, or legal threat, so it does not need security or legal escalation. The request blocks renewal (financial impact) but lacks a deadline, so medium urgency is appropriate.

**edge-29** — The ticket is a brief promotional message with no identifying account information or product context, so it should be routed as spam. It poses no operational, security, or legal concern based on its content, and there is no urgency. A human escalation is unnecessary because no sensitive data, access issue, or executive/legal mention appears.

**edge-30** — The ticket explicitly requests confirmation that an offboarded engineer's access and API keys were revoked, which is a security-sensitive action. There is no company or contact named, but the language indicates an account administrator from a customer. Because credentials and potential unauthorized access are involved, route to security, mark as high urgency, and escalate so the security team can verify revocation and audit.

**edge-31** — The ticket explicitly describes a duplicate subscription charge and asks for reversal, which fits squarely into billing (refunds/charges). The sender and company are named verbatim, so identification is certain. There is financial impact, so the priority is medium, but no signs of broader system compromise or legal/compliance issues that would require escalation.

**edge-32** — The ticket reports an SSO authentication failure affecting a single user. Because the harm described is inability to access (a functional failure) rather than unauthorized access or data leakage, this routes to engineering as a bug. It's medium urgency since it blocks that analyst but doesn't affect the whole team or indicate broader exposure, and there are no signs requiring security, legal, or executive escalation.

**edge-33** — The ticket describes unauthorized visibility of sensitive data following a permissions change, which is the defining feature of a security incident rather than a simple product bug. The scope includes all workspace users and external contractors, indicating broad and potentially ongoing exposure, so the issue is routed as critical and escalated to security and incident response. The sender appears to be a workspace admin based on the language used, though no account or contact is named.
