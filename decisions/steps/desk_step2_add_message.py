"""Refund desk, step 2: add the customer's message and a second question.

A real claim is a message plus a photo. Now we send both in the same call and
ask two separate questions: what the MESSAGE says is wrong, and what the PHOTO
shows. Two questions, because they are two different things to check.

Run it from the decisions folder:
    python steps/desk_step2_add_message.py

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
# Step 1: two questions, one about the message and one about the photo
# ---------------------------------------------------------------------------
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
# Step 2: send the message and the photo of claim C01 in one call
# ---------------------------------------------------------------------------
claim = {"id": "C01", "message": "Two of my eggs arrived smashed. The yolk is all over the box.",
         "photo": "broken-02"}
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

# ---------------------------------------------------------------------------
# Step 3: print both answers
# ---------------------------------------------------------------------------
cost = decision.usage.input_tokens * 0.10 / 1_000_000
print(f"claim              {claim['id']}: {claim['message']}")
print(f"the message says   {message_answer.choice} (how sure: {message_answer.confidence:.2f})")
print(f"the photo shows    {photo_answer.choice} (how sure: {photo_answer.confidence:.2f})")
print(f"cost               ${cost:.6f}")
