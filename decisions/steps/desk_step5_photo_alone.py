"""Refund desk, step 5: ask about the photo on its own.

In steps 2 to 4 the photo question also saw the customer's message. A message
that says "cracked" might pull the photo answer toward "broken". So now each
claim gets two calls: one reads only the message, the other sees only the
photo. The policy is the same as before.

Run it from the decisions folder:
    python steps/desk_step5_photo_alone.py

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
AUTO_REFUND_AT = 0.90

CLAIM_QUESTION = {
    "type": "choice",
    "name": "claim",
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
# Step 1: the shop's policy, in plain code
# ---------------------------------------------------------------------------
def decide(claim, shown):
    """Returns the action and P(photo agrees with the message)."""
    if claim.type == "refusal" or shown.type == "refusal":
        return "person (a question was refused)", None
    if claim.choice not in ("broken", "dirty"):
        return "person (not a damage claim)", None
    if claim.confidence < AUTO_REFUND_AT:
        return "person (message is not clear)", None
    agree = next(p.probability for p in shown.probabilities if p.value == claim.choice)
    if agree >= AUTO_REFUND_AT:
        return "REFUND automatically", agree
    return "person (photo does not clearly agree)", agree


# ---------------------------------------------------------------------------
# Step 2: two calls per claim, so the photo question never sees the message
# ---------------------------------------------------------------------------
claims = json.load(open("returns_claims.json"))["claims"]
start = time.perf_counter()
tokens = 0
refunded = 0
print(f"{'id':<4} {'photo file':<10} {'message says':<12} {'photo shows':<12} {'P(agree)':>8}  action")
for c in claims:
    first = client.decisions.create(
        model="gpt-6-luna",
        input=f"Customer message: {c['message']}",
        questions=[CLAIM_QUESTION],
    )
    photo_bytes = open(f"eggs/{c['photo']}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    second = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [{"type": "input_image", "image_url": url}]}],
        questions=[PHOTO_QUESTION],
    )
    tokens += first.usage.input_tokens + second.usage.input_tokens
    claim, shown = first.answers[0], second.answers[0]
    action, agree = decide(claim, shown)
    if action.startswith("REFUND"):
        refunded += 1
    agree_text = "-" if agree is None else f"{agree:.2f}"
    print(f"{c['id']:<4} {c['photo']:<10} {claim.choice:<12} {shown.choice:<12} {agree_text:>8}  {action}")

# ---------------------------------------------------------------------------
# Step 3: add up the time, the tokens and the cost
# ---------------------------------------------------------------------------
seconds = time.perf_counter() - start
cost = tokens * 0.10 / 1_000_000
print()
print(f"two calls per claim. {len(claims)} claims in {seconds:.1f} s: {refunded} refunded "
      f"automatically, {len(claims) - refunded} sent to a person")
print(f"input tokens {tokens}, cost ${cost:.6f} (about ${cost / len(claims) * 1000:.4f} per 1,000 claims)")
