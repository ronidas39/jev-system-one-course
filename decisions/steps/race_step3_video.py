"""Lane race, step 3: the same race, but the road comes from a video.

The Decisions API reads text and pictures, not video. A video is a stack of
pictures called frames. The race video (race_images/clip.mp4) was cut into its
frames once, and they are saved in race_images/frames. At each step we send the
frame the car sees right now, or the last 3 frames, so the model can see the
road move. The rule is the same as step 2.

Run it from the decisions folder:
    python steps/race_step3_video.py        # 1 frame per step
    python steps/race_step3_video.py 3      # the last 3 frames per step

Author: Roni Das
"""

import base64
import json
import os
import sys
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

FRAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 1   # frames sent per step
CUTOFF = 0.80   # drive on only when the top lane has at least this probability
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
# Step 1: load the road (the video frames were cut once and saved)
# ---------------------------------------------------------------------------
road = json.load(open("race_images/road.json"))
client = OpenAI()

# ---------------------------------------------------------------------------
# Step 2: drive all 60 steps, sending video frames as pictures
# ---------------------------------------------------------------------------
car = 2   # the car starts in the middle lane
drove_on = slowed_down = crashed = 0
tokens = 0
start = time.perf_counter()
print(f"{FRAMES} frame(s) per step")
for step in road["steps"]:
    # The frame the car sees now, and the ones just before it, oldest first.
    numbers = sorted({max(0, step["frame"] - k) for k in range(FRAMES)})
    content = [{"type": "input_text", "text": LEGEND}]
    for n in numbers:
        frame = base64.b64encode(open(f"race_images/frames/frame_{n:05d}.jpg", "rb").read()).decode()
        content.append({"type": "input_image", "image_url": "data:image/jpeg;base64," + frame})
    if step["step"] == 10:
        print("step 10 sends", [f"frame_{n:05d}.jpg" for n in numbers])

    decision = client.decisions.create(model="gpt-6-luna", questions=[QUESTION],
                                       input=[{"role": "user", "content": content}])
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
            crashed += 1
        else:
            drove_on += 1
    else:
        slowed_down += 1

# ---------------------------------------------------------------------------
# Step 3: count what happened, and what it cost
# ---------------------------------------------------------------------------
seconds = time.perf_counter() - start
print(f"\n{FRAMES} frame(s): drove on {drove_on}, slowed down {slowed_down}, crashed {crashed} (60 steps)")
print(f"time: {seconds:.0f} seconds in all, cost: ${tokens * 0.10 / 1_000_000:.6f}")
