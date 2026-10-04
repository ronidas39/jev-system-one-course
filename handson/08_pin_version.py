"""Exercise 8: aliases and pinned versions.

jev-latest is an alias. It moves when TypeSafe ships a new release.
jev-1.13.0 is a pinned version ID. The response always tells you which
versioned model answered, so log it.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Noul, TypeSafeAPIError, TypeSafeClient

from common import check_key_present, log_call, timed

check_key_present()

QUESTION = {"refund": Noul(instructions="Does the customer request a refund?")}
STATE = "My flight was cancelled. Can I get my money back?"

# The first three names come from docs.typesafe.ai/models.
# "jev" is used in the SDK usage guide. "jev-1.13" appears in a code sample on the
# jaggedness page. "jev-0.1.0" does not exist; we send it on purpose to see the error.
NAMES = ["jev-latest", "jev-preview", "jev-1.13.0", "jev", "jev-1.13", "jev-0.1.0"]

with TypeSafeClient() as client:
    for name in NAMES:
        try:
            response, seconds = timed(client.system_one, state=STATE, questions=QUESTION,
                                      model=name)
            print(f"asked for {name:<12} -> answered by {response.model}, "
                  f"refund noul {response.answers['refund'].noul:.2f}")
            log_call("08_pin_version.py", response.model, response.usage.input_tokens,
                     response.usage.output_tokens, seconds, note=f"asked {name}")
        except TypeSafeAPIError as error:
            print(f"asked for {name:<12} -> error {error.status}: {error}")

# The pinned way to build a client for production:
pinned = TypeSafeClient(model="jev-1.13.0")
pinned.close()
print("A client can be pinned once: TypeSafeClient(model='jev-1.13.0')")
