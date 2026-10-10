"""Decisions 7: a refusal, two errors, and code that handles both.

Part 1, a refusal. Three questions about one support message. Two are fair.
The third asks which illness the customer has, which a support tool has no
business guessing, so the model may refuse that one question. The other
answers still come back. Then we ask it again with an "other" option.

Part 2, errors. A broken request fails as a whole, with an HTTP error.
We cause two on purpose and print what they look like.

Run it from the decisions folder:
    python 07_refusals_and_errors.py

Author: Roni Das
"""

import os

import openai
from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: one message, two fair questions and one unfair one
# ---------------------------------------------------------------------------
MESSAGE = ("I was in hospital all of last week, so I missed the return window for my "
           "order. Can I still send it back and get my money?")

TEAM = {"type": "choice", "name": "team", "instructions": "Which team should handle this?",
        "choices": [
            {"value": "returns", "description": "Exchanges, returns, wrong or damaged items"},
            {"value": "shipping", "description": "Delivery status, delays, lost packages"},
            {"value": "billing", "description": "Charges, invoices, payment problems"},
        ]}
REFUND = {"type": "predicate", "name": "refund_requested",
          "instructions": "Does the customer ask for their money back?"}
ILLNESS = {"type": "choice", "name": "illness",
           "instructions": "Which illness does the customer have?",
           "choices": [
               {"value": "heart", "description": "A heart condition"},
               {"value": "cancer", "description": "Cancer"},
               {"value": "infection", "description": "An infection"},
           ]}


def route(answer):
    """What our code does with one answer. A refusal always goes to a person."""
    if answer.type == "refusal":
        return "REFUSED -> send to a person"
    if answer.type == "predicate":
        return f"probability {answer.probability:.2f}"
    return f"{answer.choice} (confidence {answer.confidence:.2f})"


# ---------------------------------------------------------------------------
# Step 2: ask all three together, and route each answer
# ---------------------------------------------------------------------------
print("Part 1 · a refusal")
decision = client.decisions.create(model="gpt-6-luna", input=MESSAGE,
                                   questions=[TEAM, REFUND, ILLNESS])
for answer in decision.answers:
    print(f"{answer.name:<17} {route(answer)}")

# ---------------------------------------------------------------------------
# Step 3: the same health question, now with an "other" option
# ---------------------------------------------------------------------------
print()
print("The same health question, now with an 'other' option")
ILLNESS["choices"].append({"value": "other", "description": "Something else, or not stated"})
again = client.decisions.create(model="gpt-6-luna", input=MESSAGE, questions=[ILLNESS])
print(f"{'illness':<17} {route(again.answers[0])}")

# ---------------------------------------------------------------------------
# Step 4: two broken requests, which fail as a whole
# ---------------------------------------------------------------------------
print()
print("Part 2 · errors")
ONE_OPTION = {"type": "choice", "name": "team", "instructions": "Which team?",
              "choices": [{"value": "returns"}]}
UNKNOWN_TYPE = {"type": "yes_no", "name": "x", "instructions": "Is this a refund?"}

for label, question in [("a choice with only one option", ONE_OPTION),
                        ("an unknown question type", UNKNOWN_TYPE)]:
    try:
        client.decisions.create(model="gpt-6-luna", input=MESSAGE, questions=[question])
        print(label, "-> no error")
    except openai.APIStatusError as error:
        print(f"{label} -> HTTP {error.status_code}: {type(error).__name__}")
        print("   ", error.body["message"])
