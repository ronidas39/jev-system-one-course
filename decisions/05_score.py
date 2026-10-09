"""Decisions 5: rate on ordered levels (score).

Levels are numbered from 0. The score is the probability-weighted average of
the level numbers, so it can land between two levels. Same four bug reports
as handson/04_score.py.

Author: Roni Das
Created: 2026-10-09
"""

from common import ask, check_key_present, make_client

check_key_present()
client = make_client()

SEVERITY = {
    "type": "score",
    "name": "severity",
    "instructions": "How severe is the reported issue?",
    "levels": [
        {"label": "cosmetic", "description": "Cosmetic; no impact to functionality"},
        {"label": "workaround", "description": "Broken or degraded feature, but workaround exists"},
        {"label": "blocking", "description": "Blocking issue; no workaround exists"},
    ],
}

REPORTS = [
    "The export button is misaligned by a few pixels on the settings page.",
    "The PDF export button does nothing when clicked. I can still export to CSV "
    "and convert it myself, but that takes ages.",
    "The export button crashes the settings page in Safari. It works in Chrome, "
    "but a few of our customers only use Safari.",
    "Nobody on our team can log in since this morning. We get a 500 error on every attempt.",
]

print(f"{'report':<60} {'score':>6} {'conf':>5}  probabilities")
for report in REPORTS:
    decision, seconds = ask(client, input=report, questions=[SEVERITY], script="05_score.py")
    answer = decision.answers[0]
    short = report[:57] + "..." if len(report) > 60 else report
    levels = "  ".join(f"{p.label} {p.probability:.2f}" for p in answer.probabilities)
    print(f"{short:<60} {answer.score:>6.2f} {answer.confidence:>5.2f}  {levels}")
print(f"model: {decision.model}")
