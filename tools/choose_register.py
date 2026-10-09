"""Ask Jev which diagram style (register) fits each slide, then check its pick against our rules.

For every slide in slides.json, Jev gets the slide's plain-words brief as the
state and one Choice question whose options are the registers in
registers.json, each described by what it is, what it is for and what it is
not for.

Then plain code checks the pick, and overrides it when:
  1. the pick cannot be drawn in this deck (for example an interactive diagram
     in a still image),
  2. the pick breaks a content-shape rule (for example measured numbers must
     be a chart), or
  3. Jev's confidence is low, so the rules decide instead.
When it overrides, it takes the allowed register Jev itself gave the highest
probability, so Jev's ranking is still used. Two slides in a row in the same
drawn style are also changed, because a deck in one style looks generated.

Every pick, confidence, probability and override is saved to
tools/register_choices.json, with the reason in plain words.

    python tools/choose_register.py
    python tools/choose_register.py --only p01-cold-open,p07-verdict   # re-ask a few, keep the rest

Author: Roni Das
Created: 2026-10-04
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from typesafe_sdk import Choice

from jevcourse.calls import ask_jev, make_jev_client

HERE = Path(__file__).resolve().parent
LOW_CONFIDENCE = 0.30
"""Below this, Jev is not sure enough to decide alone."""
REAL_CAPTURES = {"real_screenshot", "real_terminal_capture"}
"""Real captures may repeat. Everything else must change from one slide to the next."""


def allowed_for(shapes: list[str], rules: dict[str, list[str]]) -> list[str]:
    """Registers that serve every shape on the slide, or any of them if none serves all."""
    sets = [set(rules[s]) for s in shapes if s in rules]
    if not sets:
        return []
    common = set.intersection(*sets)
    return sorted(common or set.union(*sets))


KITS = ["jev", "combined"]
"""The two decks built from slides.json: the Jev-only course and the combined course."""


def kits_of(slide: dict[str, Any]) -> list[str]:
    """The decks a slide belongs to. No "kits" field means both."""
    return slide.get("kits", KITS)


def best_allowed(probabilities: dict[str, float], allowed: list[str], avoid: str = "") -> str:
    """The allowed register Jev rated highest, skipping `avoid`."""
    ranked = sorted(probabilities, key=probabilities.get, reverse=True)  # type: ignore[arg-type]
    for name in ranked:
        if name in allowed and name != avoid:
            return name
    return allowed[0]


def main() -> None:
    """Ask Jev about every slide, apply the checks, save and print the log."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", default="",
                        help="comma-separated slide ids to ask about again; every other slide "
                             "keeps its saved decision")
    args = parser.parse_args()
    reg = json.loads((HERE / "registers.json").read_text())
    all_slides = json.loads((HERE / "slides.json").read_text())["slides"]
    only = {x for x in args.only.split(",") if x}
    saved = {}
    if only and (HERE / "register_choices.json").exists():
        saved = {r["id"]: r for r in json.loads((HERE / "register_choices.json").read_text())}
    slides = [sl for sl in all_slides if not only or sl["id"] in only or sl["id"] not in saved]
    available = set(reg["available_in_this_deck"])
    rules = {k: v for k, v in reg["shape_rules"].items() if not k.startswith("_")}
    question = {"register": Choice(
        instructions="Which diagram style best explains the content of this slide in a video "
                     "course? Pick the style that matches what the slide must show.",
        criteria={name: {k: v for k, v in r.items()} for name, r in reg["registers"].items()})}

    def ask(slide: dict[str, Any]) -> dict[str, Any]:
        with make_jev_client() as client:
            state = {"slide_title": slide["title"], "what_the_slide_must_show": slide["brief"]}
            result = ask_jev(client, state, question)
        return {"answer": result.answer["register"], "seconds": result.seconds,
                "usd": result.usd, "input_tokens": result.input_tokens}

    with ThreadPoolExecutor(max_workers=6) as pool:
        answers = list(pool.map(ask, slides))

    asked = {sl["id"]: got for sl, got in zip(slides, answers, strict=True)}
    log: list[dict[str, Any]] = []
    last_in_kit: dict[str, str] = {}
    for i, slide in enumerate(all_slides):
        kits = kits_of(slide)
        if slide["id"] not in asked:
            log.append(saved[slide["id"]])
            for kit in kits:
                last_in_kit[kit] = saved[slide["id"]]["final"]
            continue
        got = asked[slide["id"]]
        # Neighbours are judged inside each deck (kit) the slide belongs to.
        before = {last_in_kit.get(kit, "") for kit in kits}
        previous = next(iter(before - {""}), "")
        nxt = next((s["id"] for s in all_slides[i + 1:] if set(kits_of(s)) & set(kits)), "")
        following = saved[nxt]["final"] if nxt in saved and nxt not in asked else ""
        pick, conf = got["answer"]["choice"], got["answer"]["confidence"]
        probs = got["answer"]["probabilities"]
        allowed = [r for r in allowed_for(slide["shapes"], rules) if r in available]
        final, reasons = pick, []
        if pick not in available:
            final = best_allowed(probs, allowed)
            reasons.append(f"'{pick}' cannot be drawn in a still slide")
        elif pick not in allowed:
            final = best_allowed(probs, allowed)
            reasons.append(f"'{pick}' breaks the rule for {', '.join(slide['shapes'])}")
        elif conf < LOW_CONFIDENCE:
            reasons.append(f"confidence {conf:.2f} is low; the rules allow '{pick}', so it stays")
        if final in before and final not in REAL_CAPTURES and len(allowed) > 1:
            changed = best_allowed(probs, allowed, avoid=final)
            reasons.append(f"'{final}' was used on the slide before, so '{changed}' instead")
            final = changed
        if final == following and final not in REAL_CAPTURES and len(allowed) > 1:
            changed = best_allowed(probs, allowed, avoid=final)
            if changed != previous:
                reasons.append(f"'{final}' is used on the slide after, so '{changed}' instead")
                final = changed
        for kit in kits:
            last_in_kit[kit] = final
        log.append({"id": slide["id"], "part": slide["part"], "title": slide["title"],
                    "jev_pick": pick, "confidence": conf,
                    "top3": sorted(probs.items(), key=lambda kv: -kv[1])[:3],
                    "allowed_by_rules": allowed, "final": final,
                    "overridden": final != pick, "reasons": reasons,
                    "seconds": round(got["seconds"], 3), "usd": got["usd"]})

    (HERE / "register_choices.json").write_text(json.dumps(log, indent=1))
    kept = sum(not r["overridden"] for r in log)
    for r in (x for x in log if not only or x["id"] in asked):
        flag = "KEPT    " if not r["overridden"] else "OVERRIDE"
        print(f"{r['id']:<26} Jev: {r['jev_pick']:<22} {r['confidence']:.2f}  {flag} -> "
              f"{r['final']:<22} {'; '.join(r['reasons'])}")
    usd = sum(r["usd"] for r in log if r["id"] in asked)
    print(f"\n{len(log)} slides. Jev's pick kept on {kept}, overridden on {len(log) - kept}. "
          f"Asked now: {len(asked)}, cost ${usd:.5f}.")


if __name__ == "__main__":
    main()
