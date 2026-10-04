"""Exercise 2: a yes/no question (Noul) on six messages.

These six messages are the ones TypeSafe uses on its Noul docs page, so you
can compare your numbers with the numbers TypeSafe recorded there.
All six messages go in one loop, one request per message, because each
message is a different state.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Noul, TypeSafeClient

from common import check_key_present, log_call, timed

check_key_present()

QUESTION = {"is_human_escalation": Noul(instructions="Is the customer asking for a human agent?")}

# Each pair: (message, value TypeSafe recorded on docs.typesafe.ai/primitives/noul for jev-1.13.0)
MESSAGES = [
    ("Thanks, that fixed it!", 0.02),
    ("How do I reset my password?", 0.07),
    ("I need this sorted today, whatever it takes.", 0.26),
    ("Are you a bot?", 0.40),
    ("Is there any way to speak to someone about my invoice?", 0.84),
    ("I have asked three times now. Can I please just talk to a real person?", 0.99),
]

print(f"{'message':<74} {'our noul':>8} {'docs':>6}")
with TypeSafeClient() as client:
    for message, docs_value in MESSAGES:
        response, seconds = timed(client.system_one, state=message, questions=QUESTION)
        value = response.answers["is_human_escalation"].noul
        print(f"{message:<74} {value:>8.2f} {docs_value:>6.2f}")
        log_call("02_noul.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds)
print(f"model: {response.model}")
