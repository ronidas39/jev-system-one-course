#!/bin/bash
# Exercise 1a: your first call to Jev with curl.
# The key comes from the TYPESAFE_API_KEY environment variable. It is never typed into this file.
# -w prints the HTTP status and the total time on the last line.
curl -s -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -w "\nHTTP %{http_code}, total time %{time_total} s\n" \
  -d @- <<'JSON'
{
  "state": "Hi, I've been trying to connect my Stripe account for 3 days and the integration keeps failing. I'm losing sales. Please help ASAP.",
  "model": "jev-latest",
  "questions": {
    "urgency": {
      "type": "noul",
      "instructions": "Does this message express urgency?"
    }
  }
}
JSON
