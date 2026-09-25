# Eval scorecard: mode=rules

Generated 2026-09-24 20:07 on 33 gold tickets (10 Climb samples + 23 edge cases).

| Metric | Value |
|---|---|
| Escalation recall (must-escalate tickets caught) | **100%** |
| Missed escalations | none |
| False escalations (not tolerated by gold) | none |
| Escalation reason accuracy | 100% |
| Category accuracy: strict / ambiguity-aware | 82% / 100% |
| Urgency exact / within tolerance | 76% / 97% |
| Urgency **under**-called (said calmer than gold) | 0% — none |
| Urgency over-called (said more urgent than gold) | 24% — ['edge-11 said medium, gold low', 'edge-12 said medium, gold low', 'edge-17 said medium, gold low', 'edge-22 said medium, gold low', 'edge-23 said high, gold low', 'edge-25 said medium, gold low', 'edge-30 said high, gold medium', 'edge-33 said critical, gold high'] |
| Under-calls on tickets gold does NOT mark ambiguous | none |
| Any critical ticket read as less than critical | NO |
| Customer name accuracy (incl. correctly null) | 100% |
| Identifier extraction | 100% |
| Overclaimed sender confidence (safety: must be none) | none |
| Sender-inference confidence within expected band | 100% |
| Confidence misses | none |
| Every guess carries its basis | yes |
| Latency p50 / p95 per ticket | 0 ms / 12 ms |
| Wall time (concurrency 4) | 0.0 s |
| Tokens in / out | 0 / 0 |

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
| climb-09 | security/critical/ESC | security/critical/ESC [data_exposure] | ✅ | ✅ | ✅ | security-incident-response |
| climb-10 | bug/critical/- | bug/critical/-  | ✅ | ✅ | ✅ | engineering-oncall |
| edge-11 | billing/low/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-12 | other/low/ESC | other/medium/ESC [executive_mention] | ✅ | ✅ | ✅ | general-support |
| edge-13 | other/medium/- | bug/medium/-  | ✅ | ✅ | ✅ | engineering-triage |
| edge-14 | security/high/ESC | security/high/ESC [security_incident] | ✅ | ✅ | ✅ | security-incident-response |
| edge-15 | feature_request/medium/- | other/medium/-  | ✅ | ✅ | ✅ | human-review |
| edge-16 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-17 | other/low/- | other/medium/-  | ✅ | ✅ | ✅ | human-review |
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
| edge-31 | billing/medium/- | billing/medium/-  | ✅ | ✅ | ✅ | billing-support |
| edge-32 | bug/medium/- | other/medium/-  | ✅ | ✅ | ✅ | human-review |
| edge-33 | security/high/ESC | security/critical/ESC [data_exposure] | ✅ | ✅ | ✅ | security-incident-response |

## Rationales (model output, verbatim)

**climb-01** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**climb-02** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'high'. Escalation is decided by the guardrail layer.

**climb-03** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.unauthorized_access forced escalate=true (matched 'credentials'); security.unauthorized_access lifted urgency medium -> critical

**climb-04** — Keyword-rules mode (no model available): category 'legal_contract' by cue words, urgency 'high'. Escalation is decided by the guardrail layer.
  - overrides: legal.threat forced escalate=true (matched 'legal team')

**climb-05** — Keyword-rules mode (no model available): category 'spam' by cue words, urgency 'low'. Escalation is decided by the guardrail layer.

**climb-06** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**climb-07** — Keyword-rules mode (no model available): category 'onboarding' by cue words, urgency 'high'. Escalation is decided by the guardrail layer.
  - overrides: executive.mention forced escalate=true (matched 'CEO')

**climb-08** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'low'. Escalation is decided by the guardrail layer.

**climb-09** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.data_exposure forced escalate=true (matched 'another company's customer records'); security.data_exposure lifted urgency medium -> critical

**climb-10** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'critical'. Escalation is decided by the guardrail layer.

**edge-11** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-12** — Keyword-rules mode (no model available): category 'other' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: executive.mention forced escalate=true (matched 'CEO')

**edge-13** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-14** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.unauthorized_access forced escalate=true (matched 'phishing'); security.unauthorized_access lifted urgency medium -> high

**edge-15** — Keyword-rules mode (no model available): category 'other' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-16** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-17** — Keyword-rules mode (no model available): category 'other' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-18** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-19** — Keyword-rules mode (no model available): category 'legal_contract' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: legal.compliance_request forced escalate=true (matched 'GDPR'); legal.compliance_request lifted urgency medium -> high

**edge-20** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'critical'. Escalation is decided by the guardrail layer.

**edge-21** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-22** — Keyword-rules mode (no model available): category 'feature_request' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: executive.mention forced escalate=true (matched 'VP')

**edge-23** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'high'. Escalation is decided by the guardrail layer.

**edge-24** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.vulnerability_report forced escalate=true (matched 'IDOR'); security.vulnerability_report lifted urgency medium -> high; security.data_exposure lifted urgency high -> critical

**edge-25** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-26** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'high'. Escalation is decided by the guardrail layer.

**edge-27** — Keyword-rules mode (no model available): category 'bug' by cue words, urgency 'critical'. Escalation is decided by the guardrail layer.

**edge-28** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-29** — Keyword-rules mode (no model available): category 'spam' by cue words, urgency 'low'. Escalation is decided by the guardrail layer.

**edge-30** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.unauthorized_access forced escalate=true (matched 'offboarded'); security.unauthorized_access lifted urgency medium -> high

**edge-31** — Keyword-rules mode (no model available): category 'billing' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-32** — Keyword-rules mode (no model available): category 'other' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.

**edge-33** — Keyword-rules mode (no model available): category 'security' by cue words, urgency 'medium'. Escalation is decided by the guardrail layer.
  - overrides: security.data_exposure forced escalate=true (matched 'permissions change'); security.data_exposure lifted urgency medium -> critical
