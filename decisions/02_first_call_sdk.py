"""Decisions 2: our first call to OpenAI's Decisions API, with the Python SDK.

We send one complaint and one choice question: which department should
handle it? The answer comes back as a Python object, so we read it by name.

Run it from the decisions folder:
    python 02_first_call_sdk.py

Author: Roni Das
"""

import os
import time

from openai import OpenAI

# Read the API key from the .env file in the course folder.
for line in open("../.env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

client = OpenAI()

# ---------------------------------------------------------------------------
# Step 1: ask one choice question about one complaint
# ---------------------------------------------------------------------------
start = time.time()
decision = client.decisions.create(
    model="gpt-6-luna",
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
)
seconds = time.time() - start

# ---------------------------------------------------------------------------
# Step 2: read the answer
# ---------------------------------------------------------------------------
answer = decision.answers[0]
print("answer type  ", answer.type)
print("choice       ", answer.choice)
print("confidence   ", answer.confidence)
for p in answer.probabilities:
    print(f"  P({p.value})", p.probability)

# ---------------------------------------------------------------------------
# Step 3: the cost. Only input tokens are paid for, at $0.10 per million.
# ---------------------------------------------------------------------------
tokens = decision.usage.input_tokens
print("model        ", decision.model)
print("input tokens ", tokens)
print("output tokens", decision.usage.output_tokens)
print(f"cost (US$)    {tokens * 0.10 / 1_000_000:.8f}")
print(f"time (s)      {seconds:.3f}")
