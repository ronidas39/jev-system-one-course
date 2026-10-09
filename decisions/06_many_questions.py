"""Decisions 6: many questions in one call, against one question per call.

Same ticket and the same eight questions as handson/05_many_questions.py.
We send them once together, then once each, and compare the time on this
machine and the input tokens (the cost). Then we check the answers match.

Author: Roni Das
Created: 2026-10-09
"""

from common import ask, check_key_present, cost_usd, make_client

check_key_present()
client = make_client()

TICKET = (
    "Hi, I placed an order (#98423) last Thursday and was charged twice. I also can't "
    "log in after the site update, and adding Apple Pay would be really helpful. "
    "This is getting frustrating."
)


def predicate(name: str, text: str) -> dict:
    return {"type": "predicate", "name": name, "instructions": text}


QUESTIONS = [
    {"type": "choice", "name": "category",
     "instructions": "What is the main topic of this ticket?",
     "choices": [
         {"value": "bug_report",
          "description": "The user is reporting something that is broken or producing errors"},
         {"value": "billing", "description": "Charges, invoices, refunds, subscriptions"},
         {"value": "feature_request", "description": "The user is requesting new functionality"},
         {"value": "account", "description": "Login, permissions, profile, security"},
     ]},
    {"type": "score", "name": "bug_severity",
     "instructions": "How severe is the reported issue?",
     "levels": [
         {"label": "cosmetic", "description": "Cosmetic; no impact to functionality"},
         {"label": "workaround", "description": "Broken or degraded feature; workaround exists"},
         {"label": "blocking", "description": "Blocking issue; no workaround exists"},
     ]},
    predicate("has_reproducible_steps",
              "Does the user describe specific steps to reproduce the issue?"),
    predicate("refund_requested", "Does the customer request a refund?"),
    predicate("mentions_duplicate_charge", "Does the customer say they were charged twice?"),
    predicate("cannot_log_in", "Does the customer say they cannot log in?"),
    predicate("asks_for_feature", "Does the customer ask for a new feature?"),
    {"type": "score", "name": "frustration",
     "instructions": "How frustrated does the customer appear?",
     "levels": [
         {"label": "calm", "description": "Calm, just stating facts"},
         {"label": "frustrated", "description": "Frustrated but civil"},
         {"label": "angry", "description": "Very angry, strong language"},
     ]},
]


def short(answer: object) -> str:
    """One short text for any answer type."""
    kind = answer.type
    if kind == "predicate":
        return f"{answer.probability:.2f}"
    if kind == "choice":
        return f"{answer.choice} (conf {answer.confidence:.2f})"
    if kind == "score":
        return f"{answer.score:.2f} (conf {answer.confidence:.2f})"
    return "REFUSED"


together, together_s = ask(client, input=TICKET, questions=QUESTIONS,
                           script="06_many_questions.py", note="8 questions, 1 call")
separate = {}
separate_s = 0.0
separate_tokens = 0
for question in QUESTIONS:
    one, seconds = ask(client, input=TICKET, questions=[question],
                       script="06_many_questions.py", note=f"1 question: {question['name']}")
    separate[question["name"]] = one.answers[0]
    separate_s += seconds
    separate_tokens += one.usage.input_tokens

print(f"{'question':<26} {'one call (8 together)':<26} {'8 separate calls':<26}")
for answer in together.answers:
    print(f"{answer.name:<26} {short(answer):<26} {short(separate[answer.name]):<26}")

tokens = together.usage.input_tokens
print()
print(f"one call:  {together_s:6.3f} s, {tokens:5d} input tokens, ${cost_usd(tokens):.8f}")
print(f"8 calls:   {separate_s:6.3f} s, {separate_tokens:5d} input tokens, "
      f"${cost_usd(separate_tokens):.8f}")
print(f"8 calls cost {separate_tokens / tokens:.1f}x the tokens and took "
      f"{separate_s / together_s:.1f}x the time (one after another, from this machine).")
print(f"model: {together.model}")
