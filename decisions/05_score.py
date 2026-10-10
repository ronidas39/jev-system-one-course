"""Decisions 5: rate something on ordered levels (a score).

The levels are numbered from 0. The score is the average of the level
numbers, weighted by their probabilities, so it can land between two levels.
Same four bug reports as we gave Jev.

Run it from the decisions folder:
    python 05_score.py

Author: Roni Das
"""

import os

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: the question, with three levels in order, and four bug reports
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Step 2: score each report, and print the score and every level's probability
# ---------------------------------------------------------------------------
print(f"{'report':<45} {'score':>6} {'conf':>5}  probabilities")
for report in REPORTS:
    decision = client.decisions.create(model="gpt-6-luna", input=report, questions=[SEVERITY])
    answer = decision.answers[0]
    levels = "  ".join(f"{p.label} {p.probability:.2f}" for p in answer.probabilities)
    print(f"{report[:42] + '...':<45} {answer.score:>6.2f} {answer.confidence:>5.2f}  {levels}")
