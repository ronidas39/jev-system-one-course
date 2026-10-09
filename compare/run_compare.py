"""Compare Jev with OpenAI models on the same task, the same inputs, the same machine.

Three ways to run it, called protocols:

  accuracy   every item once, 8 calls in flight at a time, per model.
             Gives accuracy against the known truth, total cost, and the
             wall-clock time for the whole batch (the parallel timing).
  latency    a fixed sample, one call at a time, after 5 warm-up calls.
             The models take turns item by item, and the order rotates each
             round, so no model always gets the quiet network moment.
             Gives median and p90 latency per call (the sequential timing).
  batching   a fixed sample, two ways: all questions in ONE call, then one
             call PER question. Shows what asking many questions at once saves.

Every raw call (answer, seconds, tokens, dollars) is saved to compare/results/.

    python compare/run_compare.py --task tickets --protocol accuracy
    python compare/run_compare.py --task pairs --protocol latency --rounds 3

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
import platform
import random
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jevcourse.calls import (
    JEV_MODEL,
    CallResult,
    ask_jev,
    ask_openai,
    make_jev_client,
    make_openai_client,
)
from jevcourse.prices import PRICES_READ_ON
from jevcourse.tasks import (
    PAIR_SCHEMA,
    TICKET_QUESTIONS,
    TICKET_SCHEMA,
    TICKET_SYSTEM_PROMPT,
    pair_from_jev,
    pair_from_openai,
    pair_questions,
    pair_state,
    pair_system_prompt,
    pair_user_message,
    ticket_from_jev,
    ticket_from_openai,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "compare/results"
MODELS = [JEV_MODEL, "gpt-6-luna", "gpt-6.1-sol"]
WARM_UP_CALLS = 5
SAMPLE_SEED = 7

TASKS: dict[str, dict[str, Any]] = {
    "tickets": {
        "file": ROOT / "data/tickets.jsonl", "id": "id",
        "questions": TICKET_QUESTIONS, "prompt": TICKET_SYSTEM_PROMPT, "schema": TICKET_SCHEMA,
        "state": lambda item: item["text"], "user": lambda item: item["text"],
        "from_jev": ticket_from_jev, "from_openai": ticket_from_openai,
        "confidence_field": {"team": "team_confidence"},
    },
    "pairs": {
        "file": ROOT / "capstone/out/candidate_pairs.jsonl", "id": "pair_id", "wording": "v1",
        "questions": pair_questions("v1"), "prompt": pair_system_prompt("v1"),
        "schema": PAIR_SCHEMA, "state": pair_state, "user": pair_user_message,
        "from_jev": pair_from_jev, "from_openai": pair_from_openai,
        "confidence_field": {"link": "link_confidence"},
    },
    "pairs-v1-fresh": {
        "file": ROOT / "capstone/out/candidate_pairs-fresh.jsonl", "id": "pair_id",
        "wording": "v1", "questions": pair_questions("v1"), "prompt": pair_system_prompt("v1"),
        "schema": PAIR_SCHEMA, "state": pair_state, "user": pair_user_message,
        "from_jev": pair_from_jev, "from_openai": pair_from_openai,
        "confidence_field": {"link": "link_confidence"},
    },
    "pairs-v2-fresh": {
        "file": ROOT / "capstone/out/candidate_pairs-fresh.jsonl", "id": "pair_id",
        "wording": "v2", "questions": pair_questions("v2"), "prompt": pair_system_prompt("v2"),
        "schema": PAIR_SCHEMA, "state": pair_state, "user": pair_user_message,
        "from_jev": pair_from_jev, "from_openai": pair_from_openai,
        "confidence_field": {"link": "link_confidence"},
    },
}

_local = threading.local()


def clients() -> tuple[Any, Any]:
    """One Jev client and one OpenAI client per thread, made once and reused."""
    if not hasattr(_local, "jev"):
        _local.jev, _local.openai = make_jev_client(), make_openai_client()
    return _local.jev, _local.openai


def one_question_job(task: dict[str, Any], field: str) -> tuple[dict, str, dict]:
    """The task cut down to a single question, for the batching protocol."""
    questions = {field: task["questions"][field]}
    conf = task["confidence_field"].get(field)
    keep = [field] + ([conf] if conf else [])
    lines = task["prompt"].split("\n")
    prompt = "\n".join([lines[0]] + [ln for ln in lines[1:] if ln.split(":")[0] in keep])
    body = task["schema"]["schema"]
    schema = {"name": f"{task['schema']['name']}_{field}", "strict": True,
              "schema": {**body, "required": keep,
                         "properties": {k: body["properties"][k] for k in keep}}}
    return questions, prompt, schema


def call(model: str, task: dict[str, Any], item: dict[str, Any],
         questions: dict | None = None, prompt: str | None = None,
         schema: dict | None = None) -> CallResult:
    """Ask one model about one item."""
    jev, openai = clients()
    if model == JEV_MODEL:
        return ask_jev(jev, task["state"](item), questions or task["questions"])
    return ask_openai(openai, model, prompt or task["prompt"], task["user"](item),
                      schema or task["schema"])


def record(model: str, task: dict[str, Any], item: dict[str, Any], result: CallResult,
           **extra: Any) -> dict[str, Any]:
    """One saved row: the raw call plus the answer in the common form."""
    convert: Callable[[dict], dict] = task["from_jev" if model == JEV_MODEL else "from_openai"]
    try:
        common = convert(result.answer)
    except KeyError:
        common = None
    return {"item": item[task["id"]], "model": model, **extra, "common": common,
            **result.to_dict()}


def safe_call(model: str, task: dict[str, Any], item: dict[str, Any],
              **kw: Any) -> CallResult | dict[str, str]:
    """Call, but keep going when one call fails. Failures are saved, not hidden."""
    try:
        return call(model, task, item, **kw)
    except Exception as error:  # noqa: BLE001  any API failure is recorded as a row
        return {"error": f"{type(error).__name__}: {str(error)[:200]}"}


def run_accuracy(task: dict[str, Any], items: list[dict], models: list[str],
                 workers: int) -> list[dict]:
    """Every item once per model, `workers` calls in flight."""
    rows: list[dict] = []
    for model in models:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda it, m=model: safe_call(m, task, it), items))
        wall = time.perf_counter() - start
        for item, res in zip(items, results, strict=True):
            if isinstance(res, dict):
                rows.append({"item": item[task["id"]], "model": model, **res})
            else:
                rows.append(record(model, task, item, res))
        rows.append({"model": model, "batch_wall_seconds": wall, "workers": workers,
                     "items": len(items)})
        print(f"  {model:<14} {len(items)} items in {wall:6.1f} s with {workers} workers")
    return rows


def run_latency(task: dict[str, Any], items: list[dict], models: list[str],
                rounds: int) -> list[dict]:
    """One call at a time, models taking turns, order rotating every round."""
    for model in models:
        for item in items[:WARM_UP_CALLS]:
            safe_call(model, task, item)
    print(f"  warm-up done: {WARM_UP_CALLS} calls per model, not counted")
    rows: list[dict] = []
    for rnd in range(rounds):
        for i, item in enumerate(items):
            shift = (i + rnd) % len(models)
            for model in models[shift:] + models[:shift]:
                res = safe_call(model, task, item)
                if isinstance(res, dict):
                    rows.append({"item": item[task["id"]], "model": model, "round": rnd, **res})
                else:
                    rows.append(record(model, task, item, res, round=rnd))
        print(f"  round {rnd + 1}/{rounds} done")
    return rows


def run_batching(task: dict[str, Any], items: list[dict], models: list[str]) -> list[dict]:
    """All questions in one call, then one call per question, for the same items."""
    rows: list[dict] = []
    fields = list(task["questions"])
    for item in items:
        for model in models:
            res = safe_call(model, task, item)
            if not isinstance(res, dict):
                rows.append(record(model, task, item, res, mode="one_call"))
            for field in fields:
                q, p, s = one_question_job(task, field)
                res = safe_call(model, task, item, questions=q, prompt=p, schema=s)
                if not isinstance(res, dict):
                    row = res.to_dict()
                    rows.append({"item": item[task["id"]], "model": model,
                                 "mode": "one_call_per_question", "field": field, **row})
    return rows


def main() -> None:
    """Run one protocol on one task and save every call."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--task", choices=list(TASKS), required=True)
    parser.add_argument("--protocol", choices=["accuracy", "latency", "batching"], required=True)
    parser.add_argument("--models", default=",".join(MODELS))
    parser.add_argument("--sample", type=int, default=40, help="items for latency and batching")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="use only the first N items")
    args = parser.parse_args()

    task = TASKS[args.task]
    items = [json.loads(line) for line in Path(task["file"]).read_text().splitlines()]
    if args.limit:
        items = items[: args.limit]
    if args.protocol != "accuracy":
        items = random.Random(SAMPLE_SEED).sample(items, min(args.sample, len(items)))
    models = args.models.split(",")
    started = datetime.now(timezone.utc)
    print(f"{args.task} / {args.protocol}: {len(items)} items, models {models}")

    if args.protocol == "accuracy":
        rows = run_accuracy(task, items, models, args.workers)
    elif args.protocol == "latency":
        rows = run_latency(task, items, models, args.rounds)
    else:
        rows = run_batching(task, items, models)

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.task}-{args.protocol}.jsonl"
    meta = {"meta": True, "task": args.task, "protocol": args.protocol, "models": models,
            "items": len(items), "rounds": args.rounds, "wording": task.get("wording"), "workers": args.workers,
            "started_utc": started.isoformat(timespec="seconds"),
            "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "machine": f"{platform.system()} {platform.machine()}, Python "
                       f"{platform.python_version()}",
            "prices_read_on": PRICES_READ_ON}
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [meta, *rows]))
    errors = sum(1 for r in rows if "error" in r)
    print(f"saved {len(rows)} rows to {out.relative_to(ROOT)} ({errors} failed calls)")


if __name__ == "__main__":
    main()
