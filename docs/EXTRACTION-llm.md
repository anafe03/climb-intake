# Extraction: names, contacts, identifiers (mode=llm)

`scripts/extraction_probe.py` · 10 tickets · 2026-09-25 09:39

**Customer name right: 10 of 10.** **Identifiers found: 5 of 5.** A name counts as right only if the company is stated in the text; a guess from an email domain must stay a guess.

| id | what it tests | expected customer | got | identifier | |
|---|---|---|---|---|---|
| `ext-01` | Company and contact in a signature. | Meridian Health | Meridian Health |  | ✅ |
| `ext-02` | An invoice number and no company at all. | none | (guess) Existing paying customer requesting a copy of an invoice | found INV-20931 | ✅ |
| `ext-03` | An account id and a company named in the sign-off. | Brightwater Labs | Brightwater Labs | found ACC-5521 | ✅ |
| `ext-04` | Trap: a company named in the text that is not the customer. | none | (guess) Existing customer using the Salesforce integration, likely an admin or ops user monitoring syncs |  | ✅ |
| `ext-05` | Trap: two companies. The customer is the one writing. | Brightline | Brightline |  | ✅ |
| `ext-06` | Only an email address. The domain is a clue, not a stated name. | none | (guess) Customer from Northwind (northwind.co.uk) reporting an issue with CSV export | found jo@northwind.co.uk | ✅ |
| `ext-07` | Nothing identifying at all. The right answer is to say so. | none | (guess) Existing Climb user reporting a malfunctioning report in the product |  | ✅ |
| `ext-08` | A signature in Spanish. | Grupo Alameda | Grupo Alameda |  | ✅ |
| `ext-09` | An order number, a phone number and a first name only. | none | (guess) Existing paying customer reporting a duplicate charge on a single order | found 88213 | ✅ |
| `ext-10` | A ticket reference and a company in the closing line. | Acme Robotics | Acme Robotics | found 4471 | ✅ |
