"""Decisions 10: grade 33 egg photos and decide what to do with each egg.

We ask one question about every photo in eggs/: is the shell clean, dirty,
cracked, or is the photo unclear? Each egg gets one number, P(not clean),
the chance that the egg is NOT clean. One simple rule then says:
sell it, throw it away, or let a person look at it.

The labels in eggs/labels.csv are the course author's own, made by eye.
They are drafts, not an expert's grades. See eggs/CREDITS.md.

Run it from the decisions folder:
    python 10_egg_grading.py

Author: Roni Das
"""

import base64
import csv
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

QUESTION = {
    "type": "choice",
    "name": "condition",
    "instructions": "What is the condition of the egg shell in this photo?",
    "choices": [
        {"value": "clean", "description": "Shell is intact with no dirt, stains or droppings."},
        {"value": "dirty", "description": "Shell is intact but has dirt, stains or droppings."},
        {"value": "cracked", "description": "Shell has a crack, hole, or is broken open."},
        {"value": "unclear", "description": "The photo does not show the shell well enough."},
    ],
}

# ---------------------------------------------------------------------------
# Step 1: load the 33 photo names and my labels
# ---------------------------------------------------------------------------
labels = {row["egg"]: row["condition"] for row in csv.DictReader(open("eggs/labels.csv"))}
print(f"Step 1: {len(labels)} photos with my labels")

# ---------------------------------------------------------------------------
# Step 2: one call per photo, keep P(not clean)
# ---------------------------------------------------------------------------
not_clean = {}
tokens = 0
print("\nStep 2: one call per photo")
for egg, label in labels.items():
    photo_bytes = open(f"eggs/{egg}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=[QUESTION],
    )
    answer = decision.answers[0]
    p_clean = next(p.probability for p in answer.probabilities if p.value == "clean")
    not_clean[egg] = 1 - p_clean
    tokens += decision.usage.input_tokens
print(f"   {len(labels)} calls, {tokens} input tokens, cost ${tokens * 0.10 / 1_000_000:.6f}")

# ---------------------------------------------------------------------------
# Step 3: turn each number into an action with one simple rule
#         P(not clean) below 0.30  -> SELL it        (we are sure it is clean)
#         P(not clean) above 0.70  -> THROW it away  (we are sure it is bad)
#         anything in between      -> a PERSON looks at it
# ---------------------------------------------------------------------------
SURE_CLEAN = 0.30
SURE_BAD = 0.70

print("\nStep 3: what we do with each egg")
print(f"   {'photo':<10} {'my label':<9} {'P(not clean)':>12}   action")
counts = {"SELL": 0, "THROW": 0, "PERSON": 0}
mistakes = []
for egg, label in labels.items():
    p = not_clean[egg]
    if p < SURE_CLEAN:
        action = "SELL"
    elif p > SURE_BAD:
        action = "THROW"
    else:
        action = "PERSON"
    counts[action] += 1
    print(f"   {egg:<10} {label:<9} {p:>12.2f}   {action}")
    # A mistake is selling a bad egg, or throwing away a clean one.
    if (action == "SELL" and label != "clean") or (action == "THROW" and label == "clean"):
        mistakes.append(egg)

# ---------------------------------------------------------------------------
# Step 4: the summary
# ---------------------------------------------------------------------------
print(f"\nStep 4: sell {counts['SELL']}, throw away {counts['THROW']}, "
      f"a person checks {counts['PERSON']}")
print(f"   mistakes (a bad egg sold, or a clean egg thrown away): {len(mistakes)} {mistakes}")
