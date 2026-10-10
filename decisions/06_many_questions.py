"""Decisions 6: eight questions in one call, against one question per call.

Same ticket and the same eight questions as we gave Jev. We send them once
together, then once each, and compare the answers, the input tokens (the
cost) and the time on this machine.

Run it from the decisions folder:
    python 06_many_questions.py

Author: Roni Das
"""

import os
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: one ticket and eight questions of all three types
# ---------------------------------------------------------------------------
TICKET = (
    "Hi, I placed an order (#98423) last Thursday and was charged twice. I also can't "
    "log in after the site update, and adding Apple Pay would be really helpful. "
    "This is getting frustrating."
)

QUESTIONS = [
    {"type": "choice", "name": "category",
     "instructions": "What is the main topic of this ticket?",
     "choices": [
         {"value": "bug_report",
          "description": "The user is reporting something that is broken or producing errors"},
         {"value": "billing", "description": "Charges, invoices, refunds, subscriptions"},
         {"value": "feature_request", "description": "The user is requesting new functionality"},
         {"value": "account", "description": "Login, permissions, profile, security"},
     ]},
    {"type": "score", "name": "bug_severity",
     "instructions": "How severe is the reported issue?",
     "levels": [
         {"label": "cosmetic", "description": "Cosmetic; no impact to functionality"},
         {"label": "workaround", "description": "Broken or degraded feature; workaround exists"},
         {"label": "blocking", "description": "Blocking issue; no workaround exists"},
     ]},
    {"type": "predicate", "name": "has_reproducible_steps",
     "instructions": "Does the user describe specific steps to reproduce the issue?"},
    {"type": "predicate", "name": "refund_requested",
     "instructions": "Does the customer request a refund?"},
    {"type": "predicate", "name": "mentions_duplicate_charge",
     "instructions": "Does the customer say they were charged twice?"},
    {"type": "predicate", "name": "cannot_log_in",
     "instructions": "Does the customer say they cannot log in?"},
    {"type": "predicate", "name": "asks_for_feature",
     "instructions": "Does the customer ask for a new feature?"},
    {"type": "score", "name": "frustration",
     "instructions": "How frustrated does the customer appear?",
     "levels": [
         {"label": "calm", "description": "Calm, just stating facts"},
         {"label": "frustrated", "description": "Frustrated but civil"},
         {"label": "angry", "description": "Very angry, strong language"},
     ]},
]


def short(answer):
    """One short piece of text for any type of answer."""
    if answer.type == "predicate":
        return f"{answer.probability:.2f}"
    if answer.type == "choice":
        return f"{answer.choice} (conf {answer.confidence:.2f})"
    if answer.type == "score":
        return f"{answer.score:.2f} (conf {answer.confidence:.2f})"
    return "REFUSED"


# ---------------------------------------------------------------------------
# Step 2: all eight questions in one call
# ---------------------------------------------------------------------------
start = time.time()
together = client.decisions.create(model="gpt-6-luna", input=TICKET, questions=QUESTIONS)
together_seconds = time.time() - start
together_tokens = together.usage.input_tokens

# ---------------------------------------------------------------------------
# Step 3: the same eight questions, one call each, one after another
# ---------------------------------------------------------------------------
separate = {}
separate_seconds = 0
separate_tokens = 0
for question in QUESTIONS:
    start = time.time()
    one = client.decisions.create(model="gpt-6-luna", input=TICKET, questions=[question])
    separate_seconds += time.time() - start
    separate_tokens += one.usage.input_tokens
    separate[question["name"]] = one.answers[0]

# ---------------------------------------------------------------------------
# Step 4: compare the answers, the tokens and the time
# ---------------------------------------------------------------------------
print(f"{'question':<26} {'one call (8 together)':<26} {'8 separate calls':<26}")
for answer in together.answers:
    print(f"{answer.name:<26} {short(answer):<26} {short(separate[answer.name]):<26}")

print()
print(f"one call: {together_seconds:6.3f} s, {together_tokens:5d} input tokens, "
      f"${together_tokens * 0.10 / 1_000_000:.8f}")
print(f"8 calls:  {separate_seconds:6.3f} s, {separate_tokens:5d} input tokens, "
      f"${separate_tokens * 0.10 / 1_000_000:.8f}")
print(f"8 calls cost {separate_tokens / together_tokens:.1f}x the tokens and took "
      f"{separate_seconds / together_seconds:.1f}x the time.")
