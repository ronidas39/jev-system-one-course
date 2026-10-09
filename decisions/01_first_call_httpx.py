"""Decisions 1b: the same first call from Python, as plain HTTP with httpx.

No OpenAI SDK here. We build the JSON body ourselves, send it, and print the
raw JSON that comes back. This is exactly what the SDK does for you in 02.

Author: Roni Das
Created: 2026-10-09
"""

import json
import os
import time

import httpx

from common import check_key_present, cost_usd, show

check_key_present()

body = {
    "model": "gpt-6-luna",
    "input": "I was charged twice for my order.",
    "questions": [{
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
}
headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}

start = time.perf_counter()
response = httpx.post("https://api.openai.com/v1/decisions", json=body, headers=headers,
                      timeout=60.0)
seconds = time.perf_counter() - start
response.raise_for_status()
data = response.json()

print(json.dumps(data, indent=2))
print()
show("HTTP status", response.status_code)
show("time (s)", f"{seconds:.3f}")
show("input tokens", data["usage"]["input_tokens"])
show("cost (US$)", f"{cost_usd(data['usage']['input_tokens']):.8f}")
