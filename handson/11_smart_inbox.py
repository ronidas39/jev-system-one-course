"""Exercise 11: a small project, the Smart Support Inbox.

For each ticket we ask three questions in ONE call:
  team (Choice), urgency (Score), frustration (Score).
Then our code routes the ticket:
  team confidence >= ROUTE_AT  -> send to that team automatically
  otherwise                    -> put it in the human triage pile
  urgency rounds to "today"    -> mark as urgent
We compare every answer with the hand-made labels in tickets.json and
report accuracy, time per call, and cost from the usage numbers.

Author: Roni Das
Created: 2026-10-04
"""

import json
import statistics
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from common import check_key_present, cost_usd, log_call, timed
from inbox_questions import QUESTIONS

check_key_present()

ROUTE_AT = 0.60  # our own threshold for automatic routing; tune it on your data

data = json.loads(Path("tickets.json").read_text())
rows = []
with TypeSafeClient(model="jev-1.13.0") as client:  # pinned, so results stay comparable
    for ticket in data["tickets"]:
        response, seconds = timed(client.system_one, state=ticket["text"], questions=QUESTIONS)
        a = response.answers
        rows.append({
            "id": ticket["id"],
            "gold_team": ticket["team"], "team": a["team"].choice,
            "team_conf": a["team"].confidence, "team_probs": a["team"].probabilities,
            "gold_urgency": ticket["urgency"], "urgency": a["urgency"].score,
            "urgency_conf": a["urgency"].confidence,
            "gold_frustration": ticket["frustration"], "frustration": a["frustration"].score,
            "seconds": seconds, "input_tokens": response.usage.input_tokens,
            "model": response.model,
        })
        log_call("11_smart_inbox.py", response.model, response.usage.input_tokens,
                 response.usage.output_tokens, seconds, note=f"ticket {ticket['id']}")

Path("outputs/11_smart_inbox_results.json").write_text(json.dumps(rows, indent=1))

print(f"{'id':>2} {'gold team':<10} {'Jev team':<10} {'conf':>5} {'route':<8} "
      f"{'urg gold/Jev':>12} {'frus gold/Jev':>13}")
for r in rows:
    route = "AUTO" if r["team_conf"] >= ROUTE_AT else "HUMAN"
    mark = "" if r["team"] == r["gold_team"] else "  <- differs"
    print(f"{r['id']:>2} {r['gold_team']:<10} {r['team']:<10} {r['team_conf']:>5.2f} {route:<8} "
          f"{r['gold_urgency']:>5} / {r['urgency']:<5.2f} {r['gold_frustration']:>5} / "
          f"{r['frustration']:<5.2f}{mark}")

n = len(rows)
team_right = sum(r["team"] == r["gold_team"] for r in rows)
auto = [r for r in rows if r["team_conf"] >= ROUTE_AT]
human = [r for r in rows if r["team_conf"] < ROUTE_AT]
auto_right = sum(r["team"] == r["gold_team"] for r in auto)
human_right = sum(r["team"] == r["gold_team"] for r in human)
urg_exact = sum(round(r["urgency"]) == r["gold_urgency"] for r in rows)
frus_exact = sum(round(r["frustration"]) == r["gold_frustration"] for r in rows)
urg_near = sum(abs(round(r["urgency"]) - r["gold_urgency"]) <= 1 for r in rows)
times = sorted(r["seconds"] for r in rows)
tokens = sum(r["input_tokens"] for r in rows)

print()
print(f"model: {rows[0]['model']}, tickets: {n} (hand-made, labels by one person)")
print(f"team right: {team_right}/{n} = {team_right / n:.0%}")
print(f"  auto-routed (conf >= {ROUTE_AT}): {len(auto)} tickets, right {auto_right}/{len(auto)}")
print(f"  sent to humans (conf < {ROUTE_AT}): {len(human)} tickets, Jev's guess right "
      f"{human_right}/{len(human)}")
print(f"urgency level right (score rounded): {urg_exact}/{n}, within one level: {urg_near}/{n}")
print(f"frustration level right (score rounded): {frus_exact}/{n}")
print(f"time per call on this machine: median {statistics.median(times):.3f} s, "
      f"slowest {times[-1]:.3f} s, fastest {times[0]:.3f} s")
print(f"input tokens: {tokens} in total, {tokens / n:.0f} per ticket")
print(f"cost: ${cost_usd(tokens):.6f} for {n} tickets, "
      f"${cost_usd(tokens) / n * 1000:.4f} per 1,000 tickets of this size")

print("\nIs confidence honest here? Team accuracy by confidence bucket:")
for low, high in ((0.0, 0.6), (0.6, 0.9), (0.9, 1.01)):
    bucket = [r for r in rows if low <= r["team_conf"] < high]
    if bucket:
        right = sum(r["team"] == r["gold_team"] for r in bucket)
        print(f"  confidence {low:.1f} to {min(high, 1.0):.1f}: {len(bucket):2d} tickets, "
              f"right {right}/{len(bucket)}")
