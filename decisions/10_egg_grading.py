"""Decisions 10: grade 33 egg photos, then decide what to do with the odds.

Steps, in the order the course runs them:

    plan      count the calls and estimate the bill. No network, no cost.
    classify  one call per photo. Saves every raw answer to results/<run>/calls.jsonl.
    sweep     no network: try pairs of cut-offs on P(not clean) against the labels.
    repeat    send the SAME photo three times, to see if the odds move.
    compare   the same photos through the Responses API, asking Luna to write JSON.

Every number this prints comes from a saved response. sweep reads only the saved
file, so you can run it again and again for free.

The labels in eggs/labels.csv are the course author's labels, made by eye.
They are drafts, not an expert's grades. See eggs/CREDITS.md.

    python 10_egg_grading.py plan
    python 10_egg_grading.py classify
    python 10_egg_grading.py sweep
    python 10_egg_grading.py sweep --run reference     # the run recorded for the course

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from common import (MODEL, USD_PER_MILLION_INPUT_TOKENS, check_key_present, cost_usd,
                    image_data_url, log_call, make_client)
from egg_questions import EGG_QUESTIONS, OPTIONS

HERE = Path(__file__).resolve().parent
EGGS = HERE / "eggs"
MAX_CALLS = 100
"""A hard stop for one command, so a bug can never turn into a big bill."""
LUNA_USD_PER_MILLION_OUTPUT = 0.50
"""gpt-6-luna output price on the Responses API, read 9 October 2026 (models page)."""
CUT_PAIRS = [(0.50, 0.50), (0.20, 0.80), (0.10, 0.90), (0.30, 0.70)]


def photos() -> list[str]:
    with (EGGS / "photos.csv").open() as fh:
        return [row["egg"] for row in csv.DictReader(fh)]


def labels() -> dict[str, str]:
    with (EGGS / "labels.csv").open() as fh:
        return {row["egg"]: row["condition"] for row in csv.DictReader(fh)}


def photo_input(egg: str) -> list[dict[str, Any]]:
    return [{"role": "user", "content": [
        {"type": "input_text", "text": "One egg from a grading line."},
        {"type": "input_image", "image_url": image_data_url(EGGS / f"{egg}.jpg")},
    ]}]


class Budget:
    """Counts paid calls and stops before MAX_CALLS."""

    def __init__(self) -> None:
        check_key_present()
        self.client = make_client()
        self.used = 0

    def tick(self) -> None:
        self.used += 1
        if self.used > MAX_CALLS:
            sys.exit(f"stopped: more than {MAX_CALLS} calls in one command")


def decide(budget: Budget, egg: str, questions: list[dict[str, Any]]) -> tuple[dict, float]:
    budget.tick()
    start = time.perf_counter()
    decision = budget.client.decisions.create(model=MODEL, input=photo_input(egg),
                                              questions=questions)
    seconds = time.perf_counter() - start
    log_call("10_egg_grading.py", decision.usage.input_tokens, seconds, note=egg)
    return decision.model_dump(), seconds * 1000


def p_clean(response: dict) -> float | None:
    """P(clean) from a saved response, or None if the condition question was refused."""
    for answer in response["answers"]:
        if answer["name"] == "condition" and answer["type"] == "choice":
            return next(p["probability"] for p in answer["probabilities"] if p["value"] == "clean")
    return None


def save(out: Path, rows: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "calls.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def load(out: Path) -> list[dict]:
    path = out / "calls.jsonl"
    if not path.exists():
        sys.exit(f"no saved calls in {path.relative_to(HERE)}: run `classify` first")
    return [json.loads(line) for line in path.read_text().splitlines()]


def cmd_plan() -> None:
    eggs = photos()
    print(f"{len(eggs)} photos, {len(EGG_QUESTIONS)} questions per call, one call per photo")
    for tokens in (300, 500, 1000):
        usd = len(eggs) * tokens * USD_PER_MILLION_INPUT_TOKENS / 1e6
        print(f"  if a call reads {tokens:>4} input tokens: {len(eggs)} calls cost ${usd:.4f}")
    print(f"price used: ${USD_PER_MILLION_INPUT_TOKENS} per million input tokens, no output charge")


def cmd_classify(out: Path) -> None:
    budget = Budget()
    truth = labels()
    rows = []
    print(f"{'photo':<10} {'label':<8} {'clean':>5} {'dirty':>5} {'crack':>5} {'unclr':>5}"
          f"  {'ms':>5} {'tokens':>6}")
    for egg in photos():
        response, ms = decide(budget, egg, EGG_QUESTIONS)
        rows.append({"step": "classify", "egg": egg, "latency_ms": round(ms, 1),
                     "response": response})
        cond = next(a for a in response["answers"] if a["name"] == "condition")
        if cond["type"] == "refusal":
            cells = "REFUSED".ljust(23)
        else:
            o = {p["value"]: p["probability"] for p in cond["probabilities"]}
            cells = " ".join(f"{o.get(k, 0):5.2f}" for k in OPTIONS)
        print(f"{egg:<10} {truth[egg]:<8} {cells}  {ms:5.0f} {response['usage']['input_tokens']:>6}")
    save(out, rows)
    tokens = [r["response"]["usage"]["input_tokens"] for r in rows]
    ms = [r["latency_ms"] for r in rows]
    print(f"\n{len(rows)} calls, median {statistics.median(ms):.0f} ms, "
          f"median {statistics.median(tokens):.0f} input tokens, "
          f"total ${cost_usd(sum(tokens)):.6f}, saved to {out.relative_to(HERE)}/calls.jsonl")


def cmd_sweep(out: Path) -> None:
    truth = labels()
    points = [(r["egg"], 1.0 - p) for r in load(out)
              if r["step"] == "classify" and (p := p_clean(r["response"])) is not None]
    bad = sum(1 for egg, _ in points if truth[egg] != "clean")
    print(f"{len(points)} photos, {bad} not clean by my labels. "
          f"Score = P(not clean) = 1 - P(clean).")
    print(f"{'pass below':>10} {'reject above':>12} {'passed bad':>10} {'rejected good':>13}"
          f" {'to a person':>11}")
    for low, high in CUT_PAIRS:
        passed_bad = sum(1 for e, s in points if s < low and truth[e] != "clean")
        rejected_good = sum(1 for e, s in points if s > high and truth[e] == "clean")
        person = sum(1 for _, s in points if low <= s <= high)
        print(f"{low:>10.2f} {high:>12.2f} {passed_bad:>10} {rejected_good:>13} {person:>11}")
    low, high = CUT_PAIRS[-1]
    middle = [f"{e} {s:.2f} ({truth[e]})" for e, s in points if low <= s <= high]
    print(f"\nsent to a person with cut-offs {low:.2f} / {high:.2f}:")
    for line in middle:
        print(f"  {line}")


def cmd_repeat(out: Path, n: int) -> None:
    budget = Budget()
    rows = []
    for egg in photos()[::4][:n]:
        tries = []
        for k in range(3):
            response, ms = decide(budget, egg, EGG_QUESTIONS[:1])
            rows.append({"step": "repeat", "egg": egg, "try": k, "latency_ms": round(ms, 1),
                         "response": response})
            tries.append(p_clean(response))
        gap = max(tries) - min(tries)
        print(f"{egg:<10} P(clean) on 3 tries: {tries}   largest gap {gap:.3f}")
    save(out / "repeat", rows)


def written_answer(response: Any) -> str:
    try:
        return str(json.loads(response.output_text)["condition"])
    except (ValueError, KeyError, TypeError):
        return "unparsed"


def cmd_compare(out: Path, n: int) -> None:
    """The same photos, the same one question, asked two ways, back to back."""
    budget = Budget()
    truth = labels()
    schema = {"type": "object", "additionalProperties": False, "required": ["condition"],
              "properties": {"condition": {"type": "string", "enum": OPTIONS}}}
    rows = []
    stats: dict[str, dict[str, list[float]]] = {
        k: {"ms": [], "usd": [], "right": []} for k in ("decisions", "responses")}
    print(f"{'photo':<10} {'label':<8} {'decisions':<16} {'responses (writes JSON)':<24}")
    for egg in photos()[::2][:n]:
        response, ms = decide(budget, egg, EGG_QUESTIONS[:1])
        o = {p["value"]: p["probability"] for p in response["answers"][0].get("probabilities", [])}
        top = max(o, key=o.get) if o else "refusal"
        stats["decisions"]["ms"].append(ms)
        stats["decisions"]["usd"].append(cost_usd(response["usage"]["input_tokens"]))
        stats["decisions"]["right"].append(top == truth[egg])

        budget.tick()
        start = time.perf_counter()
        written = budget.client.responses.create(
            model=MODEL, reasoning={"effort": "none"},
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": "One egg from a grading line. Is the shell "
                 "clean, dirty, cracked, or is the photo unclear? Answer in the JSON schema."},
                {"type": "input_image", "image_url": image_data_url(EGGS / f"{egg}.jpg")},
            ]}],
            text={"format": {"type": "json_schema", "name": "egg", "schema": schema,
                             "strict": True}})
        ms2 = (time.perf_counter() - start) * 1000
        said = written_answer(written)
        usd2 = (written.usage.input_tokens * USD_PER_MILLION_INPUT_TOKENS
                + written.usage.output_tokens * LUNA_USD_PER_MILLION_OUTPUT) / 1e6
        log_call("10_egg_grading.py", written.usage.input_tokens, ms2 / 1000, note=egg,
                 provider="openai-responses", output_tokens=written.usage.output_tokens, usd=usd2)
        stats["responses"]["ms"].append(ms2)
        stats["responses"]["usd"].append(usd2)
        stats["responses"]["right"].append(said == truth[egg])
        rows.append({"step": "compare", "egg": egg, "decisions_ms": round(ms, 1),
                     "decisions": response, "responses_ms": round(ms2, 1),
                     "responses": written.model_dump()})
        print(f"{egg:<10} {truth[egg]:<8} {top + f' {o.get(top, 0):.2f}':<16} {said:<24}")
    save(out / "compare", rows)
    print()
    for k, st in stats.items():
        print(f"{k:<10} median {statistics.median(st['ms']):5.0f} ms, matched my label "
              f"{sum(st['right'])}/{len(st['right'])}, "
              f"${sum(st['usd']) / len(st['usd']) * 1000:.4f} per 1,000 photos")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["plan", "classify", "sweep", "repeat", "compare"])
    parser.add_argument("--run", default="mine", help="folder name under results/")
    parser.add_argument("--n", type=int, default=4, help="photos for repeat or compare")
    args = parser.parse_args()
    out = HERE / "results" / args.run
    if args.step == "plan":
        cmd_plan()
    elif args.step == "classify":
        cmd_classify(out)
    elif args.step == "sweep":
        cmd_sweep(out)
    elif args.step == "repeat":
        cmd_repeat(out, args.n)
    else:
        cmd_compare(out, args.n)


if __name__ == "__main__":
    main()
