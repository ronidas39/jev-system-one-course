"""Step 2: ask a model about every candidate pair, then apply the merge policy.

Each pair gets the same three questions as use case 4 (one Score, two Nouls),
in one call. Then the policy turns the answer into an action:

  score rounds to 2  ->  merge          the two records become one company
  score rounds to 1  ->  person checks  a human looks before anything changes
  score rounds to 0  ->  keep separate

Eight calls run at the same time, so 1,010 pairs take seconds, not minutes.

    python capstone/step2_decide.py                      # Jev, wording v2
    python capstone/step2_decide.py --wording v1         # the first wording
    python capstone/step2_decide.py --model gpt-6-luna   # the same job on an OpenAI model
    python capstone/step2_decide.py --data companies-fresh   # the test set

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from jevcourse.calls import JEV_MODEL, ask_jev, ask_openai, make_jev_client, make_openai_client
from jevcourse.tasks import (
    PAIR_SCHEMA,
    pair_from_jev,
    pair_from_openai,
    pair_questions,
    pair_state,
    pair_system_prompt,
    pair_user_message,
)

ROOT = Path(__file__).resolve().parents[1]
ACTION = {2: "merge", 1: "person_checks", 0: "keep_separate"}
WORKERS = 8
_local = threading.local()


ATTEMPTS = 3
"""A batch job should not die on one slow call. Try up to 3 times, waiting 2 s, then 4 s."""


def decide(model: str, wording: str, pair: dict[str, Any]) -> dict[str, Any]:
    """One pair, with retries. If every try fails, the pair goes to a person."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return {**decide_once(model, wording, pair), "attempts": attempt}
        except Exception as error:  # noqa: BLE001  timeouts, rate limits, server errors
            last = f"{type(error).__name__}: {str(error)[:200]}"
            if any(w in type(error).__name__ for w in ("Authentication", "Permission", "BadRequest")):
                raise  # a wrong key or a broken request will not fix itself; stop and say so
            if attempt < ATTEMPTS:
                time.sleep(2 ** attempt)
    print(f"  pair {pair['pair_id']}: {ATTEMPTS} tries failed ({last}); a person checks it")
    return {"pair_id": pair["pair_id"], "a": pair["a"]["record_id"], "b": pair["b"]["record_id"],
            "action": "person_checks", "error": last, "attempts": ATTEMPTS,
            "seconds": 0.0, "input_tokens": 0, "usd": 0.0}


def decide_once(model: str, wording: str, pair: dict[str, Any]) -> dict[str, Any]:
    """One call about one pair, turned into an action."""
    if not hasattr(_local, "client"):
        _local.client = make_jev_client() if model == JEV_MODEL else make_openai_client()
    if model == JEV_MODEL:
        result = ask_jev(_local.client, pair_state(pair), pair_questions(wording))
        common = pair_from_jev(result.answer)
    else:
        result = ask_openai(_local.client, model, pair_system_prompt(wording),
                            pair_user_message(pair), PAIR_SCHEMA)
        common = pair_from_openai(result.answer)
    return {"pair_id": pair["pair_id"], "a": pair["a"]["record_id"], "b": pair["b"]["record_id"],
            "action": ACTION[common["link"]], **common, "seconds": result.seconds,
            "input_tokens": result.input_tokens, "usd": result.usd}


def main() -> None:
    """Decide every pair and save the decisions."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=JEV_MODEL)
    parser.add_argument("--wording", choices=["v1", "v2"], default="v2",
                        help="which wording of the middle level to use (see jevcourse/tasks.py)")
    parser.add_argument("--data", default="companies",
                        help="companies (the training set) or companies-fresh (the test set)")
    parser.add_argument("--pairs", default="",
                        help="a candidate-pairs file; by default the one step 1 wrote for --data")
    args = parser.parse_args()
    if not args.pairs:
        tag = "" if args.data == "companies" else "-" + args.data.removeprefix("companies-")
        args.pairs = f"capstone/out/candidate_pairs{tag}.jsonl"
    pairs = [json.loads(line) for line in (ROOT / args.pairs).read_text().splitlines()]
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        decisions = list(pool.map(lambda p: decide(args.model, args.wording, p), pairs))
    wall = time.perf_counter() - start
    tag = "" if args.pairs.endswith("candidate_pairs.jsonl") else "-fresh"
    out = ROOT / f"capstone/out/decisions-{args.model}-{args.wording}{tag}.jsonl"
    out.write_text("".join(json.dumps(d) + "\n" for d in decisions))
    counts = {a: sum(d["action"] == a for d in decisions) for a in ACTION.values()}
    usd = sum(d["usd"] for d in decisions)
    print(f"{args.model}, wording {args.wording}: {len(pairs)} pairs in {wall:.1f} s ({WORKERS} calls at a time)")
    print(f"merge {counts['merge']}, person checks {counts['person_checks']}, "
          f"keep separate {counts['keep_separate']}")
    print(f"cost ${usd:.4f} in total, ${usd / len(pairs) * 1000:.4f} per 1,000 pairs")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
