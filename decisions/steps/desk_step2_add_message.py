"""Refund desk, step 2: add the customer's message and a second question.

A real claim is a message plus a photo. Now we send both in the same call and
ask two separate questions: what the MESSAGE says is wrong, and what the PHOTO
shows. Two questions, because they are two different things to check.

    python steps/desk_step2_add_message.py

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

CLAIM_QUESTION = {
    "type": "choice", "name": "claim",
    "instructions": "Read only the customer's message. What do they say is wrong?",
    "choices": [
        {"value": "broken", "description": "An egg is cracked, smashed or broken open."},
        {"value": "dirty", "description": "The shells are dirty or stained."},
        {"value": "late", "description": "The order came late."},
        {"value": "other", "description": "Anything else."},
    ],
}
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


def message_part(message: str) -> dict:
    """The customer's words, as a text part of the input."""
    return {"type": "input_text", "text": f"Customer message: {message}"}


def photo_part(photo: str) -> dict:
    """One egg photo, as an image part of the input."""
    return {"type": "input_image", "image_url": image_data_url(HERE / "eggs" / f"{photo}.jpg")}


claim = {"id": "C01", "message": "Two of my eggs arrived smashed. The yolk is all over the box.",
         "photo": "broken-02"}
decision, seconds = ask(client,
                        input=[{"role": "user", "content": [message_part(claim["message"]),
                                                            photo_part(claim["photo"])]}],
                        questions=[CLAIM_QUESTION, PHOTO_QUESTION],
                        script="steps/desk_step2_add_message.py")
answers = {a.name: a for a in decision.answers}
show("claim", f"{claim['id']}: {claim['message']}")
show("message says", f"{answers['claim'].choice} (confidence {answers['claim'].confidence:.2f})")
show("photo shows", f"{answers['photo'].choice} (confidence {answers['photo'].confidence:.2f})")
show("photo probabilities", {k: round(v, 2) for k, v in odds(answers["photo"]).items()})
show("input tokens / cost", f"{decision.usage.input_tokens} / ${cost_usd(decision.usage.input_tokens):.6f}")
show("time (s)", f"{seconds:.2f}")
