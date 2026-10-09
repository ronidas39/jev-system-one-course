"""Put every player of one race run side by side: crashes, slow-downs, speed, cost.

    python race/compare.py                    # your runs, in results/race/mine
    python race/compare.py --run reference    # the runs recorded for the course

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = ["text", "jev", "picture", "clip1", "clip3"]
SAYS = {"text": "Decisions, road as text", "jev": "Jev, road as text",
        "picture": "Decisions, one picture", "clip1": "Decisions, 1 video frame",
        "clip3": "Decisions, 3 video frames"}

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--run", default="mine")
args = parser.parse_args()
folder = HERE.parent / "results" / "race" / args.run
print(f"{'player':<27} {'crashes':>7} {'slow':>5} {'moves':>6} {'median ms':>9} "
      f"{'tokens/step':>11} {'$ per 1,000':>11}")
for name in ORDER:
    for path in sorted(folder.glob(f"{name}-seed*.jsonl")):
        meta, *rows = [json.loads(line) for line in path.read_text().splitlines()]
        crashes = sum(r["action"] == "CRASH" for r in rows)
        slow = sum(r["action"] == "slow down" for r in rows)
        ms = statistics.median(r["seconds"] for r in rows) * 1000
        tokens = sum(r["tokens"] for r in rows) / len(rows)
        usd = sum(r["usd"] for r in rows) / len(rows) * 1000
        print(f"{SAYS[name]:<27} {crashes:>7} {slow:>5} {len(rows) - crashes - slow:>6} "
              f"{ms:>9.0f} {tokens:>11.0f} {usd:>11.4f}")
print(f"\nseed {meta['seed']}, {meta['steps']} steps each, cut-off {meta['cutoff']}")
