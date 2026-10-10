"""Duplicate check, step 3 of 3: a second pair that only looks like a duplicate.

Adds a second pair, a parent company and its subsidiary in another country,
and a loop over both pairs. This step behaves like
usecases/04_duplicate_check.py.

    python usecases/steps/project4_step3_two_pairs.py

Author: Roni Das
Created: 2026-10-10
"""

import json

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import PAIR_QUESTIONS, pair_state

OUTCOME = {0: "keep separate", 1: "send to a person", 2: "merge"}

PAIRS = [
    {"a": {"name": "Saffron Peak Foods Pvt Ltd", "address": "12 Mill Road, Mumbai 400001",
           "country": "IN", "phone": "+91 22 4000 1234", "website": "saffronpeakfoods.in",
           "contact": {"name": "Priya Iyer", "role": "Buyer",
                       "email": "priya.iyer@saffronpeakfoods.in"}},
     "b": {"name": "M/s. SAFFRON PEAK FOODS PRIVATE LIMITED", "address": "12 Mill Rd, Bombay",
           "country": "IN", "phone": "02240001234", "website": None,
           "contact": {"name": "Priya Iyer", "role": "Buyer", "email": "priya.iyer@gmail.com"}}},
    {"a": {"name": "Kestrel Logistics Ltd", "address": "4 Park Street, Leeds", "country": "GB",
           "phone": "+44 113 555 0101", "website": "kestrellogistics.co.uk",
           "contact": {"name": "Tom Walsh", "role": "CTO",
                       "email": "tom.walsh@kestrellogistics.co.uk"}},
     "b": {"name": "Kestrel Logistics USA Inc.", "address": "88 Lake Avenue, Austin",
           "country": "US", "phone": "+1 512 555 0199", "website": "kestrellogistics.com",
           "contact": {"name": "Sarah Brooks", "role": "Buyer",
                       "email": "sarah.brooks@kestrellogistics.com"}}},
]


def main() -> None:
    """Check two pairs: one real duplicate, one parent and its subsidiary."""
    with make_jev_client() as client:
        for pair in PAIRS:
            state = pair_state(pair)
            result = ask_jev(client, state, PAIR_QUESTIONS)
            link = result.answer["link"]
            print(f"A: {pair['a']['name']}\nB: {pair['b']['name']}")
            print("checked by code:", json.dumps(state["checked_by_code"]))
            print(f"link score {link['score']:.2f}  probabilities {link['probabilities']}  "
                  f"confidence {link['confidence']:.2f}")
            print(f"same_name {result.answer['same_name']['noul']:.2f}   "
                  f"same_place {result.answer['same_place']['noul']:.2f}")
            print(f"decision: {OUTCOME[min(round(link['score']), 2)]}   "
                  f"({result.seconds:.3f} s, {result.input_tokens} tokens, ${result.usd:.7f})\n")


if __name__ == "__main__":
    main()
