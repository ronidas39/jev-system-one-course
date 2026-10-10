"""Lane race, step 2: the full race. 60 pictures, one question each, and our rule.

At every step we send the picture of the road ahead, and our code decides:

  - the top lane has 0.80 or more -> the car drives on in that lane
    (if that lane has a barrier or cone at 20 m, the car crashes)
  - below 0.80                    -> the car slows down and stays in its lane

Run it from the decisions folder:
    python steps/race_step2_full_race.py

Author: Roni Das
"""

import base64
import json
import os
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

CUTOFF = 0.80   # drive on only when the top lane has at least this probability
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
# Step 1: load the road (the 60 pictures were drawn once and saved)
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
client = OpenAI()

# ---------------------------------------------------------------------------
# Step 2: drive all 60 steps: ask about each picture, then apply our rule
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
drove_on = slowed_down = crashed = 0
tokens = 0
start = time.perf_counter()
print("step  lane_1  lane_2  lane_3  what the car did")
for step in road["steps"]:
    picture = base64.b64encode(open("race_images/" + step["picture"], "rb").read()).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        questions=[QUESTION],
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": LEGEND},
            {"type": "input_image", "image_url": "data:image/png;base64," + picture},
        ]}],
    )
    tokens += decision.usage.input_tokens
    answer = decision.answers[0]
    if answer.type == "refusal":   # no answer counts as "not sure"
        probs = {"lane_1": 0.0, "lane_2": 0.0, "lane_3": 0.0}
    else:
        probs = {p.value: p.probability for p in answer.probabilities}
    best = max(probs, key=probs.get)

    # Our rule: drive on only at the cut-off or above, otherwise slow down.
    if probs[best] >= CUTOFF:
        car = int(best[-1])
        if car in step["blocked_20m"]:
            action = f"crashed in lane {car}"
            crashed += 1
        else:
            action = f"drove on in lane {car}"
            drove_on += 1
    else:
        action = "slowed down"
        slowed_down += 1
    print(f"{step['step']:>4}    {probs['lane_1']:.2f}    {probs['lane_2']:.2f}    "
          f"{probs['lane_3']:.2f}  {action}")

# ---------------------------------------------------------------------------
# Step 3: count what happened, and what it cost
# ---------------------------------------------------------------------------
seconds = time.perf_counter() - start
print(f"\npictures: drove on {drove_on}, slowed down {slowed_down}, crashed {crashed} (60 steps)")
print(f"time: {seconds:.0f} seconds in all, cost: ${tokens * 0.10 / 1_000_000:.6f}")
