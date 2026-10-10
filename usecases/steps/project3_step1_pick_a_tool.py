"""Tool routing, step 1 of 3: which tool does one request need?

An agent has five tools. One Choice question asks Jev which tool fits one
customer request, and Jev gives a probability for every tool.

    python usecases/steps/project3_step1_pick_a_tool.py

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

REQUEST = "You charged me twice, send one payment back please"


def main() -> None:
    """Ask for the tool and print Jev's pick with every probability."""
    with make_jev_client() as client:
        result = ask_jev(client, REQUEST, QUESTIONS)
    answer = result.answer["tool"]
    print(f"request: {REQUEST}\n")
    print(f"Jev pick   {answer['choice']}   confidence {answer['confidence']:.2f}")
    for tool, p in answer["probabilities"].items():
        print(f"  {tool:<18}{p:.2f}")
    print(f"\n{result.model}: {result.seconds:.3f} s, {result.input_tokens} input tokens, "
          f"${result.usd:.7f}")


if __name__ == "__main__":
    main()
