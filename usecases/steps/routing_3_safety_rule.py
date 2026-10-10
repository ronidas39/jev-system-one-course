"""Tool routing, step 3 of 3: act only when Jev is sure enough.

Adds the safety rule: safe tools run at confidence 0.60 or more, the money
tool only at 0.85 or more, and anything below asks the user to clarify.
This step behaves like usecases/03_tool_routing.py.

    python usecases/steps/routing_3_safety_rule.py

Author: Roni Das
Created: 2026-10-10
"""

from typesafe_sdk import Choice

from jevcourse.calls import ask_jev, make_jev_client

TOOLS = {
    "get_order_status": "Look up where an order or parcel is right now",
    "issue_refund": "Send money back to the customer for a charge or an order",
    "reset_password": "Send a password reset link, or unlock a locked account",
    "search_help_docs": "Answer a how-to question from the help centre articles",
    "talk_to_human": "Hand over to a person: complaints, legal threats, anything else",
}
MONEY_TOOLS = {"issue_refund"}
SAFE_AT, MONEY_AT = 0.60, 0.85

QUESTIONS = {"tool": Choice(instructions="Which tool should the support agent use for this "
                            "request?", criteria=TOOLS)}

REQUESTS = [
    ("Where is my parcel? Order 88213.", "get_order_status"),
    ("It says delivered but nothing came, order 77120", "get_order_status"),
    ("You charged me twice, send one payment back please", "issue_refund"),
    ("I returned the jacket two weeks ago, where is my money?", "issue_refund"),
    ("I forgot my password", "reset_password"),
    ("my account is locked after 5 tries", "reset_password"),
    ("How do I export my data to CSV?", "search_help_docs"),
    ("Can I change the language of the app?", "search_help_docs"),
    ("I will take you to court over this", "talk_to_human"),
    ("This is the worst company I have ever dealt with", "talk_to_human"),
    ("Can you check my order and also refund the delivery fee?", "issue_refund"),
    ("money", "talk_to_human"),
    ("The app keeps logging me out, how do I stay signed in?", "search_help_docs"),
    ("I never got the reset email for my login", "reset_password"),
]


def decide(tool: str, confidence: float) -> str:
    """The whole safety rule, in plain code."""
    needed = MONEY_AT if tool in MONEY_TOOLS else SAFE_AT
    return f"run {tool}" if confidence >= needed else "ask the user to clarify"


def main() -> None:
    """Route every request and count how often Jev's pick matches mine."""
    right = acted = acted_right = 0
    with make_jev_client() as client:
        print(f"{'request':<56}{'my pick':<18}{'Jev pick':<18}{'conf':>5}  action")
        for text, mine in REQUESTS:
            answer = ask_jev(client, text, QUESTIONS).answer["tool"]
            action = decide(answer["choice"], answer["confidence"])
            right += answer["choice"] == mine
            if action.startswith("run"):
                acted += 1
                acted_right += answer["choice"] == mine
            print(f"{text[:54]:<56}{mine:<18}{answer['choice']:<18}"
                  f"{answer['confidence']:>5.2f}  {action}")
    print(f"\nJev's pick matched mine on {right} of {len(REQUESTS)} requests.")
    print(f"The agent acted on {acted}; {acted_right} of those were the tool I would pick.")
    print(f"It asked the user to clarify on {len(REQUESTS) - acted}.")


if __name__ == "__main__":
    main()
