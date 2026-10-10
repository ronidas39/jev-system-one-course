"""Decisions 8: what 20 tickets cost, read from the usage the API sends back.

We send 20 course tickets from data/tickets.jsonl, one call each, with our
three usual questions (team, urgency, frustration). Every answer carries
usage.input_tokens. Cost = input tokens x the price. Output is free.

Run it from the decisions folder:
    python 08_cost.py

Author: Roni Das
"""

import json
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

PRICE = 0.10  # US dollars per million input tokens, from OpenAI's guide, read 2026-10-09

# ---------------------------------------------------------------------------
# Step 1: our three usual questions
# ---------------------------------------------------------------------------
QUESTIONS = [
    {"type": "choice", "name": "team",
     "instructions": "Which team should handle this support ticket?",
     "choices": [
         {"value": "billing", "description": "Charges, refunds, invoices, prices on a bill, "
                                             "subscriptions, billing details"},
         {"value": "technical", "description": "Bugs, errors, crashes, outages, slow pages, "
                                               "API or integration problems"},
         {"value": "shipping", "description": "Delivery, tracking, couriers, damaged or lost "
                                              "parcels, delivery addresses"},
         {"value": "account", "description": "Login, passwords, security, profile, users and "
                                             "permissions, data deletion"},
         {"value": "sales", "description": "Buying, plans, quotes, discounts, demos, trials "
                                           "for new or bigger purchases"},
     ]},
    {"type": "score", "name": "urgency",
     "instructions": "How soon does this ticket need a response?",
     "levels": [
         {"label": "Can wait: no harm if answered in a few days"},
         {"label": "Soon: should be handled within a day or two"},
         {"label": "Today: work, money or security is blocked right now"},
     ]},
    {"type": "score", "name": "frustration",
     "instructions": "How frustrated does the customer appear?",
     "levels": [
         {"label": "Calm, just stating facts"},
         {"label": "Frustrated but civil"},
         {"label": "Very angry, insulting, or threatening to leave or complain"},
     ]},
]

# ---------------------------------------------------------------------------
# Step 2: send the first 20 tickets, and read the input tokens of each
# ---------------------------------------------------------------------------
tickets = [json.loads(line) for line in open("../data/tickets.jsonl")][:20]

total = 0
print(f"{'ticket':<7} {'characters':>10} {'input tokens':>12} {'cost (US$)':>12}")
for ticket in tickets:
    decision = client.decisions.create(model="gpt-6-luna", input=ticket["text"],
                                       questions=QUESTIONS)
    used = decision.usage.input_tokens
    total += used
    print(f"{ticket['id']:<7} {len(ticket['text']):>10} {used:>12} "
          f"{used * PRICE / 1_000_000:>12.8f}")

# ---------------------------------------------------------------------------
# Step 3: add it up, and scale to a thousand and a million tickets
# ---------------------------------------------------------------------------
cost = total * PRICE / 1_000_000
print()
print(f"price: ${PRICE} per million input tokens")
print(f"20 tickets: {total} input tokens, ${cost:.6f}")
print(f"average tokens per ticket: {total / 20:.1f}")
print(f"so 1,000 tickets cost about ${cost / 20 * 1000:.4f}, "
      f"and one million about ${cost / 20 * 1_000_000:.2f}")
