"""Jev against OpenAI's Decisions API on the same 300 support tickets.

OpenAI released the Decisions API in public beta on 6 October 2026, after the
first comparison in this repo was made. It works like Jev: you send the text and
typed questions, and you get probabilities back instead of written text. So this
folder runs the ticket triage again, with the same tickets, the same labels and
the same three questions, against Jev and against POST /v1/decisions.

Protocols, each saved to compare_decisions/results/<protocol>.jsonl with every
raw response:

  accuracy   all 300 tickets once per API, 8 calls in flight. Accuracy, total
             cost from each API's own usage numbers, wall-clock time.
  latency    40 tickets (seed 7), one call at a time, 3 rounds, the two APIs
             taking turns with the order swapped each round, after 5 warm-ups.
  batching   the same 40 tickets: all three questions in one call, then one
             call per question.
  baseline   the same three questions with the input "." (3 calls per API).
             Subtracting this from a ticket's token count gives the tokens of
             the ticket text alone, in each API's own tokenizer.

    python compare_decisions/run_decisions.py --protocol accuracy
    python compare_decisions/summarize.py

Prices (read 2026-10-09):
  Jev, $0.042 per million input tokens, output free:
      https://docs.typesafe.ai/models
  Decisions API with gpt-6-luna, $0.10 per million input tokens, no output,
  cache-read or cache-write charges:
      https://developers.openai.com/api/docs/guides/decisions#pricing-and-availability

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import json
import platform
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from jevcourse.calls import JEV_MODEL, ask_jev, make_jev_client
from jevcourse.config import require_key
from jevcourse.tasks import (
    FRUSTRATION_LEVELS,
    TEAMS,
    TICKET_QUESTIONS,
    URGENCY_LEVELS,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "compare_decisions/results"
TICKETS = ROOT / "data/tickets.jsonl"
DECISIONS = "decisions/gpt-6-luna"
APIS = [JEV_MODEL, DECISIONS]
PRICES_READ_ON = "2026-10-09"
JEV_USD_PER_M_INPUT = 0.042
DECISIONS_USD_PER_M_INPUT = 0.10
SAMPLE_SEED = 7
WARM_UP_CALLS = 5
MAX_CALLS_PER_RUN = 1200
"""A hard stop, so a bug can never turn into a large bill."""

# The same three questions as jevcourse.tasks.TICKET_QUESTIONS, word for word, in
# the Decisions request shape. A Jev Score criterion is one string per level; a
# Decisions level needs a label, so the label carries that same string.
DECISION_QUESTIONS: list[dict[str, Any]] = [
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

_local = threading.local()
_calls = 0
_calls_lock = threading.Lock()


def _count_call() -> None:
    global _calls
    with _calls_lock:
        _calls += 1
        if _calls > MAX_CALLS_PER_RUN:
            raise SystemExit(f"stopped: more than {MAX_CALLS_PER_RUN} calls in one run")


def clients() -> tuple[Any, OpenAI]:
    """One client per API per thread, made once and reused, retries off."""
    if not hasattr(_local, "jev"):
        require_key("OPENAI_API_KEY")
        _local.jev = make_jev_client()
        _local.openai = OpenAI(max_retries=0, timeout=60.0)
    return _local.jev, _local.openai


def ask_decisions(client: OpenAI, text: str, questions: list[dict[str, Any]]) -> dict[str, Any]:
    """One POST /v1/decisions call, timed, with the raw response kept."""
    body = {"model": "gpt-6-luna", "input": text, "questions": questions}
    start = time.perf_counter()
    raw = client.post("/decisions", cast_to=object, body=body)
    seconds = time.perf_counter() - start
    usage = raw.get("usage", {})
    tokens = int(usage.get("input_tokens") or 0)
    return {"seconds": seconds, "input_tokens": tokens,
            "output_tokens": int(usage.get("output_tokens") or 0),
            "usd": tokens * DECISIONS_USD_PER_M_INPUT / 1e6, "raw": raw}


def common_from_decisions(raw: dict[str, Any]) -> dict[str, Any] | None:
    """The answers in the same plain form tasks.ticket_from_jev uses."""
    ans = {a.get("name"): a for a in raw.get("answers", [])}
    if any(a.get("type") == "refusal" for a in ans.values()) or len(ans) < 3:
        return None
    return {"team": ans["team"]["choice"], "team_confidence": ans["team"]["confidence"],
            "urgency": round(ans["urgency"]["score"]),
            "frustration": round(ans["frustration"]["score"])}


def common_from_jev(answers: dict[str, Any]) -> dict[str, Any]:
    """Jev's answers in the plain form (same rule as jevcourse.tasks.ticket_from_jev)."""
    return {"team": answers["team"]["choice"], "team_confidence": answers["team"]["confidence"],
            "urgency": round(answers["urgency"]["score"]),
            "frustration": round(answers["frustration"]["score"])}


