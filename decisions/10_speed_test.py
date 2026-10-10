"""Decisions 10, part 3: a small speed test against a JSON answer.

The same ten photos and the same question, asked two ways, back to back:
  - the Decisions API, which sends back a probability for every choice
  - the Responses API, where the same model writes its answer as JSON
We time each call on this machine and count how often each matches my label.

Run it from the decisions folder:
    python 10_speed_test.py

Author: Roni Das
"""

import base64
import csv
import json
import os
import statistics
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()
OPTIONS = ["clean", "dirty", "cracked", "unclear"]

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
JSON_FORMAT = {
    "type": "json_schema", "name": "egg", "strict": True,
    "schema": {"type": "object", "additionalProperties": False, "required": ["condition"],
               "properties": {"condition": {"type": "string", "enum": OPTIONS}}},
}

# ---------------------------------------------------------------------------
# Step 1: pick ten photos (every third one, so all kinds of egg are in)
# ---------------------------------------------------------------------------
labels = {row["egg"]: row["condition"] for row in csv.DictReader(open("eggs/labels.csv"))}
eggs = list(labels)[::3][:10]

# ---------------------------------------------------------------------------
# Step 2: ask each photo both ways and time each call
# ---------------------------------------------------------------------------
times = {"decisions": [], "responses": []}
right = {"decisions": 0, "responses": 0}
print(f"{'photo':<10} {'my label':<9} {'decisions':<16} responses (writes JSON)")
for egg in eggs:
    photo_bytes = open(f"eggs/{egg}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()

    start = time.perf_counter()
    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=[QUESTION],
    )
    times["decisions"].append((time.perf_counter() - start) * 1000)
    answer = decision.answers[0]
    top = max(answer.probabilities, key=lambda p: p.probability)
    if top.value == labels[egg]:
        right["decisions"] += 1

    start = time.perf_counter()
    written = client.responses.create(
        model="gpt-6-luna",
        reasoning={"effort": "none"},
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line. Is the shell clean, "
             "dirty, cracked, or is the photo unclear? Answer in the JSON schema."},
            {"type": "input_image", "image_url": url},
        ]}],
        text={"format": JSON_FORMAT},
    )
    times["responses"].append((time.perf_counter() - start) * 1000)
    said = json.loads(written.output_text)["condition"]
    if said == labels[egg]:
        right["responses"] += 1

    decisions_text = f"{top.value} {top.probability:.2f}"
    print(f"{egg:<10} {labels[egg]:<9} {decisions_text:<16} {said}")

# ---------------------------------------------------------------------------
# Step 3: the middle time and the matches, for each way
# ---------------------------------------------------------------------------
print()
for way in ["decisions", "responses"]:
    print(f"{way:<10} median {statistics.median(times[way]):5.0f} ms, "
          f"matched my label {right[way]}/{len(eggs)}")
