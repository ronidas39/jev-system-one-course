"""Triage, extra step (not on camera): three questions about the same ticket, in one call.

Adds two Score questions next to the Choice: urgency and frustration, each a
number from 0 to 2. It also prints the time, the tokens and the cost.

    python usecases/steps/extra/triage_2_three_questions.py

Author: Roni Das
Created: 2026-10-10
"""

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import TICKET_QUESTIONS

TICKET = ("Hi, I was charged $49.99 twice for the Pro plan this month. Please give me my "
          "money back. This is the second time I am writing about this.")

QUESTIONS = {**TICKET_QUESTIONS}


def main() -> None:
    """Ask the three questions and print the typed answers."""
    with make_jev_client() as client:
        result = ask_jev(client, TICKET, QUESTIONS)
    a = result.answer

    print(f"ticket: {TICKET}\n")
    print(f"team         {a['team']['choice']:<10} confidence {a['team']['confidence']:.2f}")
    print(f"             probabilities {a['team']['probabilities']}")
    print(f"urgency      score {a['urgency']['score']:.2f} of 2   "
          f"confidence {a['urgency']['confidence']:.2f}")
    print(f"frustration  score {a['frustration']['score']:.2f} of 2   "
          f"confidence {a['frustration']['confidence']:.2f}")
    print(f"\n{result.model}: {result.seconds:.3f} s, {result.input_tokens} input tokens, "
          f"${result.usd:.7f}")


if __name__ == "__main__":
    main()
