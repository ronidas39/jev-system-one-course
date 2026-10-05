"""Show the pairs that the merge rule sent to a person: the review list.

Step 2 sends a pair to a person when Jev's link score lands in the middle (0.5 to 1.5).
This prints those pairs side by side, so a person can look at them. It also shows the score,
whether other merges have already joined the two records, and the answer from truth.json
(the data maker's answer key; in real life you do not have one, so a person decides).

    python capstone/show_review.py
    python capstone/show_review.py --data companies-fresh   # the test set
    python capstone/show_review.py --data companies-fresh --limit 0   # every pair

Author: Roni Das
Created: 2026-10-05
"""

import argparse
import json
from pathlib import Path

from jevcourse.calls import JEV_MODEL

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Print the review list for one decisions file."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=JEV_MODEL)
    parser.add_argument("--wording", choices=["v1", "v2"], default="v2")
    parser.add_argument("--data", default="companies",
                        help="companies (the training set) or companies-fresh (the test set)")
    parser.add_argument("--limit", type=int, default=4,
                        help="print this many from the top and from the bottom; 0 = all")
    args = parser.parse_args()

    tag = "" if args.data == "companies" else "-fresh"
    path = ROOT / f"capstone/out/decisions-{args.model}-{args.wording}{tag}.jsonl"
    decisions = [json.loads(line) for line in path.read_text().splitlines()]
    truth = json.loads((ROOT / f"data/{args.data}/truth.json").read_text())["record_to_entity"]
    records = {r["record_id"]: r for r in
               map(json.loads, (ROOT / f"data/{args.data}/records.jsonl").read_text().splitlines())}

    parent = {rid: rid for rid in records}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for d in decisions:
        if d["action"] == "merge":
            parent[find(d["a"])] = find(d["b"])

    review = sorted((d for d in decisions if d["action"] == "person_checks"),
                    key=lambda d: d["link_score"], reverse=True)
    joined = sum(find(d["a"]) == find(d["b"]) for d in review)
    print(f"{len(review)} pairs wait for a person "
          f"({joined} of them already joined through other merges)")
    same = sum(truth[d["a"]] == truth[d["b"]] for d in review)
    print(f"answer key: {same} of the {len(review)} are really the same company\n")
    n = args.limit
    shown = review if not n or len(review) <= 2 * n else review[:n] + review[-n:]
    for i, d in enumerate(shown):
        if n and len(review) > 2 * n and i == n:
            print(f"... {len(review) - 2 * n} more in the middle ...\n")
        a, b = records[d["a"]], records[d["b"]]
        note = "   (already joined through other merges)" if find(d["a"]) == find(d["b"]) else ""
        answer = "same company" if truth[d["a"]] == truth[d["b"]] else "different companies"
        print(f"link score {d['link_score']:.2f}   answer key: {answer}{note}")
        for r in (a, b):
            print(f"  {r['source']:<8} {r['name']:<42} {r['address']}, {r['country']}")
            print(f"  {'':<8} phone {r['phone'] or '-':<18} website {r['website'] or '-'}")
        print()


if __name__ == "__main__":
    main()
