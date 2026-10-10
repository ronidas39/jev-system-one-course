"""Refund desk, step 1: one photo and one question.

We start the refund desk with the smallest thing that works. We send the photo
from one refund claim and ask one choice question: what condition is the egg
in? The answer comes back with a probability for every choice.

    python steps/desk_step1_one_photo.py

Author: Roni Das
Created: 2026-10-10
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the decisions/ folder
sys.path.insert(0, str(HERE))

from common import ask, check_key_present, cost_usd, image_data_url, make_client, odds, show  # noqa: E402

check_key_present()
client = make_client()

PHOTO_QUESTION = {
    "type": "choice", "name": "photo",
    "instructions": "Look only at the photo. What condition is the egg in?",
    "choices": [
        {"value": "clean", "description": "Whole egg, clean shell."},
        {"value": "dirty", "description": "Whole egg, dirty or stained shell."},
        {"value": "broken", "description": "Cracked, smashed or broken open."},
        {"value": "unclear", "description": "No egg, or the photo is too unclear to tell."},
    ],
}


def photo_part(photo: str) -> dict:
    """One egg photo, as an image part of the input."""
    return {"type": "input_image", "image_url": image_data_url(HERE / "eggs" / f"{photo}.jpg")}


photo = "broken-02"  # the photo sent with claim C01
decision, seconds = ask(client, input=[{"role": "user", "content": [photo_part(photo)]}],
                        questions=[PHOTO_QUESTION], script="steps/desk_step1_one_photo.py")
answer = decision.answers[0]
show("photo", f"eggs/{photo}.jpg")
show("photo shows", answer.choice)
show("confidence", f"{answer.confidence:.2f}")
show("probabilities", {k: round(v, 2) for k, v in odds(answer).items()})
show("input tokens / cost", f"{decision.usage.input_tokens} / ${cost_usd(decision.usage.input_tokens):.6f}")
show("time (s)", f"{seconds:.2f}")
