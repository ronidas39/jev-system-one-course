#!/bin/bash
# Decisions 1a: your first call to the Decisions API, with curl.
# This is the example from OpenAI's Decisions guide: route a customer complaint.
# The key comes from the OPENAI_API_KEY environment variable. It is never typed into this file.
# -w prints the HTTP status and the total time on the last line.
curl -s https://api.openai.com/v1/decisions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -w "\nHTTP %{http_code}, total time %{time_total} s\n" \
  -d @- <<'JSON'
{
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
      {"value": "other", "description": "Requests outside these categories."}
    ]
  }]
}
JSON
