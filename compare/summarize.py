"""Turn the saved raw calls into result tables and charts.

Reads compare/results/*.jsonl (written by run_compare.py) and writes:
  compare/results/summary.json   every number, for slides and for checking
  compare/results/summary.md     the tables, ready to read
  compare/results/charts/*.png   the charts

Nothing here calls an API. You can run it as often as you like.

    python compare/summarize.py

Author: Roni Das
Created: 2026-10-04
"""

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  the backend must be chosen before this import

from jevcourse.calls import percentile  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "compare/results"
CHARTS = RESULTS / "charts"
TRUTH_FILES = {"tickets": ROOT / "data/tickets.jsonl",
               "pairs": ROOT / "capstone/out/candidate_pairs.jsonl",
               "pairs-v2-fresh": ROOT / "capstone/out/candidate_pairs-fresh.jsonl"}
ROUTE_AT = 0.60
COLORS = {"jev-1.13.0": "#2a78d6", "gpt-6-luna": "#9a9a9a", "gpt-6.1-sol": "#eb6834"}


def load(name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The meta line and the call rows of one results file."""
    lines = [json.loads(x) for x in (RESULTS / f"{name}.jsonl").read_text().splitlines()]
    return lines[0], lines[1:]


def truth(task: str) -> dict[str, dict[str, Any]]:
    """The right answers, by item id."""
    key = "id" if task == "tickets" else "pair_id"
    rows = [json.loads(x) for x in TRUTH_FILES[task].read_text().splitlines()]
    return {r[key]: r for r in rows}


def cost_block(calls: list[dict[str, Any]]) -> dict[str, float]:
    """Tokens and dollars for a list of calls."""
    n = len(calls)
    usd = sum(c["usd"] for c in calls)
    return {"calls": n, "usd_total": usd, "usd_per_1000": usd / n * 1000 if n else 0.0,
            "input_tokens_mean": statistics.mean(c["input_tokens"] for c in calls),
            "output_tokens_mean": statistics.mean(c["output_tokens"] for c in calls)}


def ticket_accuracy(calls: list[dict[str, Any]], gold: dict[str, dict]) -> dict[str, Any]:
    """Team, urgency and frustration accuracy, plus the confidence-gated routing."""
    ok = [c for c in calls if c.get("common")]
    n = len(ok)
    team = sum(c["common"]["team"] == gold[c["item"]]["team"] for c in ok)
    auto = [c for c in ok if c["common"]["team_confidence"] >= ROUTE_AT]
    auto_right = sum(c["common"]["team"] == gold[c["item"]]["team"] for c in auto)
    return {
        "items": n, "team_right": team, "team_accuracy": team / n,
        "urgency_accuracy": sum(c["common"]["urgency"] == gold[c["item"]]["urgency"]
                                for c in ok) / n,
        "frustration_accuracy": sum(c["common"]["frustration"] == gold[c["item"]]["frustration"]
                                    for c in ok) / n,
        "auto_routed": len(auto), "auto_routed_share": len(auto) / n,
        "auto_routed_accuracy": auto_right / len(auto) if auto else None,
    }


def pair_accuracy(calls: list[dict[str, Any]], gold: dict[str, dict]) -> dict[str, Any]:
    """The three-way policy: merge, send to a person, keep separate."""
    ok = [c for c in calls if c.get("common")]
    true_same = sum(g["same_entity"] for g in gold.values())
    merged = [c for c in ok if c["common"]["link"] == 2]
    review = [c for c in ok if c["common"]["link"] == 1]
    separate = [c for c in ok if c["common"]["link"] == 0]
    merged_right = sum(gold[c["item"]]["same_entity"] for c in merged)
    separate_right = sum(not gold[c["item"]]["same_entity"] for c in separate)
    wrong_merges = [gold[c["item"]]["kind"] for c in merged if not gold[c["item"]]["same_entity"]]
    missed = sum(gold[c["item"]]["same_entity"] for c in separate)
    return {
        "items": len(ok), "true_duplicates": true_same,
        "merged": len(merged), "merge_precision": merged_right / len(merged) if merged else None,
        "merge_recall": merged_right / true_same,
        "wrong_merges": len(wrong_merges),
        "wrong_merges_by_kind": {k: wrong_merges.count(k) for k in sorted(set(wrong_merges))},
        "sent_to_person": len(review), "review_share": len(review) / len(ok),
        "review_that_were_duplicates": sum(gold[c["item"]]["same_entity"] for c in review),
        "kept_separate": len(separate),
        "separate_precision": separate_right / len(separate) if separate else None,
        "duplicates_wrongly_kept_separate": missed,
        "decided_automatically_right": (merged_right + separate_right) / len(ok),
    }


def threshold_sweep(calls: list[dict[str, Any]], gold: dict[str, dict]) -> list[dict]:
    """Merge only when the model's own certainty of 'same' is at least t."""
    true_same = sum(g["same_entity"] for g in gold.values())
    out = []
    for t in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
        merged = [c for c in calls if c.get("common") and c["common"]["p_same"] >= t]
        right = sum(gold[c["item"]]["same_entity"] for c in merged)
        out.append({"threshold": t, "merged": len(merged),
                    "precision": right / len(merged) if merged else None,
                    "recall": right / true_same})
    return out


def latency(calls: list[dict[str, Any]]) -> dict[str, float]:
    """Median and p90 seconds per call."""
    secs = [c["seconds"] for c in calls if "seconds" in c]
    return {"calls": len(secs), "median_s": statistics.median(secs),
            "p90_s": percentile(secs, 90), "min_s": min(secs), "max_s": max(secs)}


def summarize_task(task: str) -> dict[str, Any]:
    """Every number for one task, from its three result files."""
    gold = truth(task)
    out: dict[str, Any] = {"task": task, "models": {}}
    acc_meta, acc_rows = load(f"{task}-accuracy")
    has_timing = (RESULTS / f"{task}-latency.jsonl").exists()
    lat_meta, lat_rows = load(f"{task}-latency") if has_timing else ({}, [])
    bat_meta, bat_rows = load(f"{task}-batching") if has_timing else ({}, [])
    out["meta"] = {"accuracy": acc_meta, "latency": lat_meta, "batching": bat_meta}
    for model in acc_meta["models"]:
        calls = [r for r in acc_rows if r.get("model") == model and "item" in r]
        wall = next(r for r in acc_rows if r.get("model") == model and "batch_wall_seconds" in r)
        m: dict[str, Any] = {
            "failed_calls": sum("error" in c for c in calls),
            "parallel": {"workers": wall["workers"], "items": wall["items"],
                         "wall_seconds": wall["batch_wall_seconds"],
                         "items_per_second": wall["items"] / wall["batch_wall_seconds"]},
            "cost": cost_block([c for c in calls if "usd" in c]),
        }
        if has_timing:
            m["sequential"] = latency([r for r in lat_rows if r.get("model") == model])
        m["accuracy"] = (ticket_accuracy if task == "tickets" else pair_accuracy)(calls, gold)
        if task != "tickets":
            m["threshold_sweep"] = threshold_sweep(calls, gold)
        if not has_timing:
            out["models"][model] = m
            continue
        one = [r for r in bat_rows if r["model"] == model and r["mode"] == "one_call"]
        split = [r for r in bat_rows if r["model"] == model and r["mode"] == "one_call_per_question"]
        items = {r["item"] for r in one}
        per_item_split_s = [sum(r["seconds"] for r in split if r["item"] == i) for i in items]
        m["batching"] = {
            "items": len(items), "questions": len(split) // max(len(items), 1),
            "one_call_usd_per_item": sum(r["usd"] for r in one) / len(one),
            "split_usd_per_item": sum(r["usd"] for r in split) / len(items),
            "one_call_tokens_per_item": statistics.mean(r["input_tokens"] for r in one),
            "split_tokens_per_item": sum(r["input_tokens"] for r in split) / len(items),
            "one_call_median_s": statistics.median(r["seconds"] for r in one),
            "split_median_s_one_after_another": statistics.median(per_item_split_s),
        }
        out["models"][model] = m
    return out


def write_markdown(summary: dict[str, Any]) -> str:
    """The two comparison tables plus the batching table, as Markdown."""
    lines = []
    for task, s in summary["tasks"].items():
        lines.append(f"\n## {task}\n")
        if task == "tickets":
            lines.append("| model | team right | urgency right | frustration right | "
                         "median s | p90 s | 300 in parallel (8 at once) | $ per 1,000 |")
        else:
            lines.append("| model | merged | merge precision | merge recall | wrong merges | "
                         "sent to a person | median s | p90 s | 1,010 in parallel | $ per 1,000 |")
        lines.append("|" + "---|" * (8 if task == "tickets" else 10))
        for model, m in s["models"].items():
            a, p, c = m["accuracy"], m["parallel"], m["cost"]
            q = m.get("sequential", {"median_s": float("nan"), "p90_s": float("nan")})
            if task == "tickets":
                lines.append(f"| {model} | {a['team_accuracy']:.1%} | {a['urgency_accuracy']:.1%} "
                             f"| {a['frustration_accuracy']:.1%} | {q['median_s']:.3f} | "
                             f"{q['p90_s']:.3f} | {p['wall_seconds']:.1f} s | "
                             f"${c['usd_per_1000']:.4f} |")
            else:
                lines.append(f"| {model} | {a['merged']} | {a['merge_precision']:.1%} | "
                             f"{a['merge_recall']:.1%} | {a['wrong_merges']} | "
                             f"{a['sent_to_person']} | {q['median_s']:.3f} | {q['p90_s']:.3f} | "
                             f"{p['wall_seconds']:.1f} s | ${c['usd_per_1000']:.4f} |")
        if "batching" not in next(iter(s["models"].values())):
            continue
        lines.append("\nAll questions in one call, against one call per question:\n")
        lines.append("| model | tokens, one call | tokens, split | $ one call | $ split | "
                     "median s one call | median s split |")
        lines.append("|---|---|---|---|---|---|---|")
        for model, m in s["models"].items():
            b = m["batching"]
            lines.append(f"| {model} | {b['one_call_tokens_per_item']:.0f} | "
                         f"{b['split_tokens_per_item']:.0f} | ${b['one_call_usd_per_item']:.7f} | "
                         f"${b['split_usd_per_item']:.7f} | {b['one_call_median_s']:.3f} | "
                         f"{b['split_median_s_one_after_another']:.3f} |")
    return "# Jev against OpenAI models: results\n" + "\n".join(lines) + "\n"


def bar_chart(summary: dict[str, Any], task: str, value: str, label: str, fname: str) -> None:
    """One simple bar per model."""
    models = list(summary["tasks"][task]["models"])
    vals = [summary["tasks"][task]["models"][m][value.split(".")[0]][value.split(".")[1]]
            for m in models]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.bar(models, vals, color=[COLORS.get(m, "#555") for m in models])
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.3g}", ha="center", va="bottom")
    ax.set_ylabel(label)
    ax.set_title(f"{task}: {label}", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS / fname, dpi=150)
    plt.close(fig)


def main() -> None:
    """Write summary.json, summary.md and the charts."""
    tasks = [t for t in ("tickets", "pairs", "pairs-v2-fresh")
             if (RESULTS / f"{t}-accuracy.jsonl").exists()]
    summary = {"tasks": {t: summarize_task(t) for t in tasks}}
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    (RESULTS / "summary.md").write_text(write_markdown(summary))
    CHARTS.mkdir(exist_ok=True)
    for t in [t for t in tasks if "sequential" in next(iter(summary["tasks"][t]["models"].values()))]:
        bar_chart(summary, t, "sequential.median_s", "median seconds per call",
                  f"{t}-median-latency.png")
        bar_chart(summary, t, "cost.usd_per_1000", "US dollars per 1,000 items",
                  f"{t}-cost-per-1000.png")
    print((RESULTS / "summary.md").read_text())


if __name__ == "__main__":
    main()
