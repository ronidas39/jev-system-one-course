"""The big project: clean up messy company records with Jev.

Our company keeps customer records in three systems (sales, billing, support).
The same company is often typed differently in each one. Here we take every
record whose name contains "Orchid", ask Jev about each pair of records, and
join the records that belong to the same company.

Run it from the course folder:
    python usecases/big_project.py

Author: Roni Das
"""

import json
import os
from itertools import combinations

from typesafe_sdk import Score, TypeSafeClient

# Read the API key from the .env file in the course folder.
for line in open(".env"):
    if line.startswith("TYPESAFE_API_KEY="):
        os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip()

# ---------------------------------------------------------------------------
# Step 1: load the messy records
# ---------------------------------------------------------------------------
all_records = [json.loads(line) for line in open("data/companies-fresh/records.jsonl")]
records = [r for r in all_records if "orchid" in r["name"].lower()]

print(f"Step 1: {len(records)} records have 'Orchid' in the name")
for r in records:
    print(f"   {r['record_id']}  {r['name']:<38} {r['address']}")

# ---------------------------------------------------------------------------
# Step 2: make every pair of records
# ---------------------------------------------------------------------------
pairs = list(combinations(records, 2))
print(f"\nStep 2: {len(pairs)} pairs to check")

# ---------------------------------------------------------------------------
# Step 3: ask Jev about each pair
# ---------------------------------------------------------------------------
QUESTION = {
    "link": Score(
        instructions="How do the two company records relate?",
        criteria=[
            "Two different companies.",
            "Not sure: a person should check before merging.",
            "The same company, just written differently: legal words like Ltd added "
            "or dropped, short forms, capital letters, small typos, a different contact.",
        ],
    )
}

merge, person, separate = [], [], []
with TypeSafeClient() as client:
    for a, b in pairs:
        answer = client.system_one(state={"record_a": a, "record_b": b}, questions=QUESTION)
        score = answer.answers["link"].score          # a number from 0 to 2
        if score >= 1.5:
            merge.append((a, b))
        elif score >= 0.5:
            person.append((a, b))
        else:
            separate.append((a, b))

print(f"\nStep 3: Jev decided: merge {len(merge)}, person checks {len(person)}, "
      f"keep separate {len(separate)}")
for a, b in person:
    print(f"   check: {a['name']}  <->  {b['name']}")

# ---------------------------------------------------------------------------
# Step 4: join the merged records into companies
# ---------------------------------------------------------------------------
company_of = {r["record_id"]: r["record_id"] for r in records}   # each record starts alone

for a, b in merge:
    old, new = company_of[b["record_id"]], company_of[a["record_id"]]
    for record_id, company in company_of.items():
        if company == old:
            company_of[record_id] = new

companies = {}
for r in records:
    companies.setdefault(company_of[r["record_id"]], []).append(r["name"])

print(f"\nStep 4: {len(records)} records became {len(companies)} companies")
for names in companies.values():
    print("   - " + "  |  ".join(names))

# Check against the true answer that came with the data.
truth = json.load(open("data/companies-fresh/truth.json"))["record_to_entity"]
real = len({truth[r["record_id"]] for r in records})
print(f"\nThe true answer: {real} real companies")
