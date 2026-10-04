"""Exercise 12: a fair comparison of Jev with normal chat models.

Same 30 hand-made tickets, same three questions, same labels, same machine,
same time window. For each ticket we call Jev, then each chat model, one
after another, so the network is the same for everyone.
The chat models must answer in a fixed JSON shape (structured output), so
nobody is punished for messy text. We measure: accuracy against the labels,
wall-clock time per call, and cost from each response's own token counts.

Needs OPENAI_API_KEY as well as TYPESAFE_API_KEY. Uses only the Python
standard library for the OpenAI call, so nothing extra to install.

Author: Roni Das
Created: 2026-10-04
"""

import json
import os
import statistics
import time
import urllib.request
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from common import check_key_present, cost_usd, log_call, timed
from jevcourse.prices import openai_cost_usd
from inbox_questions import QUESTIONS  # the same questions as the Smart Support Inbox

check_key_present()
if not os.environ.get("OPENAI_API_KEY", "").strip():
    raise SystemExit("OPENAI_API_KEY is not set.")

# Prices come from jevcourse/prices.py (OpenAI pricing page, Standard tier, read 2026-10-04).
# Each model runs at the fastest reasoning setting it accepts.
CHAT_MODELS = {"gpt-6-luna": "none", "gpt-6.1-sol": "low"}

TEAMS = list(QUESTIONS["team"].criteria)
SYSTEM_PROMPT = (
    "You classify customer support tickets. Answer with JSON only.\n"
    f"team: which team should handle this support ticket? Options: "
    + "; ".join(f"{k} = {v}" for k, v in QUESTIONS["team"].criteria.items())
    + "\nurgency: how soon does this ticket need a response? "
    + "; ".join(f"{i} = {v}" for i, v in enumerate(QUESTIONS["urgency"].criteria))
    + "\nfrustration: how frustrated does the customer appear? "
    + "; ".join(f"{i} = {v}" for i, v in enumerate(QUESTIONS["frustration"].criteria))
)
SCHEMA = {
    "name": "ticket_labels",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["team", "urgency", "frustration"],
        "properties": {
            "team": {"type": "string", "enum": TEAMS},
            "urgency": {"type": "integer", "enum": [0, 1, 2]},
            "frustration": {"type": "integer", "enum": [0, 1, 2]},
        },
    },
}


def ask_chat_model(model: str, ticket: str) -> tuple[dict, dict, float]:
    """One chat-completions call with a strict JSON schema. Returns (labels, usage, seconds)."""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": ticket}],
        "response_format": {"type": "json_schema", "json_schema": SCHEMA},
        "reasoning_effort": CHAT_MODELS[model],
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body, method="POST",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                 "Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=120) as reply:
        data = json.loads(reply.read())
    seconds = time.perf_counter() - start
    labels = json.loads(data["choices"][0]["message"]["content"])
    return labels, data["usage"], seconds


tickets = json.loads(Path("tickets.json").read_text())["tickets"]
results: dict[str, list[dict]] = {"jev-1.13.0": [], **{m: [] for m in CHAT_MODELS}}

with TypeSafeClient(model="jev-1.13.0") as client:
    for ticket in tickets:
        response, seconds = timed(client.system_one, state=ticket["text"], questions=QUESTIONS)
        a = response.answers
        results["jev-1.13.0"].append({
            "team": a["team"].choice, "urgency": round(a["urgency"].score),
            "frustration": round(a["frustration"].score), "seconds": seconds,
            "usd": cost_usd(response.usage.input_tokens),
            "in": response.usage.input_tokens, "out": response.usage.output_tokens})
        log_call("12_compare_chat_model.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds, note=f"ticket {ticket['id']}")
        for model in CHAT_MODELS:
            labels, usage, seconds = ask_chat_model(model, ticket["text"])
            usd = openai_cost_usd(model, usage)
            results[model].append({**labels, "seconds": seconds, "usd": usd,
                                   "in": usage["prompt_tokens"],
                                   "out": usage["completion_tokens"]})
            log_call("12_compare_chat_model.py", model, usage["prompt_tokens"],
                     usage["completion_tokens"], seconds, provider="openai", usd=usd,
                     note=f"ticket {ticket['id']}")

Path("outputs/12_compare_results.json").write_text(json.dumps(results, indent=1))

n = len(tickets)
print(f"{n} hand-made tickets, each model asked the same 3 questions, run one after another.\n")
print(f"{'model':<14} {'team':>6} {'urgency':>8} {'frustr.':>8} {'median s':>9} "
      f"{'slowest s':>10} {'USD total':>10} {'tokens in/out per call':>24}")
for model, rows in results.items():
    team = sum(r["team"] == t["team"] for r, t in zip(rows, tickets, strict=True))
    urg = sum(r["urgency"] == t["urgency"] for r, t in zip(rows, tickets, strict=True))
    fru = sum(r["frustration"] == t["frustration"] for r, t in zip(rows, tickets, strict=True))
    times = [r["seconds"] for r in rows]
    usd = sum(r["usd"] for r in rows)
    tin = statistics.mean(r["in"] for r in rows)
    tout = statistics.mean(r["out"] for r in rows)
    print(f"{model:<14} {team:>3}/{n} {urg:>5}/{n} {fru:>5}/{n} {statistics.median(times):>9.3f} "
          f"{max(times):>10.3f} {usd:>10.6f} {tin:>12.0f} / {tout:<10.0f}")

print("\nWhere the models disagree on team:")
for i, t in enumerate(tickets):
    picks = {m: results[m][i]["team"] for m in results}
    if len(set(picks.values())) > 1 or picks["jev-1.13.0"] != t["team"]:
        print(f"  ticket {t['id']:>2} (label {t['team']}): {picks}")
