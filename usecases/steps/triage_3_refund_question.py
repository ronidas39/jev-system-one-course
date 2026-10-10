"""Triage, step 3 of 4: add a yes-or-no question, still one call.

Adds a Noul question: is the customer asking for money back? Jev answers
with the probability of yes. Now the call holds all three question types.

    python usecases/steps/triage_3_refund_question.py

Author: Roni Das
Created: 2026-10-10
"""

from typesafe_sdk import Noul

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import TICKET_QUESTIONS

TICKET = ("Hi, I was charged $49.99 twice for the Pro plan this month. Please give me my "
          "money back. This is the second time I am writing about this.")

QUESTIONS = {
    **TICKET_QUESTIONS,
    "wants_refund": Noul(instructions="Is the customer asking for money back?"),
}


def main() -> None:
    """Ask the four questions and print the typed answers."""
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
    print(f"wants_refund probability of yes {a['wants_refund']['noul']:.2f}")
    print(f"\n{result.model}: {result.seconds:.3f} s, {result.input_tokens} input tokens, "
          f"${result.usd:.7f}")


if __name__ == "__main__":
    main()
