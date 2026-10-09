"""Decisions 2: the same first call with the OpenAI Python SDK.

client.decisions.create needs openai 3.26.0 or newer. The answer comes back
as an object, so we read fields by name instead of digging through JSON.

Author: Roni Das
Created: 2026-10-09
"""

from common import check_key_present, cost_usd, make_client, ask, show

check_key_present()
client = make_client()

decision, seconds = ask(
    client,
    input="I was charged twice for my order.",
    questions=[{
        "type": "choice",
        "name": "department",
        "instructions": "Which department should handle this complaint?",
        "choices": [
            {"value": "billing", "description": "Payments, invoices, and refunds."},
            {"value": "technical", "description": "Problems using the product."},
            {"value": "shipping", "description": "Delivery and tracking."},
            {"value": "other", "description": "Requests outside these categories."},
        ],
    }],
    script="02_first_call_sdk.py",
)

answer = decision.answers[0]
show("answer type", answer.type)
show("choice", answer.choice)
show("confidence", answer.confidence)
for p in answer.probabilities:
    show(f"  P({p.value})", p.probability)
show("model", decision.model)
show("input tokens", decision.usage.input_tokens)
show("output tokens", decision.usage.output_tokens)
show("cost (US$)", f"{cost_usd(decision.usage.input_tokens):.8f}")
show("time (s)", f"{seconds:.3f}")
