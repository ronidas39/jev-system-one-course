"""Decisions 4: pick one option from a list (a choice).

We ask which team should handle two tickets: a simple one, and one with
three problems in it. We print the choice, every probability and the
confidence. Same teams and tickets as we gave Jev.

Run it from the decisions folder:
    python 04_choice.py

Author: Roni Das
"""

import os

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: the question and the two tickets
# ---------------------------------------------------------------------------
TEAM = {
    "type": "choice",
    "name": "team",
    "instructions": "Which team should handle this?",
    "choices": [
        {"value": "returns", "description": "Exchanges, wrong or damaged items"},
        {"value": "shipping", "description": "Delivery status, delays, lost packages"},
        {"value": "billing", "description": "Charges, invoices, payment problems"},
    ],
}

TICKETS = [
    "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
    "Shoes arrived two weeks late and in the wrong size. Also I see two charges "
    "of $120 on my card. What are you going to do about this?",
]

# ---------------------------------------------------------------------------
# Step 2: ask about each ticket, and print the answer
# ---------------------------------------------------------------------------
for ticket in TICKETS:
    decision = client.decisions.create(model="gpt-6-luna", input=ticket, questions=[TEAM])
    answer = decision.answers[0]
    print()
    print("ticket       ", ticket[:70] + "...")
    print("choice       ", answer.choice)
    print("probabilities", {p.value: p.probability for p in answer.probabilities})
    print("confidence   ", answer.confidence)
