"""Lane race, step 4: the video-frame player. Same race, but the road comes from a video.

The Decisions API reads text and images, not video. A video is a stack of
pictures called frames. The race video (race_images/clip.mp4) was cut into its
frames once, and they are saved in race_images/frames. At each step we send the
frame the car sees right now, or the last 3 frames, so the model can see the
road move. The rule is the same as step 3.

Run it from the decisions folder:
    python steps/race_step4_video_frames.py        # 1 frame per step
    python steps/race_step4_video_frames.py 3      # the last 3 frames per step

Author: Roni Das
"""

import base64
import json
import os
import statistics
import sys
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 1   # frames sent per step
CUTOFF = 0.80   # drive only when the top lane has at least this probability
LEGEND = ("Top-down view of a three-lane road. Our car is just below the picture, driving up. "
          "Orange striped boxes are barriers. Orange triangles are cones. The distance from our "
          f"car is written on the left. These are {FRAMES} frame(s) from a video of the drive, "
          "oldest first. The road moves toward the car.")
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
player = f"clip{FRAMES}"
os.makedirs("results/race/mine", exist_ok=True)
saved = open(f"results/race/mine/{player}-seed7.jsonl", "w")
saved.write(json.dumps({"player": player, "seed": 7, "steps": 60, "cutoff": CUTOFF}) + "\n")

# ---------------------------------------------------------------------------
# Step 2: drive all 60 steps, sending video frames as images
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
rows = []
print(f"{player}: {FRAMES} frame(s) per step, cut-off {CUTOFF:.2f}")
for step in road["steps"]:
    # The frame the car sees now, and the ones just before it, oldest first.
    numbers = sorted({max(0, step["frame"] - k) for k in range(FRAMES)})
    content = [{"type": "input_text", "text": LEGEND}]
    for n in numbers:
        frame = base64.b64encode(open(f"race_images/frames/frame_{n:05d}.jpg", "rb").read()).decode()
        content.append({"type": "input_image", "image_url": "data:image/jpeg;base64," + frame})
    if step["step"] == 10:
        print("   step 10 sends", [f"frame_{n:05d}.jpg" for n in numbers])

    start = time.perf_counter()
    decision = client.decisions.create(model="gpt-6-luna", questions=[QUESTION],
                                       input=[{"role": "user", "content": content}])
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
print(f"\n{player}: {crashes} crashes, {slow} slow-downs ({close} close calls), "
      f"{len(rows) - crashes - slow} clean moves in {len(rows)} steps")
print(f"median {ms:.0f} ms per call, {tokens} input tokens, ${tokens * 0.10 / 1_000_000:.6f}")
print(f"saved: results/race/mine/{player}-seed7.jsonl")
