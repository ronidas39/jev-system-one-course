"""Decisions 4: pick one option from a list (choice).

Prints the chosen option, the probability of every option, and the
confidence. Same team list and tickets as handson/03_choice.py.

Author: Roni Das
Created: 2026-10-09
"""

from common import ask, check_key_present, make_client, show

check_key_present()
client = make_client()

TEAM = {
    "type": "choice",
    "name": "team",
    "instructions": "Which team should handle this?",
    "choices": [
        {"value": "returns", "description": "Exchanges, wrong or damaged items"},
        {"value": "shipping", "description": "Delivery status, delays, lost packages"},
        {"value": "billing", "description": "Charges, invoices, payment problems"},
    ],
}

TICKETS = [
    "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
    "Shoes arrived two weeks late and in the wrong size. Also I see two charges "
    "of $120 on my card. What are you going to do about this?",
]

for ticket in TICKETS:
    decision, seconds = ask(client, input=ticket, questions=[TEAM], script="04_choice.py")
    answer = decision.answers[0]
    print()
    show("ticket", ticket[:70] + ("..." if len(ticket) > 70 else ""))
    show("choice", answer.choice)
    show("probabilities", {p.value: p.probability for p in answer.probabilities})
    show("confidence", answer.confidence)
    show("time (s)", f"{seconds:.3f}")
print()
show("model", decision.model)
