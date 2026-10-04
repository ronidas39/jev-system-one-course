"""Exercise 1b: the same first call, from Python, with the official SDK.

Author: Roni Das
Created: 2026-10-04
"""

from typesafe_sdk import Noul, TypeSafeClient

from common import check_key_present, cost_usd, log_call, show, timed

check_key_present()

MESSAGE = (
    "Hi, I've been trying to connect my Stripe account for 3 days and the "
    "integration keeps failing. I'm losing sales. Please help ASAP."
)

with TypeSafeClient() as client:
    response, seconds = timed(
        client.system_one,
        state=MESSAGE,
        questions={"urgency": Noul(instructions="Does this message express urgency?")},
    )

show("model that answered", response.model)
show("urgency (noul)", response.answers["urgency"].noul)
show("input tokens", response.usage.input_tokens)
show("output tokens", response.usage.output_tokens)
show("cost (USD)", f"{cost_usd(response.usage.input_tokens):.8f}")
show("time on this machine (s)", f"{seconds:.3f}")
log_call("01_first_call.py", response.model, response.usage.input_tokens,
         response.usage.output_tokens, seconds)
