"""Duplicate check, step 1 of 3: are these two company records one company?

One Score question about one pair of records: 0 means two different
companies, 1 means a person should check, 2 means the same company. Plain
code turns the score into a decision.

    python usecases/steps/dupcheck_1_link_score.py

Author: Roni Das
Created: 2026-10-10
"""

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import PAIR_QUESTIONS

OUTCOME = {0: "keep separate", 1: "send to a person", 2: "merge"}

QUESTIONS = {"link": PAIR_QUESTIONS["link"]}

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
    """Ask the one question about the one pair."""
    state = {"record_a": PAIR["a"], "record_b": PAIR["b"]}
    with make_jev_client() as client:
        result = ask_jev(client, state, QUESTIONS)
    link = result.answer["link"]
    print(f"A: {PAIR['a']['name']}\nB: {PAIR['b']['name']}")
    print(f"link score {link['score']:.2f}  probabilities {link['probabilities']}  "
          f"confidence {link['confidence']:.2f}")
    print(f"decision: {OUTCOME[min(round(link['score']), 2)]}   "
          f"({result.seconds:.3f} s, {result.input_tokens} tokens, ${result.usd:.7f})")


if __name__ == "__main__":
    main()
