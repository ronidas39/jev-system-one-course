"""Turn the saved Jev and Decisions API calls into summary.json and summary.md.

Every number here is computed from compare_decisions/results/*.jsonl. Nothing is typed in.

    python compare_decisions/summarize.py

Author: Roni Das
Created: 2026-10-09
"""

import json
import statistics
from pathlib import Path
from typing import Any

from jevcourse.calls import percentile

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "compare_decisions/results"
GROUPS = [(0.9, 1.01), (0.7, 0.9), (0.5, 0.7), (0.0, 0.5)]


def load(name: str) -> tuple[dict, list[dict]]:
    lines = [json.loads(x) for x in (RESULTS / f"{name}.jsonl").read_text().splitlines()]
    return lines[0], lines[1:]


def main() -> None:
    gold = {t["id"]: t for t in map(json.loads,
                                     (ROOT / "data/tickets.jsonl").read_text().splitlines())}
    texts = {k: v["text"] for k, v in gold.items()}
    _, base = load("baseline")
    _, acc = load("accuracy")
    _, lat = load("latency")
    _, bat = load("batching")
    apis = sorted({r["api"] for r in acc if "api" in r})
    out: dict[str, Any] = {"apis": {}}
    for api in apis:
        calls = [r for r in acc if r.get("api") == api and "item" in r]
        ok = [r for r in calls if r.get("common")]
        wall = next(r for r in acc if r.get("api") == api and "batch_wall_seconds" in r)
        b = [r["input_tokens"] for r in base if r["api"] == api]
        baseline = statistics.median(b)
        per_ticket = [r["input_tokens"] for r in calls if "input_tokens" in r]
        chars = [len(texts[r["item"]]) for r in calls if "input_tokens" in r]
        # Tokens = fixed part + slope x characters, fitted over all 300 tickets. The slope is
        # the tokenizer (tokens per character of ticket text); the fixed part is the questions
        # and the API's own wrapping. The "." baseline is kept only as an observation: the
        # Decisions API billed 270 tokens for "." but about 466 fixed tokens on real tickets.
        slope, fixed = statistics.linear_regression(chars, per_ticket)
        usd = sum(r.get("usd", 0) for r in calls)
        lat_s = [r["seconds"] for r in lat if r["api"] == api and "seconds" in r]
        par_s = [r["seconds"] for r in calls if "seconds" in r]
        n = len(ok)

        def right(field: str, group: list[dict] = ok) -> int:
            return sum(r["common"][field] == gold[r["item"]][field] for r in group)

        one = [r for r in bat if r["api"] == api and r["mode"] == "one_call" and "usd" in r]
        split = [r for r in bat if r["api"] == api and r["mode"] == "one_call_per_question"
                 and "usd" in r]
        items = len({r["item"] for r in one})
        out["apis"][api] = {
            "calls": len(calls), "failed": sum("error" in r for r in calls),
            "refusals": sum(r.get("refusals", 0) for r in calls),
            "answered_all_three": n,
            "team_right": right("team"), "urgency_right": right("urgency"),
            "frustration_right": right("frustration"),
            "team_accuracy": right("team") / n, "urgency_accuracy": right("urgency") / n,
            "frustration_accuracy": right("frustration") / n,
            "input_tokens_total": sum(per_ticket),
            "output_tokens_total": sum(r.get("output_tokens", 0) for r in calls),
            "usd_total_300": usd, "usd_per_1000": usd / len(calls) * 1000,
            "wall_seconds_300_8_in_flight": wall["batch_wall_seconds"],
            "per_call_seconds_8_in_flight": {"p50": statistics.median(par_s),
                                             "p95": percentile(par_s, 95)},
            "per_call_seconds_one_at_a_time": {"calls": len(lat_s),
                                               "p50": statistics.median(lat_s),
                                               "p95": percentile(lat_s, 95)},
            "tokens_per_ticket_with_questions_mean": statistics.mean(per_ticket),
            "input_dot_tokens": baseline,
            "fixed_tokens_fitted": fixed,
            "ticket_text_tokens_mean": slope * statistics.mean(chars),
            "chars_per_text_token": 1 / slope,
            "fit_correlation": statistics.correlation(chars, per_ticket),
            "mean_ticket_chars": statistics.mean(chars),
            "team_by_confidence": [
                {"from": lo, "to": min(hi, 1.0), "answers": len(g), "right": right("team", g)}
                for lo, hi in GROUPS
                for g in [[r for r in ok if lo <= r["common"]["team_confidence"] < hi]]],
            "batching": {"tickets": items,
                         "tokens_one_call": sum(r["input_tokens"] for r in one) / items,
                         "tokens_split": sum(r["input_tokens"] for r in split) / items,
                         "usd_one_call": sum(r["usd"] for r in one) / items,
                         "usd_split": sum(r["usd"] for r in split) / items,
                         "median_s_one_call": statistics.median(r["seconds"] for r in one)},
        }
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=1) + "\n")

    s = out["apis"]
    md = ["# Jev against the OpenAI Decisions API: 300 support tickets", "",
          "Computed by `compare_decisions/summarize.py` from the raw calls in this folder.", "",
          "| measure | " + " | ".join(apis) + " |", "|---|" + "---|" * len(apis)]

    def row(label: str, fn: Any) -> None:
        md.append(f"| {label} | " + " | ".join(fn(s[a]) for a in apis) + " |")

    row("team right", lambda x: f"{x['team_right']}/300 ({x['team_accuracy']:.1%})")
    row("urgency right", lambda x: f"{x['urgency_right']}/300 ({x['urgency_accuracy']:.1%})")
    row("frustration right",
        lambda x: f"{x['frustration_right']}/300 ({x['frustration_accuracy']:.1%})")
    row("calls / failed / refusals",
        lambda x: f"{x['calls']} / {x['failed']} / {x['refusals']}")
    row("input tokens, all 300", lambda x: f"{x['input_tokens_total']:,}")
    row("cost, all 300", lambda x: f"${x['usd_total_300']:.6f}")
    row("cost per 1,000 tickets", lambda x: f"${x['usd_per_1000']:.4f}")
    row("300 tickets, 8 in flight", lambda x: f"{x['wall_seconds_300_8_in_flight']:.1f} s")
    row("per call p50 / p95, one at a time",
        lambda x: "{p50:.3f} / {p95:.3f} s".format(**x["per_call_seconds_one_at_a_time"]))
    row("per call p50 / p95, 8 in flight",
        lambda x: "{p50:.3f} / {p95:.3f} s".format(**x["per_call_seconds_8_in_flight"]))
    row("tokens per ticket (text + questions)",
        lambda x: f"{x['tokens_per_ticket_with_questions_mean']:.0f}")
    row("fixed tokens per call (questions + wrapping, fitted)",
        lambda x: f"{x['fixed_tokens_fitted']:.0f}")
    row("tokens for the ticket text alone (fitted)",
        lambda x: f"{x['ticket_text_tokens_mean']:.1f}")
    row("input tokens billed for the input \".\" with the same questions",
        lambda x: f"{x['input_dot_tokens']:.0f}")
    row("characters per text token", lambda x: f"{x['chars_per_text_token']:.2f}")
    row("batching (40 tickets): tokens per ticket, one call vs 3 calls",
        lambda x: "{tokens_one_call:.0f} vs {tokens_split:.0f}".format(**x["batching"]))
    row("output tokens reported, all 300 (not billed by either)",
        lambda x: f"{x['output_tokens_total']:,}")
    md += ["", "Team answers right, by the API's own confidence:", "",
           "| API | 0.9 or more | 0.7 to 0.9 | 0.5 to 0.7 | under 0.5 |", "|---|---|---|---|---|"]
    for a in apis:
        md.append(f"| {a} | " + " | ".join(f"{g['right']} of {g['answers']}"
                                           for g in s[a]["team_by_confidence"]) + " |")
    (RESULTS / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
