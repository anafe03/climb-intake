# Eval scorecard: mode=rules

Generated 2026-09-21 10:43 on 30 gold tickets (10 Climb samples + 20 edge cases).

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
| Latency p50 / p95 per ticket | 0 ms / 0 ms |
| Wall time (concurrency 4) | 0.0 s |
| Tokens in / out | 0 / 0 |

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
| climb-09 | security/critical/ESC | security/critical/ESC [data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/medium/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | bug/medium/-  | ✅ | ✅ | ✅ | engineering-triage |
| edge-14 | security/high/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-15 | feature_request/medium/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-16 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-17 | other/low/- | other/medium/-  | ✅ | ✅ | ✅ | general-support |
| edge-18 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-19 | legal_contract/high/ESC | legal_contract/high/ESC [compliance_request] | ✅ | ✅ | ✅ | legal-and-account-management |
| edge-20 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-21 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-22 | other/low/ESC | feature_request/medium/ESC [executive_mention] | ✅ | ✅ | ✅ | product-feedback |
| edge-23 | spam/low/- | billing/high/-  | ✅ | ✅ | ❌ | billing-support |
| edge-24 | security/critical/ESC | security/critical/ESC [security_incident, data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| edge-25 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-26 | billing/high/- | billing/high/-  | ✅ | ✅ | ✅ | billing-support |
| edge-27 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-28 | other/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-29 | spam/low/- | spam/low/-  | ✅ | ✅ | ✅ | spam-review |
| edge-30 | security/medium/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**climb-02** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'high' from cue words. Escalation determined by guardrail regexes.

**climb-03** — Rules-only mode (no model): category 'security' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: security.unauthorized_access forced escalate=true (matched 'credentials'); security.unauthorized_access lifted urgency medium -> critical

**climb-04** — Rules-only mode (no model): category 'legal_contract' by keyword match, urgency 'high' from cue words. Escalation determined by guardrail regexes.
  - overrides: legal.threat forced escalate=true (matched 'legal team')

**climb-05** — Rules-only mode (no model): category 'spam' by keyword match, urgency 'low' from cue words. Escalation determined by guardrail regexes.

**climb-06** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**climb-07** — Rules-only mode (no model): category 'onboarding' by keyword match, urgency 'high' from cue words. Escalation determined by guardrail regexes.
  - overrides: executive.mention forced escalate=true (matched 'CEO')

**climb-08** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'low' from cue words. Escalation determined by guardrail regexes.

**climb-09** — Rules-only mode (no model): category 'security' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: security.data_exposure forced escalate=true (matched 'another company's customer records'); security.data_exposure lifted urgency medium -> critical

**climb-10** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'critical' from cue words. Escalation determined by guardrail regexes.

**edge-11** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-12** — Rules-only mode (no model): category 'other' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: executive.mention forced escalate=true (matched 'CEO')

**edge-13** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-14** — Rules-only mode (no model): category 'security' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: security.unauthorized_access forced escalate=true (matched 'phishing'); security.unauthorized_access lifted urgency medium -> high

**edge-15** — Rules-only mode (no model): category 'other' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-16** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-17** — Rules-only mode (no model): category 'other' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-18** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-19** — Rules-only mode (no model): category 'legal_contract' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: legal.compliance_request forced escalate=true (matched 'GDPR'); legal.compliance_request lifted urgency medium -> high

**edge-20** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'critical' from cue words. Escalation determined by guardrail regexes.

**edge-21** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-22** — Rules-only mode (no model): category 'feature_request' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: executive.mention forced escalate=true (matched 'VP')

**edge-23** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'high' from cue words. Escalation determined by guardrail regexes.

**edge-24** — Rules-only mode (no model): category 'security' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: security.vulnerability_report forced escalate=true (matched 'IDOR'); security.vulnerability_report lifted urgency medium -> high; security.data_exposure lifted urgency high -> critical

**edge-25** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-26** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'high' from cue words. Escalation determined by guardrail regexes.

**edge-27** — Rules-only mode (no model): category 'bug' by keyword match, urgency 'critical' from cue words. Escalation determined by guardrail regexes.

**edge-28** — Rules-only mode (no model): category 'billing' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.

**edge-29** — Rules-only mode (no model): category 'spam' by keyword match, urgency 'low' from cue words. Escalation determined by guardrail regexes.

**edge-30** — Rules-only mode (no model): category 'security' by keyword match, urgency 'medium' from cue words. Escalation determined by guardrail regexes.
  - overrides: security.unauthorized_access forced escalate=true (matched 'offboarded'); security.unauthorized_access lifted urgency medium -> high