def one_call(api: str, ticket: dict[str, Any], only: str | None = None,
             text: str | None = None) -> dict[str, Any]:
    """Ask one API about one ticket. Failures are saved as rows, never hidden."""
    _count_call()
    jev, oa = clients()
    state = ticket["text"] if text is None else text
    row: dict[str, Any] = {"item": ticket.get("id"), "api": api, "question": only or "all"}
    try:
        if api == JEV_MODEL:
            qs = {only: TICKET_QUESTIONS[only]} if only else TICKET_QUESTIONS
            res = ask_jev(jev, state, qs)
            row.update(seconds=res.seconds, input_tokens=res.input_tokens,
                       output_tokens=res.output_tokens, usd=res.usd,
                       raw={"model": res.model, "answers": res.answer, "usage": res.raw_usage})
            if not only:
                row["common"] = common_from_jev(res.answer)
        else:
            qs = [q for q in DECISION_QUESTIONS if only in (None, q["name"])]
            row.update(ask_decisions(oa, state, qs))
            row["refusals"] = sum(a.get("type") == "refusal" for a in row["raw"]["answers"])
            if not only:
                row["common"] = common_from_decisions(row["raw"])
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001  any API failure is recorded as a row
        row["error"] = f"{type(error).__name__}: {str(error)[:300]}"
    return row


def run_accuracy(tickets: list[dict], workers: int) -> list[dict]:
    rows: list[dict] = []
    for api in APIS:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            got = list(pool.map(lambda t, a=api: one_call(a, t), tickets))
        wall = time.perf_counter() - start
        rows += got
        rows.append({"api": api, "batch_wall_seconds": wall, "workers": workers,
                     "items": len(tickets)})
        print(f"  {api:<22} {len(tickets)} tickets in {wall:6.1f} s, {workers} in flight, "
              f"{sum('error' in r for r in got)} failed")
    return rows


def run_latency(tickets: list[dict], rounds: int) -> list[dict]:
    for api in APIS:
        for t in tickets[:WARM_UP_CALLS]:
            one_call(api, t)
    rows: list[dict] = []
    for rnd in range(rounds):
        for i, t in enumerate(tickets):
            order = APIS if (i + rnd) % 2 == 0 else APIS[::-1]
            for api in order:
                rows.append({**one_call(api, t), "round": rnd})
        print(f"  round {rnd + 1}/{rounds} done")
    return rows


def run_batching(tickets: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for t in tickets:
        for api in APIS:
            rows.append({**one_call(api, t), "mode": "one_call"})
            for q in ("team", "urgency", "frustration"):
                rows.append({**one_call(api, t, only=q), "mode": "one_call_per_question"})
    return rows


def run_baseline() -> list[dict]:
    return [{**one_call(api, {"id": "baseline"}, text="."), "try": k}
            for api in APIS for k in range(3)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--protocol", required=True,
                        choices=["accuracy", "latency", "batching", "baseline"])
    parser.add_argument("--sample", type=int, default=40)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    tickets = [json.loads(line) for line in TICKETS.read_text().splitlines()]
    if args.protocol in ("latency", "batching"):
        tickets = random.Random(SAMPLE_SEED).sample(tickets, args.sample)
    started = datetime.now(UTC)
    print(f"{args.protocol}: {len(tickets)} tickets, APIs {APIS}")
    if args.protocol == "accuracy":
        rows = run_accuracy(tickets, args.workers)
    elif args.protocol == "latency":
        rows = run_latency(tickets, args.rounds)
    elif args.protocol == "batching":
        rows = run_batching(tickets)
    else:
        rows = run_baseline()

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.protocol}.jsonl"
    meta = {"meta": True, "protocol": args.protocol, "apis": APIS, "items": len(tickets),
            "rounds": args.rounds, "workers": args.workers, "calls": _calls,
            "started_utc": started.isoformat(timespec="seconds"),
            "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "machine": f"{platform.system()} {platform.machine()}, Python "
                       f"{platform.python_version()}",
            "prices_read_on": PRICES_READ_ON,
            "decisions_questions": DECISION_QUESTIONS}
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in [meta, *rows]))
    errors = sum(1 for r in rows if "error" in r)
    print(f"saved {len(rows)} rows to {out.relative_to(ROOT)} ({_calls} calls, {errors} failed)")


if __name__ == "__main__":
    main()
