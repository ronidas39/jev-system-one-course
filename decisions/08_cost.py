"""Decisions 8: what a call costs, read from the usage the API sends back.

We send 20 real tickets from data/tickets.jsonl, one call each, with the same
three questions the course uses everywhere (team, urgency, frustration).
Every response carries usage.input_tokens. Cost = input tokens x the price.
There is no output charge on this endpoint.

Author: Roni Das
Created: 2026-10-09
"""

import json
import statistics

from jevcourse.tasks import FRUSTRATION_LEVELS, TEAMS, URGENCY_LEVELS

from common import (PRICE_READ_ON, REPO_ROOT, USD_PER_MILLION_INPUT_TOKENS, ask,
                    check_key_present, cost_usd, make_client)

check_key_present()
client = make_client()

QUESTIONS = [
    {"type": "choice", "name": "team",
     "instructions": "Which team should handle this support ticket?",
     "choices": [{"value": k, "description": v} for k, v in TEAMS.items()]},
    {"type": "score", "name": "urgency",
     "instructions": "How soon does this ticket need a response?",
     "levels": [{"label": text} for text in URGENCY_LEVELS]},
    {"type": "score", "name": "frustration",
     "instructions": "How frustrated does the customer appear?",
     "levels": [{"label": text} for text in FRUSTRATION_LEVELS]},
]

tickets = [json.loads(line) for line in (REPO_ROOT / "data/tickets.jsonl").read_text().splitlines()]
tokens = []
print(f"{'ticket':<7} {'characters':>10} {'input tokens':>12} {'cost (US$)':>12}")
for ticket in tickets[:20]:
    decision, _ = ask(client, input=ticket["text"], questions=QUESTIONS, script="08_cost.py")
    used = decision.usage.input_tokens
    tokens.append(used)
    print(f"{ticket['id']:<7} {len(ticket['text']):>10} {used:>12} {cost_usd(used):>12.8f}")

total = sum(tokens)
print()
print(f"price: ${USD_PER_MILLION_INPUT_TOKENS} per million input tokens (read {PRICE_READ_ON})")
print(f"20 tickets: {total} input tokens, ${cost_usd(total):.6f}")
print(f"median tokens per ticket: {statistics.median(tokens):.0f}")
print(f"so 1,000 tickets cost about ${cost_usd(total) / 20 * 1000:.4f}, "
      f"and one million about ${cost_usd(total) / 20 * 1_000_000:.2f}")
