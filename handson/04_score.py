"""Exercise 4: place something on a scale you describe (Score).

Asks the same bug-severity Score about five bug reports. The levels are
descriptions of situations, not numbers.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Score, TypeSafeClient

from common import check_key_present, log_call, timed

check_key_present()

SEVERITY = Score(
    instructions="How severe is the reported issue?",
    criteria=[
        "Cosmetic; no impact to functionality",
        "Broken or degraded feature, but workaround exists",
        "Blocking issue; no workaround exists",
    ],
)

REPORTS = [
    "The export button is misaligned by a few pixels on the settings page.",
    "The PDF export button does nothing when clicked. I can still export to CSV "
    "and convert it myself, but that takes ages.",
    "The export button crashes the settings page in Safari. It works in Chrome, "
    "but a few of our customers only use Safari.",
    "Nobody on our team can log in since this morning. We get a 500 error on every attempt.",
]

print(f"{'report':<60} {'score':>6} {'conf':>5}  probabilities (level: p)")
with TypeSafeClient() as client:
    for report in REPORTS:
        response, seconds = timed(client.system_one, state=report,
                                  questions={"severity": SEVERITY})
        answer = response.answers["severity"]
        short = report[:57] + "..." if len(report) > 60 else report
        print(f"{short:<60} {answer.score:>6.2f} {answer.confidence:>5.2f}  {answer.probabilities}")
        log_call("04_score.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds)

    # Try this: levels that are only numbers. The docs say this works badly.
    numbers_only = Score(instructions="Rate severity from 0 to 2, where 2 is worst",
                         criteria=["0", "1", "2"])
    response, seconds = timed(client.system_one, state=REPORTS[0],
                              questions={"severity": numbers_only})
    answer = response.answers["severity"]
    print(f"\nSame first report, levels are only numbers: score {answer.score:.2f}, "
          f"confidence {answer.confidence:.2f}, {answer.probabilities}")
    log_call("04_score.py", response.model, response.usage.input_tokens,
             response.usage.output_tokens, seconds, note="numbers-only levels")
print(f"model: {response.model}")
