"""Refund desk, extra: ask about the photo in its own call.

In steps 2 to 4 the photo question also sees the customer's message. Here each
claim gets two calls, one for the message and one for the photo alone, so the
customer's words cannot push the photo answer. The rule is the same as before.

Run it from the decisions folder:
    python steps/extra/desk_step5_photo_alone.py

Author: Roni Das
"""

import base64
import json
import os
import time

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
# Step 2: two calls per claim, so the photo question never sees the message
# ---------------------------------------------------------------------------
claims = json.load(open("returns_claims.json"))["claims"]
start = time.perf_counter()
tokens = 0
refunded = 0
print(f"{'claim':<6} {'photo':<10} {'message says':<13} {'photo shows':<12} {'photo agrees':>12}  what we do")
for claim in claims:
    first = client.decisions.create(
        model="gpt-6-luna",
        input=f"Customer message: {claim['message']}",
        questions=[MESSAGE_QUESTION],
    )
    photo_bytes = open(f"eggs/{claim['photo']}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    second = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [{"type": "input_image", "image_url": url}]}],
        questions=[PHOTO_QUESTION],
    )
    tokens += first.usage.input_tokens + second.usage.input_tokens
    message_answer, photo_answer = first.answers[0], second.answers[0]
    action, photo_agrees = decide(message_answer, photo_answer)
    if action == "refund now":
        refunded += 1
    agrees_text = "-" if photo_agrees is None else f"{photo_agrees:.2f}"
    print(f"{claim['id']:<6} {claim['photo']:<10} {message_answer.choice:<13} {photo_answer.choice:<12} "
          f"{agrees_text:>12}  {action}")

# ---------------------------------------------------------------------------
# Step 3: add up the time and the cost
# ---------------------------------------------------------------------------
seconds = time.perf_counter() - start
cost = tokens * 0.10 / 1_000_000
print()
print(f"{len(claims)} claims in {seconds:.1f} seconds: {refunded} refunded now, "
      f"{len(claims) - refunded} for a person to check")
print(f"cost for all {len(claims)} claims: ${cost:.6f}")
