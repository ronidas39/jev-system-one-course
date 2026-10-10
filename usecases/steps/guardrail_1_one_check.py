"""Guardrail, step 1 of 4: does this draft reply promise a refund?

One Noul question about one draft reply that a support agent might send.
Jev answers with the probability that the draft promises money back.

    python usecases/steps/guardrail_1_one_check.py

Author: Roni Das
Created: 2026-10-10
"""

from typesafe_sdk import Noul

from jevcourse.calls import ask_jev, make_jev_client

QUESTIONS = {
    "promises_refund": Noul(instructions="Does `draft_reply` promise or confirm that the "
                            "customer will get money back?"),
}

MESSAGE = "I was charged twice. Can I get one payment back?"
DRAFT = "No problem, I have refunded the second payment. It will be back on your card in 3 days."


def main() -> None:
    """Ask the one question about the one draft."""
    state = {"customer_message": MESSAGE, "draft_reply": DRAFT}
    with make_jev_client() as client:
        result = ask_jev(client, state, QUESTIONS)
    p = result.answer["promises_refund"]["noul"]

    print(f"customer: {MESSAGE}")
    print(f"draft:    {DRAFT}\n")
    print(f"promises_refund  probability of yes {p:.2f}")
    print(f"\n{result.model}: {result.seconds:.3f} s, {result.input_tokens} input tokens, "
          f"${result.usd:.7f}")


if __name__ == "__main__":
    main()
