"""Lane race, step 3: the picture player. The full 60-step race, saved to a file.

The same rule as step 2, over all 60 steps of the road:

  - the top lane has 0.80 or more -> drive into that lane
    (if that lane has a barrier or cone at 20 m, that is a crash)
  - below 0.80, or a refusal      -> slow down and stay in our lane
    (if our lane has something at 20 m, we count a "close call")

Every step is saved to results/race/mine/picture-seed7.jsonl, so we can replay
the race and compare it with the other players later.

Run it from the decisions folder:
    python steps/race_step3_picture.py

Author: Roni Das
"""

import base64
import json
import os
import statistics
import time

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
# Step 1: load the road, and open the file we save every step to
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
client = OpenAI()
os.makedirs("results/race/mine", exist_ok=True)
saved = open("results/race/mine/picture-seed7.jsonl", "w")
saved.write(json.dumps({"player": "picture", "seed": 7, "steps": 60, "cutoff": CUTOFF}) + "\n")

# ---------------------------------------------------------------------------
# Step 2: drive all 60 steps
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
rows = []
print(f"cut-off {CUTOFF:.2f}")
print("step  lane_1  lane_2  lane_3  action                    ms")
for step in road["steps"]:
    picture = base64.b64encode(open("race_images/" + step["picture"], "rb").read()).decode()
    start = time.perf_counter()
    decision = client.decisions.create(
        model="gpt-6-luna",
        questions=[QUESTION],
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": LEGEND},
            {"type": "input_image", "image_url": "data:image/png;base64," + picture},
        ]}],
    )
    seconds = time.perf_counter() - start
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

    tokens = decision.usage.input_tokens
    row = {"step": step["step"], "probs": probs, "action": action, "car_lane": car,
           "blocked_20m": step["blocked_20m"], "tokens": tokens, "seconds": seconds,
           "usd": tokens * 0.10 / 1_000_000}   # $0.10 per 1M input tokens
    rows.append(row)
    saved.write(json.dumps(row) + "\n")
    print(f"{step['step']:>4}    {probs['lane_1']:.2f}    {probs['lane_2']:.2f}    "
          f"{probs['lane_3']:.2f}  {action:<22} {seconds * 1000:>5.0f}")
saved.close()

# ---------------------------------------------------------------------------
# Step 3: count what happened, and what it cost
# ---------------------------------------------------------------------------
actions = [r["action"] for r in rows]
crashes = actions.count("CRASH")
slow = sum(a.startswith("slow down") for a in actions)
close = actions.count("slow down, close call")
tokens = sum(r["tokens"] for r in rows)
ms = statistics.median(r["seconds"] for r in rows) * 1000
print(f"\npicture: {crashes} crashes, {slow} slow-downs ({close} close calls), "
      f"{len(rows) - crashes - slow} clean moves in {len(rows)} steps")
print(f"median {ms:.0f} ms per call, {tokens} input tokens, ${tokens * 0.10 / 1_000_000:.6f}")
print("saved: results/race/mine/picture-seed7.jsonl")
