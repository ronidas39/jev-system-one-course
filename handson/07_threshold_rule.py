"""Exercise 7: a confidence rule. Act, ask a human, or do not act.

The thresholds are ours, not TypeSafe's. TypeSafe's docs say: start
conservative, test on your own data, and adjust.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, TypeSafeClient

from common import check_key_present, log_call, timed

check_key_present()

ACT_AT = 0.85      # at or above this: act automatically
ASK_AT = 0.50      # between ASK_AT and ACT_AT: ask a person to confirm
                   # below ASK_AT: do not act; send to a human

INTENT = Choice(
    instructions="What action is the user requesting?",
    criteria={
        "check_balance": "Check the balance of an account",
        "approve_transfer": "Approve the pending transfer request",
        "other": "Something else",
    },
)

COMMANDS = [
    "What's my balance right now?",
    "Yes, go ahead and approve the transfer that is waiting.",
    "Hmm, the transfer... I think maybe, can you check it first?",
    "My card got stuck in the machine at the station.",
]


def decide(choice: str, confidence: float) -> str:
    """Turn one answer into one action, using our own thresholds."""
    if confidence < ASK_AT:
        return "DO NOT ACT -> send to a human"
    if choice == "approve_transfer" and confidence < ACT_AT:
        return "ASK -> 'Do you want to approve this transfer?'"
    if choice == "other":
        return "DO NOT ACT -> send to a human"
    return f"ACT -> run {choice}"


with TypeSafeClient() as client:
    for command in COMMANDS:
        response, seconds = timed(client.system_one, state=command, questions={"intent": INTENT})
        answer = response.answers["intent"]
        print(f"{command}\n   {answer.choice}, confidence {answer.confidence:.2f}, "
              f"{answer.probabilities}\n   => {decide(answer.choice, answer.confidence)}")
        log_call("07_threshold_rule.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds)
print(f"model: {response.model}")
