# Does the model catch escalations the keywords cannot?

`scripts/keyword_free_probe.py` · 6 tickets · 2026-09-24 20:05

## Why this exists

On the 33-row gold set the two halves of the classifier agree about escalation *exactly*:
11 tickets caught by both, none caught by either alone. Read carelessly that says the model
adds nothing. Read honestly it says the gold set cannot tell, because every escalating row in
it contains keyword vocabulary — which is unsurprising, since the rows and the patterns were
written by the same hand.

So: tickets that escalate in meaning and contain **none** of the words the patterns look for.
The keyword layer is checked silent on each one before the model sees it, so anything caught
here is caught by judgement alone.

Precondition verified: the keyword layer fires on none of them.

## Result

| Escalations the keywords cannot see | **5 of 5 caught by the model** |
|---|---|
| Missed | none |
| Control ticket wrongly escalated | no |

| id | what makes it invisible to the keywords | should escalate | model said | |
|---|---|---|---|---|
| `kf-01` | A leaver still has access, described without any of the words the patterns look for. | yes | **escalated** — security_incident, data_exposure | ✅ |
| `kf-02` | British English. The pattern knows lawyer, attorney and counsel; it does not know solicitor. | yes | **escalated** — legal_threat | ✅ |
| `kf-03` | The most senior person in the company, named by role rather than by title. | yes | **escalated** — executive_mention | ✅ |
| `kf-04` | Cross-tenant leak phrased from the other direction, with no matching noun phrase. | yes | **escalated** — security_incident, data_exposure | ✅ |
| `kf-05` | A statutory erasure demand with no acronym and no regulator named. | yes | **escalated** — compliance_request | ✅ |
| `kf-06` | Control. Reads urgent and is ordinary support work, so a model that escalates everything fails here. | no (control) | did not escalate | ✅ |

## The tickets

**kf-01** — Sam finished up with us back in June and we just noticed he can still get into the reporting dashboard. Can you close that off?

> This is an active security incident: a former employee retains access. Their data is exposed to an unauthorized individual. A human should confirm identity, revoke access immediately, and validate other offboarding controls.

**kf-02** — We've asked our solicitors to look over the agreement, because what you've delivered is not what was signed for. Expect to hear from them this week.

> They invoked solicitors regarding the agreement, indicating a potential legal dispute that requires legal review and coordination.

**kf-03** — The woman who runs our company saw the outage notice and wants someone to explain what happened before Thursday's board pack goes out.

> Escalate due to executive involvement ("the woman who runs our company" and a board deliverable). No signs of security incident, data exposure, legal or compliance requests.

**kf-04** — Quick heads up - the monthly summary you emailed us has a page at the end that clearly belongs to a different business. Names, totals, the lot.

> A customer received another business's names and totals in a report, indicating cross-tenant access and confirmed data exposure. This requires immediate security incident response and containment.

**kf-05** — One of our staff has asked us to have all of her information wiped from your system. We're told we have a month to action it under the new privacy rules here.

> This is a regulatory data erasure (GDPR/UK GDPR) request with a statutory deadline, which requires compliance review and tracking. No signs of security incident, data exposure, legal threat, or executive involvement.

**kf-06** — The export is timing out on anything over about 40,000 rows. We've retried four times this morning and we need the file for a client meeting tomorrow.

> No signs of security or data exposure, no legal or compliance requests, and no executives mentioned. This is a functional failure of the export feature.

