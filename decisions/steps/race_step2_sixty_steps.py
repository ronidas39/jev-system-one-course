"""Lane race, step 2: drive 10 steps, with the 0.80 cut-off and the slow-down rule.

Now we ask once per step, and our code decides what the car does:

  - the top lane's probability is 0.80 or more -> drive into that lane
    (if that lane has a barrier or cone at 20 m, that is a crash)
  - below 0.80, or a refusal                   -> slow down and stay in our lane
    (if our lane has something 20 m ahead, we count a "close call")

We drive only 10 steps here to keep it short. The full race is 60 steps.

    python steps/race_step2_sixty_steps.py

Author: Roni Das
Created: 2026-10-10
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the decisions/ folder
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "race"))

from common import ask, check_key_present, cost_usd, make_client  # noqa: E402
from play import LEGEND, QUESTION, bars, png_url  # noqa: E402
from road import blocked_at_20m, draw, make_road  # noqa: E402

STEPS = 10
CUTOFF = 0.80
"""Drive into a lane only when the model gives it at least this probability."""

check_key_present()
client = make_client()
road = make_road(seed=7, steps=STEPS)


def lane_odds(step: int) -> tuple[dict[str, float] | None, int, float]:
    """Ask about the picture for one step. Returns (lane probabilities or None, tokens, seconds)."""
    content = [{"type": "input_text", "text": LEGEND},
               {"type": "input_image", "image_url": png_url(draw(road, step))}]
    decision, seconds = ask(client, input=[{"role": "user", "content": content}],
                            questions=[QUESTION], script="steps/race_step2_sixty_steps.py")
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


car, actions, tokens = 2, [], 0
print(f"seed 7, {STEPS} steps, cut-off {CUTOFF:.2f}")
print(f"{'step':>4}  {'lane 1':<15}  {'lane 2':<15}  {'lane 3':<15}  {'action':<16} {'ms':>5}")
for step in range(STEPS):
    probs, used, seconds = lane_odds(step)
    action, car = choose(probs, car, blocked_at_20m(road, step))
    actions.append(action)
    tokens += used
    print(f"{step:>4}  {bars(probs)}  {action:<16} {seconds * 1000:>5.0f}", flush=True)

crashes = actions.count("CRASH")
slow = sum(a.startswith("slow down") for a in actions)
print(f"\n{crashes} crashes, {slow} slow-downs ({actions.count('slow down, close call')} close calls), "
      f"{STEPS - crashes - slow} clean moves in {STEPS} steps")
print(f"{tokens} input tokens, ${cost_usd(tokens):.6f}")
