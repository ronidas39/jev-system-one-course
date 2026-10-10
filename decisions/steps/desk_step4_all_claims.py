"""Refund desk, step 4: the full desk, every claim in returns_claims.json.

The same two questions and the same policy as step 3. Now we run all eight
claims, print one line per claim, and add up the time, the tokens and the cost.

Run it from the decisions folder:
    python steps/desk_step4_all_claims.py

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
# Step 2: ask about every claim, one call each, and let the policy decide
# ---------------------------------------------------------------------------
claims = json.load(open("returns_claims.json"))["claims"]
start = time.perf_counter()
tokens = 0
refunded = 0
print(f"{'id':<4} {'photo file':<10} {'message says':<12} {'photo shows':<12} {'P(agree)':>8}  action")
for c in claims:
    photo_bytes = open(f"eggs/{c['photo']}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": f"Customer message: {c['message']}"},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=[CLAIM_QUESTION, PHOTO_QUESTION],
    )
    tokens += decision.usage.input_tokens
    answers = {a.name: a for a in decision.answers}
    claim, shown = answers["claim"], answers["photo"]
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
print(f"{len(claims)} claims in {seconds:.1f} s: {refunded} refunded automatically, "
      f"{len(claims) - refunded} sent to a person")
print(f"input tokens {tokens}, cost ${cost:.6f} (about ${cost / len(claims) * 1000:.4f} per 1,000 claims)")
