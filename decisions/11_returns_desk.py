"""Decisions 11: a small real-world project. A refund desk that reads text AND a photo.

A grocery delivery shop gets refund claims: a short message plus a photo.
For each claim we send the message and the photo together, in ONE call, with
two questions: what the MESSAGE says is wrong, and what the PHOTO shows.
Two separate questions, because OpenAI's guide says to separate different
concerns. Then a simple, written-down policy decides what happens:

  - any question refused              -> a person checks it
  - the message claims broken or dirty, and the photo shows that same
    problem with probability 0.90 or more -> refund automatically
  - anything else                     -> a person checks it

The shop never refuses a refund automatically. The model can only make the
easy "yes" faster. Every "no" stays with a person.

The claims are in returns_claims.json. They are made up for this course.

    python 11_returns_desk.py              # message and photo in one call
    python 11_returns_desk.py --separate   # the photo question gets the photo only

Why --separate: in one call, the photo question also sees the message. A
message that says "cracked" can pull the photo answer toward "broken". With
--separate, the photo is judged on its own, in a second call.

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import json
import time
from pathlib import Path

from common import ask, check_key_present, cost_usd, image_data_url, make_client

AUTO_REFUND_AT = 0.90
"""Refund without a person only when P(photo shows what the message claims) is at least this."""

HERE = Path(__file__).resolve().parent
check_key_present()
client = make_client()

QUESTIONS = [
    {"type": "choice", "name": "claim",
     "instructions": "Read only the customer's message. What do they say is wrong?",
     "choices": [
         {"value": "broken", "description": "An egg is cracked, smashed or broken open."},
         {"value": "dirty", "description": "The shells are dirty or stained."},
         {"value": "late", "description": "The order came late."},
         {"value": "other", "description": "Anything else."},
     ]},
    {"type": "choice", "name": "photo",
     "instructions": "Look only at the photo. What condition is the egg in?",
     "choices": [
         {"value": "clean", "description": "Whole egg, clean shell."},
         {"value": "dirty", "description": "Whole egg, dirty or stained shell."},
         {"value": "broken", "description": "Cracked, smashed or broken open."},
         {"value": "unclear", "description": "No egg, or the photo is too unclear to tell."},
     ]},
]


def decide(answers: dict) -> tuple[str, float | None]:
    """The shop's policy, in plain code. Returns the action and P(photo agrees)."""
    if any(a.type == "refusal" for a in answers.values()):
        return "person (a question was refused)", None
    said = answers["claim"].choice
    if said not in ("broken", "dirty"):
        return "person (not a damage claim)", None
    agree = next(p.probability for p in answers["photo"].probabilities if p.value == said)
    if agree >= AUTO_REFUND_AT:
        return "REFUND automatically", agree
    return "person (photo does not clearly agree)", agree


parser = argparse.ArgumentParser(description="A refund desk that reads text and a photo.")
parser.add_argument("--separate", action="store_true",
                    help="ask about the photo in its own call, without the message")
args = parser.parse_args()


def message_part(claim: dict) -> dict:
    return {"type": "input_text", "text": f"Customer message: {claim['message']}"}


def photo_part(claim: dict) -> dict:
    return {"type": "input_image", "image_url": image_data_url(HERE / "eggs" / f"{claim['photo']}.jpg")}


claims = json.loads((HERE / "returns_claims.json").read_text())["claims"]
start = time.perf_counter()
tokens = 0
actions = []
print(f"{'id':<4} {'photo file':<10} {'message says':<12} {'photo shows':<12} {'P(agree)':>8}  action")
for claim in claims:
    if args.separate:
        first, _ = ask(client, input=claim["message"], questions=QUESTIONS[:1],
                       script="11_returns_desk.py", note=claim["id"] + " message")
        second, _ = ask(client, input=[{"role": "user", "content": [photo_part(claim)]}],
                        questions=QUESTIONS[1:], script="11_returns_desk.py",
                        note=claim["id"] + " photo")
        tokens += first.usage.input_tokens + second.usage.input_tokens
        answers = {a.name: a for a in [*first.answers, *second.answers]}
    else:
        decision, _ = ask(client, input=[{"role": "user", "content": [message_part(claim),
                                                                      photo_part(claim)]}],
                          questions=QUESTIONS, script="11_returns_desk.py", note=claim["id"])
        tokens += decision.usage.input_tokens
        answers = {a.name: a for a in decision.answers}
    action, agree = decide(answers)
    actions.append(action)
    said = answers["claim"].choice if answers["claim"].type == "choice" else "refused"
    shows = answers["photo"].choice if answers["photo"].type == "choice" else "refused"
    p = "-" if agree is None else f"{agree:.2f}"
    print(f"{claim['id']:<4} {claim['photo']:<10} {said:<12} {shows:<12} {p:>8}  {action}")

seconds = time.perf_counter() - start
auto = sum(a.startswith("REFUND") for a in actions)
print()
mode = "two calls per claim (photo on its own)" if args.separate else "one call per claim"
print(f"{mode}. {len(claims)} claims in {seconds:.1f} s: {auto} refunded automatically, "
      f"{len(claims) - auto} sent to a person")
print(f"input tokens {tokens}, cost ${cost_usd(tokens):.6f} "
      f"(about ${cost_usd(tokens) / len(claims) * 1000:.4f} per 1,000 claims)")
