"""Decisions 10: grade 33 egg photos, then choose two cut-offs and check them.

We ask one question about every photo in eggs/: is the shell clean, dirty,
cracked, or is the photo unclear? Each egg gets one number, P(not clean).
Two cut-offs turn that number into pass, reject, or "a person checks it".

We choose the cut-offs on half of the photos, then check them on the other
half, the photos we did NOT use to choose them.

The labels in eggs/labels.csv are the course author's own, made by eye.
They are drafts, not an expert's grades. See eggs/CREDITS.md.

Run it from the decisions folder:
    python 10_egg_grading.py

Author: Roni Das
"""

import base64
import csv
import os

from openai import OpenAI

# Read the API key from the .env file in the course folder (one folder up).
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

QUESTION = {
    "type": "choice",
    "name": "condition",
    "instructions": "What is the condition of the egg shell in this photo?",
    "choices": [
        {"value": "clean", "description": "Shell is intact with no dirt, stains or droppings."},
        {"value": "dirty", "description": "Shell is intact but has dirt, stains or droppings."},
        {"value": "cracked", "description": "Shell has a crack, hole, or is broken open."},
        {"value": "unclear", "description": "The photo does not show the shell well enough."},
    ],
}

# ---------------------------------------------------------------------------
# Step 1: load the 33 photo names and my labels
# ---------------------------------------------------------------------------
labels = {row["egg"]: row["condition"] for row in csv.DictReader(open("eggs/labels.csv"))}
print(f"Step 1: {len(labels)} photos with my labels")

# ---------------------------------------------------------------------------
# Step 2: one call per photo, keep P(not clean)
# ---------------------------------------------------------------------------
not_clean = {}
tokens = 0
print("\nStep 2: one call per photo")
print(f"   {'photo':<10} {'my label':<9} {'P(not clean)':>12}")
for egg, label in labels.items():
    photo_bytes = open(f"eggs/{egg}.jpg", "rb").read()
    url = "data:image/jpeg;base64," + base64.b64encode(photo_bytes).decode()
    decision = client.decisions.create(
        model="gpt-6-luna",
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url},
        ]}],
        questions=[QUESTION],
    )
    answer = decision.answers[0]
    p_clean = next(p.probability for p in answer.probabilities if p.value == "clean")
    not_clean[egg] = 1 - p_clean
    tokens += decision.usage.input_tokens
    print(f"   {egg:<10} {label:<9} {not_clean[egg]:>12.2f}")
print(f"   {len(labels)} calls, {tokens} input tokens, cost ${tokens * 0.10 / 1_000_000:.6f}")

# ---------------------------------------------------------------------------
# Step 3: try four pairs of cut-offs on half of the photos.
#         Below LOW we pass the egg, above HIGH we reject it,
#         and in between a person checks it.
# ---------------------------------------------------------------------------
CUT_OFFS = [(0.50, 0.50), (0.40, 0.60), (0.30, 0.70), (0.20, 0.80)]


def try_cut_offs(eggs):
    print(f"   {'pass below':>10} {'reject above':>12} {'passed bad':>10} {'rejected good':>13}"
          f" {'to a person':>11}")
    for low, high in CUT_OFFS:
        passed_bad = sum(1 for e in eggs if not_clean[e] < low and labels[e] != "clean")
        rejected_good = sum(1 for e in eggs if not_clean[e] > high and labels[e] == "clean")
        person = sum(1 for e in eggs if low <= not_clean[e] <= high)
        print(f"   {low:>10.2f} {high:>12.2f} {passed_bad:>10} {rejected_good:>13} {person:>11}")


eggs = list(labels)
choose_on = eggs[0::2]   # every other photo: used to choose the cut-offs
check_on = eggs[1::2]    # the rest: never used to choose, only to check

print(f"\nStep 3: choose cut-offs on {len(choose_on)} photos")
try_cut_offs(choose_on)

# ---------------------------------------------------------------------------
# Step 4: check the same cut-offs on the photos we did NOT use to choose them
# ---------------------------------------------------------------------------
print(f"\nStep 4: check them on the other {len(check_on)} photos")
try_cut_offs(check_on)

low, high = 0.30, 0.70
print(f"\n   with {low:.2f} / {high:.2f}, a person checks:")
for e in eggs:
    if low <= not_clean[e] <= high:
        print(f"   {e:<10} P(not clean) {not_clean[e]:.2f}  (my label: {labels[e]})")
