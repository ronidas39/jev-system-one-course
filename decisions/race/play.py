"""Drive the lane race with a model choosing the lane, one call per step.

Each step, the player sees the road ahead and answers one choice question:
lane 1, lane 2 or lane 3. Our code then decides:

  - the top lane's probability is at or above the cut-off -> drive into that lane
    (if that lane has a barrier or cone at 20 m, that is a crash)
  - below the cut-off, or a refusal                       -> slow down and stay
    (slowing down never crashes in this game, but it costs time)

Players (all on the same seeded road):
    picture   a picture of the road, drawn with Pillow, sent to the Decisions API
    clip1     one frame cut from a video clip of the drive, sent to the Decisions API
    clip3     the last three frames of the clip in one request, so motion is visible
    text      the road in words, sent to the Decisions API
    jev       the road in words, sent to Jev (Jev reads text only)

    python race/play.py --player picture
    python race/play.py --player jev --seed 7 --steps 60 --cutoff 0.8

Every step is saved to results/race/<run>/<player>-seed<seed>.jsonl, with a replay
page next to it that you can open in a browser.

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import base64
import io
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # decisions/common.py

from common import MODEL, check_key_present, cost_usd, image_data_url, log_call, make_client  # noqa: E402
from road import SUB, describe, draw, frames_from_clip, make_clip, make_road, blocked_at_20m  # noqa: E402

LANES = ["lane_1", "lane_2", "lane_3"]
INSTRUCTIONS = ("This shows the road ahead of our car, with distances. Which lane should the car "
                "drive in? Choose a lane with no barrier or cone at 20 metres, and if you can, "
                "none at 40 metres either.")
CHOICES = {"lane_1": "Lane 1, on the left.", "lane_2": "Lane 2, in the middle.",
           "lane_3": "Lane 3, on the right."}
LEGEND = ("Top-down view of a three-lane road. Our car is just below the picture, driving up. "
          "Orange striped boxes are barriers. Orange triangles are cones. The distance from our "
          "car is written on the left.")
QUESTION = {"type": "choice", "name": "lane", "instructions": INSTRUCTIONS,
            "choices": [{"value": k, "description": v} for k, v in CHOICES.items()]}


def png_url(img) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def ask_decisions(client, content: list[dict]) -> tuple[dict[str, float] | None, int, float]:
    """One Decisions call. Returns (lane probabilities or None if refused, tokens, seconds)."""
    start = time.perf_counter()
    d = client.decisions.create(model=MODEL, questions=[QUESTION],
                                input=[{"role": "user", "content": content}])
    seconds = time.perf_counter() - start
    log_call("race/play.py", d.usage.input_tokens, seconds, model=d.model)
    a = d.answers[0]
    probs = None if a.type == "refusal" else {str(p.value): p.probability for p in a.probabilities}
    return probs, d.usage.input_tokens, seconds


def ask_jev(client, text: str) -> tuple[dict[str, float], int, float, float]:
    from jevcourse.calls import ask_jev as jev_call
    from typesafe_sdk import Choice
    res = jev_call(client, text, {"lane": Choice(instructions=INSTRUCTIONS, criteria=CHOICES)})
    return dict(res.answer["lane"]["probabilities"]), res.input_tokens, res.seconds, res.usd


def bars(probs: dict[str, float] | None) -> str:
    if probs is None:
        return "REFUSED".ljust(54)
    return "  ".join(f"{k[-1]} {'█' * round(probs.get(k, 0) * 10):<10} {probs.get(k, 0):.2f}"
                     for k in LANES)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--player", required=True, choices=["picture", "clip1", "clip3", "text", "jev"])
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--cutoff", type=float, default=0.80)
    parser.add_argument("--run", default="mine")
    args = parser.parse_args()
    if args.steps > 100:
        sys.exit("at most 100 steps per run, so a race never costs more than a few cents")

    road = make_road(args.seed, args.steps)
    out = HERE.parent / "results" / "race" / args.run
    out.mkdir(parents=True, exist_ok=True)
    clip = out / f"clip-seed{args.seed}.mp4"
    if args.player.startswith("clip") and not clip.exists():
        make_clip(road, args.steps + 1, clip)
        print(f"made the clip {clip.relative_to(HERE.parent)} ({(args.steps + 1) * SUB} frames)")

    if args.player == "jev":
        from jevcourse.calls import make_jev_client
        client = make_jev_client()
    else:
        check_key_present()
        client = make_client()

    car, rows = 2, []
    print(f"{args.player}, seed {args.seed}, {args.steps} steps, cut-off {args.cutoff:.2f}")
    print(f"{'step':>4}  {'lane 1':<15}  {'lane 2':<15}  {'lane 3':<15}  {'action':<16} {'ms':>5}")
    for step in range(args.steps):
        if args.player == "picture":
            content = [{"type": "input_text", "text": LEGEND},
                       {"type": "input_image", "image_url": png_url(draw(road, step))}]
        elif args.player in ("clip1", "clip3"):
            last = step * SUB
            idx = [last] if args.player == "clip1" else sorted({max(0, last - 2), max(0, last - 1), last})
            paths = frames_from_clip(clip, idx, out / f"frames-seed{args.seed}")
            content = [{"type": "input_text", "text": LEGEND + f" These are {len(paths)} frame(s) "
                        "from a video of the drive, oldest first. The road moves toward the car."}]
            content += [{"type": "input_image", "image_url": image_data_url(p)} for p in paths]
        else:
            text = describe(road, step)
        if args.player == "jev":
            probs, tokens, seconds, usd = ask_jev(client, text)
        else:
            if args.player == "text":
                content = [{"type": "input_text", "text": text}]
            probs, tokens, seconds = ask_decisions(client, content)
            usd = cost_usd(tokens)
        blocked = blocked_at_20m(road, step)
        top = max(probs, key=probs.get) if probs else None
        if probs and probs[top] >= args.cutoff:
            lane = int(top[-1])
            action = "CRASH" if lane in blocked else f"drive lane {lane}"
            car = lane
        else:
            action = "slow down"
        rows.append({"step": step, "probs": probs, "action": action, "car_lane": car,
                     "blocked_20m": sorted(blocked), "tokens": tokens, "seconds": round(seconds, 4),
                     "usd": usd})
        print(f"{step:>4}  {bars(probs)}  {action:<16} {seconds * 1000:>5.0f}", flush=True)

    name = f"{args.player}-seed{args.seed}"
    meta = {"meta": True, "player": args.player, "seed": args.seed, "steps": args.steps,
            "cutoff": args.cutoff, "model": "jev-1.13.0" if args.player == "jev" else MODEL}
    (out / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [meta, *rows]))
    write_replay(road, rows, meta, out / f"{name}.html")
    crashes = sum(r["action"] == "CRASH" for r in rows)
    slow = sum(r["action"] == "slow down" for r in rows)
    ms = statistics.median(r["seconds"] for r in rows) * 1000
    tok = sum(r["tokens"] for r in rows)
    usd = sum(r["usd"] for r in rows)
    print(f"\n{args.player}: {crashes} crashes, {slow} slow-downs, "
          f"{len(rows) - crashes - slow} clean moves in {len(rows)} steps")
    print(f"median {ms:.0f} ms per call, {tok} input tokens, ${usd:.6f} "
          f"(${usd / len(rows) * 1000:.4f} per 1,000 steps)")
    print(f"replay: {(out / f'{name}.html').relative_to(HERE.parent)}")


def write_replay(road, rows: list[dict], meta: dict, path: Path) -> None:
    """A small page that plays the race back: the road with the car, and the three bars."""
    frames = []
    for r in rows:
        img = draw(road, r["step"], car_lane=r["car_lane"])
        frames.append({"img": png_url(img), "probs": r["probs"], "action": r["action"],
                       "ms": round(r["seconds"] * 1000)})
    path.write_text(REPLAY.replace("__TITLE__", f"{meta['player']}, seed {meta['seed']}, "
                                   f"cut-off {meta['cutoff']}")
                    .replace("__DATA__", json.dumps(frames)))


REPLAY = """<!doctype html><meta charset="utf-8"><title>Lane race replay</title>
<style>body{font:18px -apple-system,Segoe UI,sans-serif;background:#f6f5f1;color:#222;margin:24px}
.wrap{display:flex;gap:40px;align-items:center}.bar{height:18px;background:#2c2c2c;border-radius:9px}
.track{width:320px;background:#e3e1db;border-radius:9px}.row{display:flex;gap:14px;align-items:center;margin:14px 0}
.lab{width:64px}.num{font-family:Menlo,monospace;width:60px}#act{font-size:26px;font-weight:700;margin-top:18px}
#count{margin-top:8px;color:#555}</style>
<h2>Lane race replay: __TITLE__</h2>
<div class="wrap"><img id="road" width="340" height="400"><div>
<div class="row"><span class="lab">Lane 1</span><div class="track"><div class="bar" id="b1"></div></div><span class="num" id="n1"></span></div>
<div class="row"><span class="lab">Lane 2</span><div class="track"><div class="bar" id="b2"></div></div><span class="num" id="n2"></span></div>
<div class="row"><span class="lab">Lane 3</span><div class="track"><div class="bar" id="b3"></div></div><span class="num" id="n3"></span></div>
<div id="act"></div><div id="count"></div></div></div>
<script>const F=__DATA__;let i=0,crash=0,slow=0;
function show(){const f=F[i];document.getElementById('road').src=f.img;
for(const k of [1,2,3]){const p=f.probs?f.probs['lane_'+k]||0:0;
document.getElementById('b'+k).style.width=(p*320)+'px';document.getElementById('n'+k).textContent=f.probs?p.toFixed(2):'-';}
if(f.action==='CRASH')crash++;if(f.action==='slow down')slow++;
document.getElementById('act').textContent='step '+i+': '+f.action;
document.getElementById('count').textContent='crashes '+crash+' · slow-downs '+slow+' · '+f.ms+' ms';
i++;if(i<F.length)setTimeout(show,700);}show();</script>"""


if __name__ == "__main__":
    main()
