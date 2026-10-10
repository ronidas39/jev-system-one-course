"""Duplicate check, step 2 of 3: plain code checks the phone, Jev reads the rest.

Comparing phone digits is arithmetic, so pair_state() does it in plain code
and puts the result into the state for Jev to read. It also adds two Noul
questions: same name, and same place.

    python usecases/steps/project4_step2_code_checks.py

Author: Roni Das
Created: 2026-10-10
"""

import json

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import PAIR_QUESTIONS, pair_state

OUTCOME = {0: "keep separate", 1: "send to a person", 2: "merge"}

PAIR = {
    "a": {"name": "Saffron Peak Foods Pvt Ltd", "address": "12 Mill Road, Mumbai 400001",
          "country": "IN", "phone": "+91 22 4000 1234", "website": "saffronpeakfoods.in",
          "contact": {"name": "Priya Iyer", "role": "Buyer",
                      "email": "priya.iyer@saffronpeakfoods.in"}},
    "b": {"name": "M/s. SAFFRON PEAK FOODS PRIVATE LIMITED", "address": "12 Mill Rd, Bombay",
          "country": "IN", "phone": "02240001234", "website": None,
          "contact": {"name": "Priya Iyer", "role": "Buyer", "email": "priya.iyer@gmail.com"}},
}


def main() -> None:
    """Check the one pair with the code checks and all three questions."""
    state = pair_state(PAIR)
    with make_jev_client() as client:
        result = ask_jev(client, state, PAIR_QUESTIONS)
    link = result.answer["link"]
    print(f"A: {PAIR['a']['name']}\nB: {PAIR['b']['name']}")
    print("checked by code:", json.dumps(state["checked_by_code"]))
    print(f"link score {link['score']:.2f}  probabilities {link['probabilities']}  "
          f"confidence {link['confidence']:.2f}")
    print(f"same_name {result.answer['same_name']['noul']:.2f}   "
          f"same_place {result.answer['same_place']['noul']:.2f}")
    print(f"decision: {OUTCOME[min(round(link['score']), 2)]}   "
          f"({result.seconds:.3f} s, {result.input_tokens} tokens, ${result.usd:.7f})")


if __name__ == "__main__":
    main()
