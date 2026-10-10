"""Side by side: Jev and the Decisions API answer the same support tickets.

We take 30 tickets from data/tickets.jsonl. Each ticket comes with its right
answers (the labels): the team, the urgency and the customer's frustration.
We send every ticket to Jev and to the Decisions API with the same three
questions, one call at a time, and count the right answers, the time and the cost.

Run it from the course folder:
    python compare_decisions/side_by_side.py

Prices (read 9 October 2026), in US dollars per million input tokens:
    Jev 0.042 (https://docs.typesafe.ai/models)
    Decisions API 0.10 (https://developers.openai.com/api/docs/guides/decisions)

Author: Roni Das
"""

import json
import os
import time

from openai import OpenAI
from typesafe_sdk import Choice, Score, TypeSafeClient

# Read the two API keys from the .env file in the course folder.
for line in open(".env"):
    for name in ("TYPESAFE_API_KEY", "OPENAI_API_KEY"):
        if line.startswith(name + "="):
            os.environ[name] = line.split("=", 1)[1].strip()

# ---------------------------------------------------------------------------
# Step 1: load 30 tickets with their right answers
# ---------------------------------------------------------------------------
all_tickets = [json.loads(line) for line in open("data/tickets.jsonl")]
tickets = all_tickets[::10]          # every tenth ticket, so 30 of the 300
print(f"Step 1: {len(tickets)} tickets, for example:")
print(f"   {tickets[0]['text'][:70]}...")
print(f"   right answers: team={tickets[0]['team']}, urgency={tickets[0]['urgency']}, "
      f"frustration={tickets[0]['frustration']}")

# ---------------------------------------------------------------------------
# Step 2: the same three questions, written for each API
# ---------------------------------------------------------------------------
TEAMS = {
    "billing": "Charges, refunds, invoices, prices on a bill, subscriptions, billing details",
    "technical": "Bugs, errors, crashes, outages, slow pages, API or integration problems",
    "shipping": "Delivery, tracking, couriers, damaged or lost parcels, delivery addresses",
    "account": "Login, passwords, security, profile, users and permissions, data deletion",
    "sales": "Buying, plans, quotes, discounts, demos, trials for new or bigger purchases",
}
URGENCY = [
    "Can wait: no harm if answered in a few days",
    "Soon: should be handled within a day or two",
    "Today: work, money or security is blocked right now",
]
FRUSTRATION = [
    "Calm, just stating facts",
    "Frustrated but civil",
    "Very angry, insulting, or threatening to leave or complain",
]

JEV_QUESTIONS = {
    "team": Choice(instructions="Which team should handle this support ticket?", criteria=TEAMS),
    "urgency": Score(instructions="How soon does this ticket need a response?", criteria=URGENCY),
    "frustration": Score(instructions="How frustrated does the customer appear?",
                         criteria=FRUSTRATION),
}
DECISIONS_QUESTIONS = [
    {"type": "choice", "name": "team",
     "instructions": "Which team should handle this support ticket?",
     "choices": [{"value": k, "description": v} for k, v in TEAMS.items()]},
    {"type": "score", "name": "urgency",
     "instructions": "How soon does this ticket need a response?",
     "levels": [{"label": text} for text in URGENCY]},
    {"type": "score", "name": "frustration",
     "instructions": "How frustrated does the customer appear?",
     "levels": [{"label": text} for text in FRUSTRATION]},
]
print(f"\nStep 2: the same 3 questions for both: {', '.join(JEV_QUESTIONS)}")

# ---------------------------------------------------------------------------
# Step 3: send every ticket to both, one call at a time
# ---------------------------------------------------------------------------
jev = TypeSafeClient(model="jev-1.13.0")
openai_client = OpenAI()
results = {"jev-1.13.0": [], "decisions gpt-6-luna": []}   # one row per ticket

for ticket in tickets:
    start = time.perf_counter()
    answer = jev.system_one(state=ticket["text"], questions=JEV_QUESTIONS)
    seconds = time.perf_counter() - start
    a = answer.answers
    results["jev-1.13.0"].append({
        "team": a["team"].choice, "urgency": round(a["urgency"].score),
        "frustration": round(a["frustration"].score),
        "seconds": seconds, "tokens": answer.usage.input_tokens,
        "usd": answer.usage.input_tokens * 0.042 / 1_000_000})

    start = time.perf_counter()
    decision = openai_client.decisions.create(model="gpt-6-luna", input=ticket["text"],
                                              questions=DECISIONS_QUESTIONS)
    seconds = time.perf_counter() - start
    d = {x.name: x for x in decision.answers}
    results["decisions gpt-6-luna"].append({
        "team": d["team"].choice, "urgency": round(d["urgency"].score),
        "frustration": round(d["frustration"].score),
        "seconds": seconds, "tokens": decision.usage.input_tokens,
        "usd": decision.usage.input_tokens * 0.10 / 1_000_000})

print(f"\nStep 3: sent {len(tickets)} tickets to each API, {2 * len(tickets)} calls")

# ---------------------------------------------------------------------------
# Step 4: count right answers, time and cost for each API
# ---------------------------------------------------------------------------
print(f"\nStep 4: results on {len(tickets)} tickets")
print(f"   {'':<22} {'team':>6} {'urgency':>8} {'frustration':>12} {'time per call':>14}   cost")
for api, rows in results.items():
    right = {q: sum(row[q] == t[q] for row, t in zip(rows, tickets))
             for q in ("team", "urgency", "frustration")}
    seconds = sum(row["seconds"] for row in rows) / len(rows)
    usd = sum(row["usd"] for row in rows)
    print(f"   {api:<22} {right['team']:>3}/{len(rows)} {right['urgency']:>5}/{len(rows)} "
          f"{right['frustration']:>9}/{len(rows)} {seconds:>12.2f} s   ${usd:.6f}")

per_ticket = {api: sum(r["tokens"] for r in rows) / len(rows) for api, rows in results.items()}
print("\n   input tokens per ticket: "
      + ", ".join(f"{api} {tokens:.0f}" for api, tokens in per_ticket.items()))
