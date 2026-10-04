"""Exercise 13: the cheat-sheet example from the end of the book, as a runnable file.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

text = "I was charged twice and I can't log in. Fix this today!"
with TypeSafeClient(model="jev-1.13.0") as client:   # key from TYPESAFE_API_KEY
    r = client.system_one(
        state={"message": text},
        questions={
            "team": Choice(instructions="Which team should handle `message`?",
                           criteria={"billing": "Charges, refunds", "technical": "Bugs, errors",
                                     "other": "None of the above"}),
            "urgent": Noul(instructions="Does `message` say something is blocked right now?"),
            "frustration": Score(instructions="How frustrated is the customer?",
                                 criteria=["Calm", "Frustrated but civil", "Very angry"]),
        },
    )
team, urgent, frus = r.answers["team"], r.answers["urgent"], r.answers["frustration"]
print(r.model)                                   # the version that answered: log it
print(team.choice, team.probabilities, team.confidence)
print(urgent.noul)                               # P(yes); a Noul has no confidence field
print(frus.score, frus.probabilities, frus.legend, frus.confidence)
print(r.usage.input_tokens * 0.042 / 1e6)        # cost in US dollars
