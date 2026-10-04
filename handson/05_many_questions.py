"""Exercise 5: many questions in one call, against one question per call.

Same ticket, same eight questions. We send them once together, then once
each. We compare total time on this machine and total input tokens (cost).
Then we check the answers did not change.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

from common import check_key_present, cost_usd, log_call, timed

check_key_present()

TICKET = (
    "Hi, I placed an order (#98423) last Thursday and was charged twice. I also can't "
    "log in after the site update, and adding Apple Pay would be really helpful. "
    "This is getting frustrating."
)

QUESTIONS = {
    "category": Choice(
        instructions="What is the main topic of this ticket?",
        criteria={
            "bug_report": "The user is reporting something that is broken or producing errors",
            "billing": "Charges, invoices, refunds, subscriptions",
            "feature_request": "The user is requesting new functionality",
            "account": "Login, permissions, profile, security",
        },
    ),
    "bug_severity": Score(
        instructions="How severe is the reported issue?",
        criteria=[
            "Cosmetic; no impact to functionality",
            "Broken or degraded feature; workaround exists",
            "Blocking issue; no workaround exists",
        ],
    ),
    "has_reproducible_steps": Noul(
        instructions="Does the user describe specific steps to reproduce the issue?"),
    "refund_requested": Noul(instructions="Does the customer request a refund?"),
    "mentions_duplicate_charge": Noul(instructions="Does the customer say they were charged twice?"),
    "cannot_log_in": Noul(instructions="Does the customer say they cannot log in?"),
    "asks_for_feature": Noul(instructions="Does the customer ask for a new feature?"),
    "frustration": Score(
        instructions="How frustrated does the customer appear?",
        criteria=["Calm, just stating facts", "Frustrated but civil",
                  "Very angry, strong language"],
    ),
}


def short(answer: object) -> str:
    """One short text for any answer type."""
    kind = getattr(answer, "type", "")
    if kind == "noul":
        return f"{answer.noul:.2f}"
    if kind == "choice":
        return f"{answer.choice} (conf {answer.confidence:.2f})"
    return f"{answer.score:.2f} (conf {answer.confidence:.2f})"


with TypeSafeClient() as client:
    together, together_s = timed(client.system_one, state=TICKET, questions=QUESTIONS)
    log_call("05_many_questions.py", together.model, together.usage.input_tokens,
             together.usage.output_tokens, together_s, note="8 questions, 1 call")

    separate = {}
    separate_s = 0.0
    separate_tokens = 0
    for name, question in QUESTIONS.items():
        one, seconds = timed(client.system_one, state=TICKET, questions={name: question})
        separate[name] = one.answers[name]
        separate_s += seconds
        separate_tokens += one.usage.input_tokens or 0
        log_call("05_many_questions.py", one.model, one.usage.input_tokens,
                 one.usage.output_tokens, seconds, note=f"1 question: {name}")

print(f"{'question':<26} {'one call (8 together)':<26} {'8 separate calls':<26}")
for name in QUESTIONS:
    print(f"{name:<26} {short(together.answers[name]):<26} {short(separate[name]):<26}")

print()
print(f"one call:  {together_s:6.3f} s, {together.usage.input_tokens:5d} input tokens, "
      f"${cost_usd(together.usage.input_tokens):.8f}")
print(f"8 calls:   {separate_s:6.3f} s, {separate_tokens:5d} input tokens, "
      f"${cost_usd(separate_tokens):.8f}")
print(f"8 calls cost {separate_tokens / together.usage.input_tokens:.1f}x the tokens and took "
      f"{separate_s / together_s:.1f}x the time (one after another, from this machine).")
print(f"model: {together.model}")
