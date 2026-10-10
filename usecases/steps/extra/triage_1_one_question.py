"""Triage, extra step (not on camera): ask Jev one question about one ticket.

One Choice question: which team should handle this ticket? Jev picks one of
the five teams and gives a probability for every team.

    python usecases/steps/extra/triage_1_one_question.py

Author: Roni Das
Created: 2026-10-10
"""

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import TICKET_QUESTIONS

TICKET = ("Hi, I was charged $49.99 twice for the Pro plan this month. Please give me my "
          "money back. This is the second time I am writing about this.")

QUESTIONS = {"team": TICKET_QUESTIONS["team"]}


def main() -> None:
    """Ask the one question and print the typed answer."""
    with make_jev_client() as client:
        result = ask_jev(client, TICKET, QUESTIONS)
    a = result.answer

    print(f"ticket: {TICKET}\n")
    print(f"team         {a['team']['choice']:<10} confidence {a['team']['confidence']:.2f}")
    print(f"             probabilities {a['team']['probabilities']}")


if __name__ == "__main__":
    main()
