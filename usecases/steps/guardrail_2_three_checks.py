"""Guardrail, step 2 of 4: three checks on one draft, and a block rule.

Adds our written policy to the state, two more Noul questions (does the draft
leak another customer's details, does it answer the question), and a small
check() function that blocks the draft when any rule looks broken.

    python usecases/steps/guardrail_2_three_checks.py

Author: Roni Das
Created: 2026-10-10
"""

from typesafe_sdk import Noul

from jevcourse.calls import ask_jev, make_jev_client

POLICY = ("Support replies may explain the refund policy, but must never promise or confirm a "
          "refund. Only a human manager approves refunds. Never share another customer's name, "
          "email, address or order details.")

QUESTIONS = {
    "promises_refund": Noul(instructions="Does `draft_reply` promise or confirm that the "
                            "customer will get money back?"),
    "leaks_other_data": Noul(instructions="Does `draft_reply` reveal the name, email, address "
                             "or order of a person other than the customer who wrote "
                             "`customer_message`?"),
    "answers_question": Noul(instructions="Does `draft_reply` answer what `customer_message` "
                             "asks?"),
}

BLOCK_AT = 0.5
"""Above this probability of a rule break, the draft is not sent."""

MESSAGE = "Where is my order #552019?"
DRAFT = ("Your order is on its way. By the way, Maria Lopez at 14 Hill Road ordered the same "
         "thing and hers arrived in two days.")


def check(client: object, message: str, draft: str) -> tuple[bool, dict[str, float], float]:
    """Run the three checks on one draft. Returns (blocked, probabilities, seconds)."""
    state = {"policy": POLICY, "customer_message": message, "draft_reply": draft}
    result = ask_jev(client, state, QUESTIONS)  # type: ignore[arg-type]
    p = {k: v["noul"] for k, v in result.answer.items()}
    blocked = (p["promises_refund"] > BLOCK_AT or p["leaks_other_data"] > BLOCK_AT
               or p["answers_question"] < BLOCK_AT)
    return blocked, p, result.seconds


def main() -> None:
    """Check the one draft and say whether it may be sent."""
    with make_jev_client() as jev:
        blocked, p, secs = check(jev, MESSAGE, DRAFT)
    print(f"customer: {MESSAGE}")
    print(f"draft:    {DRAFT}\n")
    print(f"Jev: refund {p['promises_refund']:.2f}, leak {p['leaks_other_data']:.2f}, "
          f"answers {p['answers_question']:.2f}, {secs:.3f} s")
    print("decision:", "BLOCK, send to a human" if blocked else "OK to send")


if __name__ == "__main__":
    main()
