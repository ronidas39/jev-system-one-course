"""Lane race, step 4: the video-frame player. Same race, but the road comes from a video.

Now we ask once per step, and our code decides what the car does:

  - the top lane's probability is 0.80 or more -> drive into that lane
    (if that lane has a barrier or cone at 20 m, that is a crash)
  - below 0.80, or a refusal                   -> slow down and stay in our lane
    (if our lane has something 20 m ahead, we count a "close call")

The Decisions API reads text and images, not video. So we first write the
drive as a short MP4 clip, then at each step cut out the one frame the car is
seeing right now and send that frame as an image. Everything else is the same
as step 3. It is the same player as `python race/play.py --player clip1`.

    python steps/race_4_video_frames.py

Author: Roni Das
Created: 2026-10-10
"""

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the decisions/ folder
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "race"))

from common import MODEL, ask, check_key_present, cost_usd, image_data_url, make_client  # noqa: E402
from play import LEGEND, QUESTION, bars, write_replay  # noqa: E402
from road import SUB, blocked_at_20m, frames_from_clip, make_clip, make_road  # noqa: E402

STEPS = 60
CUTOFF = 0.80
"""Drive into a lane only when the model gives it at least this probability."""

check_key_present()
client = make_client()
road = make_road(seed=7, steps=STEPS)
out = HERE / "results" / "race" / "mine"
clip = out / f"clip-seed7-{STEPS}steps.mp4"
if not clip.exists():
    make_clip(road, STEPS + 1, clip)
    print(f"made the clip {clip.relative_to(HERE)} ({(STEPS + 1) * SUB} frames)")


def lane_odds(step: int) -> tuple[dict[str, float] | None, int, float]:
    """Ask about the video frame for one step. Returns (lane probabilities or None, tokens, seconds)."""
    frame = frames_from_clip(clip, [step * SUB], out / "frames-seed7")[0]
    content = [{"type": "input_text", "text": LEGEND + " These are 1 frame(s) from a video of the "
                "drive, oldest first. The road moves toward the car."},
               {"type": "input_image", "image_url": image_data_url(frame)}]
    decision, seconds = ask(client, input=[{"role": "user", "content": content}],
                            questions=[QUESTION], script="steps/race_4_video_frames.py")
    answer = decision.answers[0]
    if answer.type == "refusal":
        return None, decision.usage.input_tokens, seconds
    return {str(p.value): p.probability for p in answer.probabilities}, decision.usage.input_tokens, seconds


def choose(probs: dict[str, float] | None, car: int, blocked: set[int]) -> tuple[str, int]:
    """Our rule: drive only above the cut-off, otherwise slow down. Returns (action, new lane)."""
    top = max(probs, key=probs.get) if probs else None
    if probs and probs[top] >= CUTOFF:
        lane = int(top[-1])
        return ("CRASH" if lane in blocked else f"drive lane {lane}"), lane
    if car in blocked:
        return "slow down, close call", car
    return "slow down", car


meta = {"meta": True, "player": "clip1", "seed": 7, "steps": STEPS, "cutoff": CUTOFF, "model": MODEL}
steps_file = out / "clip1-seed7.jsonl"
steps_file.write_text(json.dumps(meta) + "\n")  # every step is added as it happens

car, rows = 2, []
print(f"clip1, seed 7, {STEPS} steps, cut-off {CUTOFF:.2f}")
print(f"{'step':>4}  {'lane 1':<15}  {'lane 2':<15}  {'lane 3':<15}  {'action':<16} {'ms':>5}")
for step in range(STEPS):
    probs, used, seconds = lane_odds(step)
    blocked = blocked_at_20m(road, step)
    action, car = choose(probs, car, blocked)
    rows.append({"step": step, "probs": probs, "action": action, "car_lane": car,
                 "blocked_20m": sorted(blocked), "tokens": used, "seconds": round(seconds, 4),
                 "usd": cost_usd(used)})
    with steps_file.open("a") as fh:
        fh.write(json.dumps(rows[-1]) + "\n")
    print(f"{step:>4}  {bars(probs)}  {action:<16} {seconds * 1000:>5.0f}", flush=True)

write_replay(road, rows, meta, out / "clip1-seed7.html")
actions = [r["action"] for r in rows]
crashes = actions.count("CRASH")
slow = sum(a.startswith("slow down") for a in actions)
tokens = sum(r["tokens"] for r in rows)
ms = statistics.median(r["seconds"] for r in rows) * 1000
print(f"\nclip1: {crashes} crashes, {slow} slow-downs ({actions.count('slow down, close call')} "
      f"close calls), {STEPS - crashes - slow} clean moves in {STEPS} steps")
print(f"median {ms:.0f} ms per call, {tokens} input tokens, ${cost_usd(tokens):.6f} "
      f"(${cost_usd(tokens) / STEPS * 1000:.4f} per 1,000 steps)")
print(f"saved: {steps_file.relative_to(HERE)}")
print(f"replay: {(out / 'clip1-seed7.html').relative_to(HERE)}")
