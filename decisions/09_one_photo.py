"""Decisions 9: send a photo. Three questions about one egg, in one call.

The photo goes inside the input as a base64 data URL, next to a line of text.
We ask a choice (clean, dirty, cracked, unclear), a predicate (is there a
crack) and a score (how dirty), for three eggs from the eggs/ folder.

Author: Roni Das
Created: 2026-10-09
"""

from pathlib import Path

from common import ask, check_key_present, cost_usd, image_data_url, make_client, odds, show
from egg_questions import EGG_QUESTIONS

check_key_present()
client = make_client()
EGGS = Path(__file__).resolve().parent / "eggs"

for egg in ["box10-03", "duck-04", "broken-02"]:
    url = image_data_url(EGGS / f"{egg}.jpg")
    decision, seconds = ask(
        client,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=EGG_QUESTIONS,
        script="09_one_photo.py",
    )
    answers = {a.name: a for a in decision.answers}
    print()
    show("photo", f"eggs/{egg}.jpg  (data URL: {len(url):,} characters)")
    show("condition", answers["condition"].choice)
    show("  probabilities", odds(answers["condition"]))
    show("visible crack", f"{answers['visible_crack'].probability:.2f}")
    show("dirt level (0 to 2)", f"{answers['dirt_level'].score:.2f}")
    show("input tokens / cost", f"{decision.usage.input_tokens} / ${cost_usd(decision.usage.input_tokens):.8f}")
    show("time (s)", f"{seconds:.3f}")
