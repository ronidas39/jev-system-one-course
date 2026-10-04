"""Exercise 3: pick one option from a list (Choice).

Prints the chosen option, the probability of every option, and confidence.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, TypeSafeClient

from common import check_key_present, log_call, show, timed

check_key_present()

TEAM = Choice(
    instructions="Which team should handle this?",
    criteria={
        "returns": "Exchanges, wrong or damaged items",
        "shipping": "Delivery status, delays, lost packages",
        "billing": "Charges, invoices, payment problems",
    },
)

TICKETS = [
    "My running shoes arrived in the wrong size. Can I swap them for a size 10?",
    "Shoes arrived two weeks late and in the wrong size. Also I see two charges "
    "of $120 on my card. What are you going to do about this?",
]

with TypeSafeClient() as client:
    for ticket in TICKETS:
        response, seconds = timed(client.system_one, state=ticket, questions={"team": TEAM})
        answer = response.answers["team"]
        print()
        show("ticket", ticket[:70] + ("..." if len(ticket) > 70 else ""))
        show("choice", answer.choice)
        show("probabilities", answer.probabilities)
        show("confidence", answer.confidence)
        show("time (s)", f"{seconds:.3f}")
        log_call("03_choice.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds)
print()
show("model", response.model)
