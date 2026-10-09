"""Decisions 3: a yes-or-no question (predicate) on six messages.

A predicate gives one number: the probability, from 0 to 1, that the
statement is true. These are the same six messages as handson/02_noul.py,
so you can put the two answers side by side.

Author: Roni Das
Created: 2026-10-09
"""

from common import ask, check_key_present, make_client

check_key_present()
client = make_client()

QUESTION = {
    "type": "predicate",
    "name": "is_human_escalation",
    "instructions": "Is the customer asking for a human agent?",
}

MESSAGES = [
    "Thanks, that fixed it!",
    "How do I reset my password?",
    "I need this sorted today, whatever it takes.",
    "Are you a bot?",
    "Is there any way to speak to someone about my invoice?",
    "I have asked three times now. Can I please just talk to a real person?",
]

print(f"{'message':<74} {'probability':>11}")
for message in MESSAGES:
    decision, seconds = ask(client, input=message, questions=[QUESTION], script="03_predicate.py")
    answer = decision.answers[0]
    print(f"{message:<74} {answer.probability:>11.2f}")
print(f"model: {decision.model}")
