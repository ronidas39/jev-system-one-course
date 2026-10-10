"""Lane race, step 1: one picture of the road, one lane choice.

The road pictures were drawn once and saved in the race_images folder. Here we
load the picture for the first step and send it to the Decisions API with one
choice question: lane 1, lane 2 or lane 3. Then we print what is really on the
road, so we can check the answer ourselves.

Run it from the decisions folder:
    python steps/race_step1_one_step.py

Author: Roni Das
"""

import base64
import json
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

# ---------------------------------------------------------------------------
# Step 1: load the road and the picture for the first step
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
step = road["steps"][0]
picture = base64.b64encode(open("race_images/" + step["picture"], "rb").read()).decode()

print("picture:", "race_images/" + step["picture"])
print("what is really there:", step["text"])
print("lanes blocked at 20 m:", step["blocked_20m"])

# ---------------------------------------------------------------------------
# Step 2: the question, and a legend that says what the shapes mean
# ---------------------------------------------------------------------------
LEGEND = ("Top-down view of a three-lane road. Our car is just below the picture, driving up. "
          "Orange striped boxes are barriers. Orange triangles are cones. The distance from our "
          "car is written on the left.")
QUESTION = {
    "type": "choice",
    "name": "lane",
    "instructions": "This shows the road ahead of our car, with distances. Which lane should the "
                    "car drive in? Choose a lane with no barrier or cone at 20 metres, and if you "
                    "can, none at 40 metres either.",
    "choices": [
        {"value": "lane_1", "description": "Lane 1, on the left."},
        {"value": "lane_2", "description": "Lane 2, in the middle."},
        {"value": "lane_3", "description": "Lane 3, on the right."},
    ],
}

# ---------------------------------------------------------------------------
# Step 3: send the legend and the picture, and print the answer
# ---------------------------------------------------------------------------
client = OpenAI()
decision = client.decisions.create(
    model="gpt-6-luna",
    questions=[QUESTION],
    input=[{"role": "user", "content": [
        {"type": "input_text", "text": LEGEND},
        {"type": "input_image", "image_url": "data:image/png;base64," + picture},
    ]}],
)
answer = decision.answers[0]

print("\nmodel's lane:", answer.choice)
for p in answer.probabilities:
    print(f"   {p.value}: {p.probability:.2f}")

tokens = decision.usage.input_tokens
print(f"input tokens: {tokens}, cost ${tokens * 0.10 / 1_000_000:.6f}")  # $0.10 per 1M input tokens
