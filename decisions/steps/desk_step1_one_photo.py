"""Refund desk, step 1: one photo and one question.

We start the refund desk with the smallest thing that works. We send the photo
from one refund claim and ask one question: what condition is the egg in?
The answer comes back with a chance for every option.

Run it from the decisions folder:
    python steps/desk_step1_one_photo.py

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
# Step 1: the question about the photo
# ---------------------------------------------------------------------------
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
# Step 2: send the photo from claim C01
# ---------------------------------------------------------------------------
photo = "broken-02"
photo_bytes = open(f"eggs/{photo}.jpg", "rb").read()
url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()

decision = client.decisions.create(
    model="gpt-6-luna",
    input=[{"role": "user", "content": [{"type": "input_image", "image_url": url}]}],
    questions=[PHOTO_QUESTION],
)

# ---------------------------------------------------------------------------
# Step 3: print the answer
# ---------------------------------------------------------------------------
answer = decision.answers[0]
chances = {p.value: round(p.probability, 2) for p in answer.probabilities}
cost = decision.usage.input_tokens * 0.10 / 1_000_000
print(f"photo              eggs/{photo}.jpg")
print(f"the photo shows    {answer.choice}")
print(f"chance of each     {chances}")
print(f"cost               ${cost:.6f}")
