"""Tool routing, step 2 of 3: fourteen requests, and how often Jev matches me.

Adds the fourteen requests, each with the tool I would pick by hand, and a
loop that asks Jev about each one and counts the matches.

    python usecases/steps/routing_2_many_requests.py

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



def main() -> None:
    """Route every request and count how often Jev's pick matches mine."""
    right = 0
    with make_jev_client() as client:
        print(f"{'request':<56}{'my pick':<18}{'Jev pick':<18}{'conf':>5}")
        for text, mine in REQUESTS:
            answer = ask_jev(client, text, QUESTIONS).answer["tool"]
            right += answer["choice"] == mine
            print(f"{text[:54]:<56}{mine:<18}{answer['choice']:<18}"
                  f"{answer['confidence']:>5.2f}")
    print(f"\nJev's pick matched mine on {right} of {len(REQUESTS)} requests.")


if __name__ == "__main__":
    main()
