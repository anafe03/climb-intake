# Extraction: names, contacts, identifiers (mode=rules)

`scripts/extraction_probe.py` · 10 tickets · 2026-09-25 09:38

**Customer name right: 6 of 10.** **Identifiers found: 2 of 5.** A name counts as right only if the company is stated in the text; a guess from an email domain must stay a guess.

| id | what it tests | expected customer | got | identifier | |
|---|---|---|---|---|---|
| `ext-01` | Company and contact in a signature. | Meridian Health | none |  | ⚠️ |
| `ext-02` | An invoice number and no company at all. | none | none | MISSED INV-20931 | ⚠️ |
| `ext-03` | An account id and a company named in the sign-off. | Brightwater Labs | Brightwater Labs | MISSED ACC-5521 | ⚠️ |
| `ext-04` | Trap: a company named in the text that is not the customer. | none | none |  | ✅ |
| `ext-05` | Trap: two companies. The customer is the one writing. | Brightline | none |  | ⚠️ |
| `ext-06` | Only an email address. The domain is a clue, not a stated name. | none | (guess) someone at northwind.co.uk | found jo@northwind.co.uk | ✅ |
| `ext-07` | Nothing identifying at all. The right answer is to say so. | none | none |  | ✅ |
| `ext-08` | A signature in Spanish. | Grupo Alameda | none |  | ⚠️ |
| `ext-09` | An order number, a phone number and a first name only. | none | none | MISSED 88213 | ⚠️ |
| `ext-10` | A ticket reference and a company in the closing line. | Acme Robotics | (guess) an existing customer (account reference present) | found 4471 | ⚠️ |
