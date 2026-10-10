"""Lane race, extra: drive 10 steps, with the 0.80 cut-off.

Now we ask once per step, and our code decides what the car does:

  - the top lane has 0.80 or more -> drive into that lane
    (if that lane has a barrier or cone at 20 m, that is a crash)
  - below 0.80, or a refusal      -> slow down and stay in our lane
    (if our lane has something at 20 m, we count a "close call")

Run it from the decisions folder:
    python steps/extra/race_ten_steps.py

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

CUTOFF = 0.80   # drive only when the top lane has at least this probability
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
# Step 1: load the road (the pictures were drawn once and saved)
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
client = OpenAI()

# ---------------------------------------------------------------------------
# Step 2: drive 10 steps: ask about each picture, then apply our rule
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
actions = []
print(f"cut-off {CUTOFF:.2f}")
print("step  lane_1  lane_2  lane_3  action")
for step in road["steps"][:10]:
    picture = base64.b64encode(open("race_images/" + step["picture"], "rb").read()).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        questions=[QUESTION],
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": LEGEND},
            {"type": "input_image", "image_url": "data:image/png;base64," + picture},
        ]}],
    )
    answer = decision.answers[0]
    if answer.type == "refusal":   # no answer counts as "not sure"
        probs = {"lane_1": 0.0, "lane_2": 0.0, "lane_3": 0.0}
    else:
        probs = {p.value: p.probability for p in answer.probabilities}
    top = max(probs, key=probs.get)

    # Our rule: drive only at the cut-off or above, otherwise slow down.
    if probs[top] >= CUTOFF:
        car = int(top[-1])
        action = "CRASH" if car in step["blocked_20m"] else f"drive lane {car}"
    elif car in step["blocked_20m"]:
        action = "slow down, close call"
    else:
        action = "slow down"
    actions.append(action)
    print(f"{step['step']:>4}    {probs['lane_1']:.2f}    {probs['lane_2']:.2f}    "
          f"{probs['lane_3']:.2f}  {action}")

# ---------------------------------------------------------------------------
# Step 3: count what happened
# ---------------------------------------------------------------------------
crashes = actions.count("CRASH")
slow = sum(a.startswith("slow down") for a in actions)
close = actions.count("slow down, close call")
print(f"\n{crashes} crashes, {slow} slow-downs ({close} close calls), "
      f"{len(actions) - crashes - slow} clean moves in {len(actions)} steps")
