"""Lane race, step 6: Jev reads the road as text. Same race, same 0.80 rule.

Jev reads text only, so it plays the text version of the game from step 5:
the same words from road.json, the same three lanes, the same rule.

Run it from the decisions folder:
    python steps/race_step6_jev_text.py

Author: Roni Das
"""

import json
import os
import statistics
import time

from typesafe_sdk import Choice, TypeSafeClient

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("TYPESAFE_API_KEY="):
        os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip()

CUTOFF = 0.80   # drive only when the top lane has at least this probability
QUESTION = {
    "lane": Choice(
        instructions="This shows the road ahead of our car, with distances. Which lane should the "
                     "car drive in? Choose a lane with no barrier or cone at 20 metres, and if you "
                     "can, none at 40 metres either.",
        criteria={
            "lane_1": "Lane 1, on the left.",
            "lane_2": "Lane 2, in the middle.",
            "lane_3": "Lane 3, on the right.",
        },
    )
}

# ---------------------------------------------------------------------------
# Step 1: load the road, and open the file we save every step to
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
os.makedirs("results/race/mine", exist_ok=True)
saved = open("results/race/mine/jev-seed7.jsonl", "w")
saved.write(json.dumps({"player": "jev", "seed": 7, "steps": 60, "cutoff": CUTOFF}) + "\n")

# ---------------------------------------------------------------------------
# Step 2: drive all 60 steps, sending the road as text to Jev
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
rows = []
print(f"cut-off {CUTOFF:.2f}")
print("step  lane_1  lane_2  lane_3  action")
with TypeSafeClient() as client:
    for step in road["steps"]:
        start = time.perf_counter()
        answer = client.system_one(state=step["text"], questions=QUESTION)
        seconds = time.perf_counter() - start
        probs = answer.answers["lane"].probabilities   # lane name -> probability
        top = max(probs, key=probs.get)

        # Our rule: drive only at the cut-off or above, otherwise slow down.
        if probs[top] >= CUTOFF:
            car = int(top[-1])
            action = "CRASH" if car in step["blocked_20m"] else f"drive lane {car}"
        elif car in step["blocked_20m"]:
            action = "slow down, close call"
        else:
            action = "slow down"

        tokens = answer.usage.input_tokens
        row = {"step": step["step"], "probs": probs, "action": action, "car_lane": car,
               "blocked_20m": step["blocked_20m"], "tokens": tokens, "seconds": seconds,
               "usd": tokens * 0.042 / 1_000_000}   # Jev: $0.042 per 1M input tokens
        rows.append(row)
        saved.write(json.dumps(row) + "\n")
        print(f"{step['step']:>4}    {probs['lane_1']:.2f}    {probs['lane_2']:.2f}    "
              f"{probs['lane_3']:.2f}  {action}")
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
print(f"\njev: {crashes} crashes, {slow} slow-downs ({close} close calls), "
      f"{len(rows) - crashes - slow} clean moves in {len(rows)} steps")
print(f"median {ms:.0f} ms per call, {tokens} input tokens, ${tokens * 0.042 / 1_000_000:.6f}")
print("saved: results/race/mine/jev-seed7.jsonl")
