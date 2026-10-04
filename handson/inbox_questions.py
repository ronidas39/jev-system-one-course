"""The three Smart Support Inbox questions, shared by exercises 11 and 12.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, Score

QUESTIONS = {
    "team": Choice(
        instructions="Which team should handle this support ticket?",
        criteria={
            "billing": "Charges, refunds, invoices, prices on a bill, subscriptions",
            "technical": "Bugs, errors, crashes, outages, API or integration problems",
            "shipping": "Delivery, tracking, couriers, damaged or lost parcels, addresses",
            "account": "Login, passwords, security, profile, users and permissions, data deletion",
            "sales": "Buying, plans, quotes, discounts, demos for new or bigger purchases",
        },
    ),
    "urgency": Score(
        instructions="How soon does this ticket need a response?",
        criteria=[
            "Can wait: no harm if answered in a few days",
            "Soon: should be handled within a day or two",
            "Today: work, money or security is blocked right now",
        ],
    ),
    "frustration": Score(
        instructions="How frustrated does the customer appear?",
        criteria=[
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, insulting, or threatening to leave or complain",
        ],
    ),
}
