"""Decisions 3: a yes or no question (a predicate) on six messages.

A predicate gives one number: the probability, from 0 to 1, that the answer
is yes. These are the same six messages we gave Jev, so you can compare.

Run it from the decisions folder:
    python 03_predicate.py

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
# Step 1: the question and the six messages
# ---------------------------------------------------------------------------
QUESTION = {
    "type": "predicate",
    "name": "is_human_escalation",
    "instructions": "Is the customer asking for a human agent?",
}

MESSAGES = [
    "Thanks, that fixed it!",
    "How do I reset my password?",
    "I need this sorted today, whatever it takes.",
    "Are you a bot?",
    "Is there any way to speak to someone about my invoice?",
    "I have asked three times now. Can I please just talk to a real person?",
]

# ---------------------------------------------------------------------------
# Step 2: ask about each message, and print the probability of yes
# ---------------------------------------------------------------------------
print(f"{'message':<74} {'probability':>11}")
for message in MESSAGES:
    decision = client.decisions.create(model="gpt-6-luna", input=message, questions=[QUESTION])
    answer = decision.answers[0]
    print(f"{message:<74} {answer.probability:>11.2f}")
print("model:", decision.model)
