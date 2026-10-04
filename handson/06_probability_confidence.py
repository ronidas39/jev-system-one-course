"""Exercise 6: read probabilities and confidence, and check the confidence maths.

TypeSafe's Confidence page gives the exact formulas. We recompute confidence
from the returned probabilities and compare with the confidence Jev sent.
Then we send the same request five times to see how stable the numbers are.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, Score, TypeSafeClient

from common import check_key_present, log_call, timed

check_key_present()


def choice_confidence(probabilities: list[float]) -> float:
    """Formula from docs.typesafe.ai/confidence for a Choice with n options."""
    n = len(probabilities)
    return (max(probabilities) - 1 / n) / (1 - 1 / n)


def score_confidence(probabilities: list[float]) -> float:
    """Formula from docs.typesafe.ai/confidence for a Score with n ordered levels."""
    n = len(probabilities)
    m = probabilities.index(max(probabilities))
    spread = sum(p * abs(i - m) for i, p in enumerate(probabilities))
    even_spread = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    return max(0.0, 1 - spread / even_spread)


TICKET = (
    "Shoes arrived two weeks late and in the wrong size. Also I see two charges of "
    "$120 on my card. What are you going to do about this?"
)
QUESTIONS = {
    "resolution": Choice(
        instructions="What does the customer want to happen?",
        criteria={
            "exchange": "Swap the item for a different one",
            "refund": "Money back",
            "replacement": "The same item sent again",
            "information": "Just an answer, no action needed",
        },
    ),
    "frustration": Score(
        instructions="How frustrated is the customer?",
        criteria=["Calm, just stating facts", "Frustrated but civil",
                  "Very angry, strong language or threatening to leave"],
    ),
}

with TypeSafeClient() as client:
    runs = []
    for run in range(5):
        response, seconds = timed(client.system_one, state=TICKET, questions=QUESTIONS)
        runs.append(response)
        log_call("06_probability_confidence.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds, note=f"run {run + 1}")

first = runs[0]
res = first.answers["resolution"]
fru = first.answers["frustration"]
print("Run 1, Choice 'resolution'")
print(f"  choice {res.choice}, probabilities {res.probabilities}")
print(f"  confidence from Jev {res.confidence:.3f}, our formula "
      f"{choice_confidence(list(res.probabilities.values())):.3f}")
print("Run 1, Score 'frustration'")
levels = [fru.probabilities[level] for level in sorted(fru.probabilities)]
print(f"  score {fru.score:.2f}, probabilities {fru.probabilities}")
print(f"  score from probabilities: {sum(i * p for i, p in enumerate(levels)):.2f}")
print(f"  confidence from Jev {fru.confidence:.3f}, our formula {score_confidence(levels):.3f}")

print("\nSame request, five runs:")
for i, response in enumerate(runs, start=1):
    r = response.answers["resolution"]
    f = response.answers["frustration"]
    print(f"  run {i}: resolution {r.choice} p={r.probabilities[r.choice]:.2f} "
          f"conf={r.confidence:.2f} | frustration score={f.score:.2f} conf={f.confidence:.2f}")
print(f"model: {first.model}")
