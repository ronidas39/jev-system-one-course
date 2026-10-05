# Data card

All data in this repository is **synthetic**. It was made by the two scripts in this folder.
No real customer, company or person is in it. Any match with a real company name is chance.

## Why synthetic

To measure accuracy you need the right answers. With real records you rarely know them for
sure. Here the data maker writes the right answer when it writes the record. So
every accuracy number in the course is checked against a known truth.

## tickets.jsonl

| | |
|---|---|
| Made by | `python data/make_tickets.py` |
| Seed | 20261006 (same seed, same file) |
| Rows | 300 support tickets |
| Labels | `team` (billing, technical, shipping, account, sales), `urgency` (0, 1, 2), `frustration` (0, 1, 2) |
| Per team | billing 71, technical 56, shipping 64, account 54, sales 55 |

**How a ticket is built.** One main problem sentence decides the team. One urgency phrase
decides urgency. One mood phrase decides frustration. Then some mess is added:

- a greeting and a signature.
- an unrelated detail (35% of tickets).
- a side remark about another team's topic (25%).
- a typo with two letters swapped (30%).
- all small letters (15%).

The `traits` field lists what was added.

**Known limits.** The phrases come from small lists. So the text repeats more than real
tickets do. Urgency and mood phrases are picked separately. So a few tickets mix a calm mood with
a furious phrase. A real customer would not write that. A few problem sentences could belong to
two teams. One example: "change the billing email on our account". The label is the team of the
list that sentence came from. So compare models on this data. Do not expect the same accuracy on
your own tickets.

## companies/ and companies-fresh/

| | companies | companies-fresh |
|---|---|---|
| Made by | `python data/make_companies.py` | `python data/make_companies.py --seed 20261007 --out companies-fresh` |
| Seed | 20261006 | 20261007 |
| Real companies (truth) | 355 | 355 |
| Records | 730 | 716 |
| Look-alikes | 30 subsidiaries, 25 namesakes | 30 subsidiaries, 25 namesakes |

**What a record is.** A record is one company, as typed into one system. There are three
systems: `crm` (sales), `billing` (finance) and `support` (help desk). Each real company appears
in one to three systems. Fields: name, address, country, phone, website and a contact person.
The contact has a role and an email.

**The mess.** Billing and support have more mess than the CRM. The kinds of mess:

- legal words changed or dropped: Pvt Ltd, Private Limited, Inc., GmbH.
- words written another way: Engg for Engineering, Hosp. for Hospitality, Pharmaceuticals
  for Pharma.
- "M/s." in front of Indian names.
- all capital letters.
- typos with two letters swapped.
- old city names: Bombay, Bangalore, Gurgaon, Calcutta, Madras, München.
- short street words: Rd, St.
- a floor or a suite added.
- phone numbers written four ways, or missing.
- a second phone line.
- websites with or without `www.`, or missing.
- contacts with a gmail address.
- in billing, an office that moved to a new street.

`truth.json` → `record_notes` lists the mess added to each record.

**The traps.** Subsidiaries ("Kestrel Logistics" and "Kestrel Logistics UK") are different
companies. Namesakes (the same name in another country, with a different website) are different
companies. Siblings ("Cedar Foods" and "Cedar Analytics") share a word and nothing else.

**What the model sees.** Only the two records and two checks done by code. Do the last 7 phone
digits match? Does the website match? The model never sees `truth.json`.

**Known limits.** Look-alikes are always in different countries. That makes them easier to
separate than many real ones. Names come from fixed word lists. Real data has harder cases.
Companies merge. Companies change their names. Two companies share an office. People move to a new
company.

### What is not realistic

- Postcodes are random five-digit numbers in every country. Real Indian PIN codes have six
  digits. UK postcodes mix letters and digits. The records only need a postcode to be there or
  missing. So the data maker does not copy each country's real format.
- Names, streets, phone numbers and emails are made up. Any match with a real company or person
  is chance.

## Candidate pairs (made by `capstone/step1_block.py`)

| | companies | companies-fresh |
|---|---|---|
| All possible pairs | 266,085 | 255,970 |
| Candidate pairs after blocking | 1,010 | 1,014 |
| True duplicates in the data | 473 | 463 |
| True duplicates kept by blocking | 473 (100%) | 463 (100%) |
| Same company / subsidiary / namesake / different, among candidates | 473 / 111 / 104 / 322 | 463 / 131 / 84 / 336 |
