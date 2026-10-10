"""Triage, step 4 of 4: plain code decides what to do with the ticket.

Adds the routing rule. If Jev is sure enough about the team, the ticket goes
there automatically; if not, a person looks at it. It also marks urgent
tickets and attaches the refund policy. You can pass your own ticket text.
This step behaves like usecases/01_ticket_triage.py.

    python usecases/steps/triage_4_routing.py
    python usecases/steps/triage_4_routing.py "My parcel never came and I want my money back"

Author: Roni Das
Created: 2026-10-10
"""

import sys

from typesafe_sdk import Noul

from jevcourse.calls import ask_jev, make_jev_client
from jevcourse.tasks import TICKET_QUESTIONS

TICKET = ("Hi, I was charged $49.99 twice for the Pro plan this month. Please give me my "
          "money back. This is the second time I am writing about this.")

ROUTE_AUTOMATICALLY_AT = 0.60
"""Our own starting threshold. Raise it if wrong routing is expensive for you."""

QUESTIONS = {
    **TICKET_QUESTIONS,
    "wants_refund": Noul(instructions="Is the customer asking for money back?"),
}


def main() -> None:
    """Ask, print the typed answers, then route the ticket with plain code."""
    ticket = sys.argv[1] if len(sys.argv) > 1 else TICKET
    with make_jev_client() as client:
        result = ask_jev(client, ticket, QUESTIONS)
    a = result.answer

    print(f"ticket: {ticket}\n")
    print(f"team         {a['team']['choice']:<10} confidence {a['team']['confidence']:.2f}")
    print(f"             probabilities {a['team']['probabilities']}")
    print(f"urgency      score {a['urgency']['score']:.2f} of 2   "
          f"confidence {a['urgency']['confidence']:.2f}")
    print(f"frustration  score {a['frustration']['score']:.2f} of 2   "
          f"confidence {a['frustration']['confidence']:.2f}")
    print(f"wants_refund probability of yes {a['wants_refund']['noul']:.2f}")
    print(f"\n{result.model}: {result.seconds:.3f} s, {result.input_tokens} input tokens, "
          f"${result.usd:.7f}")

    print("\nwhat the code decides:")
    if a["team"]["confidence"] >= ROUTE_AUTOMATICALLY_AT:
        print(f"  send to the {a['team']['choice']} team automatically")
    else:
        print("  not sure enough: put it in the human triage queue")
    if round(a["urgency"]["score"]) == 2:
        print("  mark as urgent")
    if a["wants_refund"]["noul"] > 0.5:
        print("  attach the refund policy for the agent")


if __name__ == "__main__":
    main()
