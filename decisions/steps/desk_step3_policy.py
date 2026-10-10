"""Refund desk, step 3: the shop's rule, and the "a person checks" path.

Now our own code decides what happens to a claim, using the two answers.
We refund now only when the message clearly says broken or dirty AND the photo
shows that same problem with a chance of 0.90 or more. Everything else goes to
a person. The model never says no to a refund on its own.
We try three claims from returns_claims.json, one for each kind of outcome.

Run it from the decisions folder:
    python steps/desk_step3_policy.py

Author: Roni Das
"""

import base64
import json
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

MESSAGE_QUESTION = {
    "type": "choice",
    "name": "message",
    "instructions": "Read only the customer's message. What do they say is wrong?",
    "choices": [
        {"value": "broken", "description": "An egg is cracked, smashed or broken open."},
        {"value": "dirty", "description": "The shells are dirty or stained."},
        {"value": "late", "description": "The order came late."},
        {"value": "other", "description": "Anything else."},
    ],
}
PHOTO_QUESTION = {
    "type": "choice",
    "name": "photo",
    "instructions": "Look only at the photo. What condition is the egg in?",
    "choices": [
        {"value": "clean", "description": "Whole egg, clean shell."},
        {"value": "dirty", "description": "Whole egg, dirty or stained shell."},
        {"value": "broken", "description": "Cracked, smashed or broken open."},
        {"value": "unclear", "description": "No egg, or the photo is too unclear to tell."},
    ],
}


# ---------------------------------------------------------------------------
# Step 1: the shop's rule, in plain code
# ---------------------------------------------------------------------------
SURE_ENOUGH = 0.90


def decide(message_answer, photo_answer):
    """What we do with one claim, and how much the photo agrees (0 to 1)."""
    if message_answer.type == "refusal" or photo_answer.type == "refusal":
        return "a person checks (no answer)", None
    problem = message_answer.choice
    if problem not in ("broken", "dirty"):
        return "a person checks (not about damage)", None
    if message_answer.confidence < SURE_ENOUGH:
        return "a person checks (message not clear)", None
    photo_agrees = next(p.probability for p in photo_answer.probabilities if p.value == problem)
    if photo_agrees >= SURE_ENOUGH:
        return "refund now", photo_agrees
    return "a person checks (photo does not match)", photo_agrees


# ---------------------------------------------------------------------------
# Step 2: ask about three claims, then let the rule decide
# ---------------------------------------------------------------------------
claims = json.load(open("returns_claims.json"))["claims"]
for claim in claims:
    if claim["id"] not in ("C01", "C05", "C07"):
        continue
    photo_bytes = open(f"eggs/{claim['photo']}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": f"Customer message: {claim['message']}"},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=[MESSAGE_QUESTION, PHOTO_QUESTION],
    )
    answers = {a.name: a for a in decision.answers}
    message_answer, photo_answer = answers["message"], answers["photo"]
    action, photo_agrees = decide(message_answer, photo_answer)
    agrees_text = "-" if photo_agrees is None else f"{photo_agrees:.2f}"

    print()
    print(f"claim              {claim['id']}: {claim['message']}")
    print(f"the message says   {message_answer.choice}")
    print(f"the photo shows    {photo_answer.choice}")
    print(f"photo agrees       {agrees_text}")
    print(f"what we do         {action}")
