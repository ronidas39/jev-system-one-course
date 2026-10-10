"""Lane race, step 1: draw the road and ask for one lane choice, for one step.

We build a short seeded road (seed 7, the same road the full race uses), draw
the road ahead as a picture, and send that picture with one choice question:
lane 1, lane 2 or lane 3. Then we print the three probabilities next to what
is really on the road, so we can check the answer ourselves.

    python steps/race_1_one_step.py

Author: Roni Das
Created: 2026-10-10
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the decisions/ folder
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "race"))

from common import ask, check_key_present, cost_usd, make_client, show  # noqa: E402
from play import LEGEND, QUESTION, png_url  # noqa: E402
from road import blocked_at_20m, describe, draw, make_road  # noqa: E402

check_key_present()
client = make_client()

road = make_road(seed=7, steps=1)
step = 0
picture = draw(road, step)
out = HERE / "results" / "race" / "mine"
out.mkdir(parents=True, exist_ok=True)
picture.save(out / "step0.png")

content = [{"type": "input_text", "text": LEGEND},
           {"type": "input_image", "image_url": png_url(picture)}]
decision, seconds = ask(client, input=[{"role": "user", "content": content}],
                        questions=[QUESTION], script="steps/race_1_one_step.py")
answer = decision.answers[0]

show("picture saved to", (out / "step0.png").relative_to(HERE))
show("what is really there", describe(road, step))
show("lanes blocked at 20 m", sorted(blocked_at_20m(road, step)))
show("model's lane", answer.choice)
for p in answer.probabilities:
    show(f"  P({p.value})", f"{p.probability:.2f}")
show("input tokens / cost", f"{decision.usage.input_tokens} / ${cost_usd(decision.usage.input_tokens):.6f}")
show("time (s)", f"{seconds:.2f}")
