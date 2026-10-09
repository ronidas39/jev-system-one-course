"""Decisions 7: refusals and errors, and code that handles both.

Part 1, a refusal. One request with three questions about one support message.
Two are fair questions. The third asks about the customer's health, which a
support tool has no business guessing. The API may refuse that one question.
The other answers still come back. Our code sends a refusal to a person,
never to a default answer.

Then the same health question again, in its own request, but with a fair
way out: an "other" option. Watch whether it is still refused.

Part 2, errors. A broken request fails as a whole, with an HTTP error code.
We cause two on purpose and print what they look like.

Author: Roni Das
Created: 2026-10-09
"""

import textwrap

import openai

from common import ask, check_key_present, cost_usd, make_client, show

check_key_present()
client = make_client()

MESSAGE = ("I was in hospital all of last week, so I missed the return window for my "
           "order. Can I still send it back and get my money?")

QUESTIONS = [
    {"type": "choice", "name": "team", "instructions": "Which team should handle this?",
     "choices": [
         {"value": "returns", "description": "Exchanges, returns, wrong or damaged items"},
         {"value": "shipping", "description": "Delivery status, delays, lost packages"},
         {"value": "billing", "description": "Charges, invoices, payment problems"},
     ]},
    {"type": "predicate", "name": "refund_requested",
     "instructions": "Does the customer ask for their money back?"},
    {"type": "choice", "name": "illness",
     "instructions": "Which illness does the customer have?",
     "choices": [
         {"value": "heart", "description": "A heart condition"},
         {"value": "cancer", "description": "Cancer"},
         {"value": "infection", "description": "An infection"},
     ]},
]


def route(answer: object) -> str:
    """What our code does with one answer. A refusal always goes to a person."""
    if answer.type == "refusal":
        return "REFUSED -> send to a person"
    if answer.type == "predicate":
        return f"probability {answer.probability:.2f}"
    return f"{answer.choice} (confidence {answer.confidence:.2f})"


print("Part 1 · a refusal")
decision, seconds = ask(client, input=MESSAGE, questions=QUESTIONS,
                        script="07_refusals_and_errors.py", note="refusal demo")
for answer in decision.answers:
    show(answer.name, route(answer))
show("input tokens", decision.usage.input_tokens)
show("cost (US$)", f"{cost_usd(decision.usage.input_tokens):.8f}")

print()
print("The same health question, now with an 'other' option")
with_other = dict(QUESTIONS[2])
with_other["choices"] = [*QUESTIONS[2]["choices"],
                         {"value": "other", "description": "Something else, or not stated"}]
again, _ = ask(client, input=MESSAGE, questions=[with_other],
               script="07_refusals_and_errors.py", note="refusal demo, with other")
show("illness", route(again.answers[0]))

print()
print("Part 2 · errors")
bad_requests = {
    "a choice with only one option": [{
        "type": "choice", "name": "team", "instructions": "Which team?",
        "choices": [{"value": "returns"}]}],
    "an unknown question type": [{
        "type": "yes_no", "name": "x", "instructions": "Is this a refund?"}],
}
for label, questions in bad_requests.items():
    try:
        client.decisions.create(model="gpt-6-luna", input=MESSAGE, questions=questions)
        show(label, "no error (unexpected)")
    except openai.APIStatusError as error:
        show(label, f"HTTP {error.status_code}: {type(error).__name__}")
        message = (error.body or {}).get("message", "") if isinstance(error.body, dict) else ""
        for line in textwrap.wrap(message, 70):
            print(f"{'':<29}{line}")
