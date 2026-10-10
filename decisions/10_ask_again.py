"""Decisions 10, part 2: ask about the same photo again. Does the answer move?

If asking again gave a different answer each time, we could ask three times
and take the average for an unsure egg. Here we send each of four photos three
times and look at the largest gap between the three answers.

Run it from the decisions folder:
    python 10_ask_again.py

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
# Step 1: send each photo three times and keep P(clean)
# ---------------------------------------------------------------------------
for egg in ["duck-01", "tray-06", "box10-09", "box10-10"]:
    photo_bytes = open(f"eggs/{egg}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    tries = []
    for _ in range(3):
        decision = client.decisions.create(
            model="gpt-6-luna",
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": "One egg from a grading line."},
                {"type": "input_image", "image_url": url},
            ]}],
            questions=[QUESTION],
        )
        answer = decision.answers[0]
        tries.append(next(p.probability for p in answer.probabilities if p.value == "clean"))

    # -----------------------------------------------------------------------
    # Step 2: how far apart are the three answers?
    # -----------------------------------------------------------------------
    gap = max(tries) - min(tries)
    print(f"{egg:<10} P(clean) on 3 tries: {[round(t, 2) for t in tries]}   largest gap {gap:.3f}")
