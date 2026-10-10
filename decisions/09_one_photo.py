"""Decisions 9: send a photo. Three questions about one egg, in one call.

A photo is not text, so we write it as base64 (plain letters and digits) and
put it in the message as a data URL, next to one line of text. We ask three
questions about each egg: a choice, a yes or no, and a score.

Run it from the decisions folder:
    python 09_one_photo.py

Author: Roni Das
"""

import base64
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: the three questions
# ---------------------------------------------------------------------------
QUESTIONS = [
    {
        "type": "choice",
        "name": "condition",
        "instructions": "What is the condition of the egg shell in this photo?",
        "choices": [
            {"value": "clean", "description": "Shell is intact with no dirt, stains or droppings."},
            {"value": "dirty", "description": "Shell is intact but has dirt, stains or droppings."},
            {"value": "cracked", "description": "Shell has a crack, hole, or is broken open."},
            {"value": "unclear", "description": "The photo does not show the shell well enough."},
        ],
    },
    {
        "type": "predicate",
        "name": "visible_crack",
        "instructions": "Does the egg shell have a visible crack, hole or break? "
                        "Ignore shadows and the carton.",
    },
    {
        "type": "score",
        "name": "dirt_level",
        "instructions": "How dirty is the egg shell?",
        "levels": [
            {"label": "none", "description": "No visible dirt or stains."},
            {"label": "light", "description": "A few small marks a customer might not notice."},
            {"label": "heavy", "description": "Smears or many spots a customer would notice."},
        ],
    },
]

# ---------------------------------------------------------------------------
# Step 2: send each photo as a base64 data URL, with the three questions
# ---------------------------------------------------------------------------
for egg in ["box10-03", "duck-04", "broken-02"]:
    photo_bytes = open(f"eggs/{egg}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()

    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=QUESTIONS,
    )

    # -----------------------------------------------------------------------
    # Step 3: print the three answers
    # -----------------------------------------------------------------------
    answers = {a.name: a for a in decision.answers}
    condition, crack, dirt = answers["condition"], answers["visible_crack"], answers["dirt_level"]
    odds = {p.value: round(p.probability, 2) for p in condition.probabilities}
    tokens = decision.usage.input_tokens
    print()
    print(f"photo           eggs/{egg}.jpg  (data URL: {len(url):,} characters)")
    print(f"condition       {condition.choice}  {odds}")
    print(f"visible crack   {crack.probability:.2f}")
    print(f"dirt (0 to 2)   {dirt.score:.2f}")
    print(f"input tokens    {tokens}  (cost ${tokens * 0.10 / 1_000_000:.8f})")
