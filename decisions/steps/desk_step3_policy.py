"""Refund desk, step 3: the shop's policy, and the "send to a person" path.

Now our code decides what happens to a claim, using the two answers:

  - any question refused              -> a person checks it
  - the message clearly claims broken or dirty (confidence 0.90 or more),
    and the photo shows that same problem with probability 0.90 or more
                                      -> refund automatically
  - anything else                     -> a person checks it

The model never refuses a refund on its own. Every "no" stays with a person.
We try three claims from returns_claims.json, one for each kind of outcome.

    python steps/desk_step3_policy.py

Author: Roni Das
Created: 2026-10-10
"""

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]  # the decisions/ folder
sys.path.insert(0, str(HERE))

from common import ask, check_key_present, cost_usd, image_data_url, make_client, show  # noqa: E402

AUTO_REFUND_AT = 0.90
"""Refund without a person only when P(photo shows what the message claims) is at least this."""

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


def decide(answers: dict) -> tuple[str, float | None]:
    """The shop's policy, in plain code. Returns the action and P(photo agrees)."""
    if any(a.type == "refusal" for a in answers.values()):
        return "person (a question was refused)", None
    said = answers["claim"].choice
    if said not in ("broken", "dirty"):
        return "person (not a damage claim)", None
    if answers["claim"].confidence < AUTO_REFUND_AT:
        return "person (message is not clear)", None
    agree = next(p.probability for p in answers["photo"].probabilities if p.value == said)
    if agree >= AUTO_REFUND_AT:
        return "REFUND automatically", agree
    return "person (photo does not clearly agree)", agree


def label(answer: Any) -> str:
    """One answer in words: the choice and how sure, or 'refused'."""
    if answer.type == "refusal":
        return "refused"
    return f"{answer.choice} (confidence {answer.confidence:.2f})"


claims = json.loads((HERE / "returns_claims.json").read_text())["claims"]
for claim in [c for c in claims if c["id"] in ("C01", "C05", "C07")]:
    decision, seconds = ask(client,
                            input=[{"role": "user", "content": [message_part(claim["message"]),
                                                                photo_part(claim["photo"])]}],
                            questions=[CLAIM_QUESTION, PHOTO_QUESTION],
                            script="steps/desk_step3_policy.py", note=claim["id"])
    answers = {a.name: a for a in decision.answers}
    action, agree = decide(answers)
    print()
    show("claim", f"{claim['id']}: {claim['message']}")
    show("message says", label(answers["claim"]))
    show("photo shows", label(answers["photo"]))
    show("P(photo agrees)", "-" if agree is None else f"{agree:.2f}")
    show("action", action)
    show("input tokens / cost", f"{decision.usage.input_tokens} / ${cost_usd(decision.usage.input_tokens):.6f}")
