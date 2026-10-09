"""Make the race video, then cut frames out of it: the clip-to-frames step, on its own.

The Decisions API reads text and images. It has no video input. So a video is
handled as what it is: a stack of pictures (frames). Your code picks the frames
it needs at the moment a decision is needed, and sends them as images.

    python race/make_clip.py                  # seed 7, the clip the race uses
    python race/make_clip.py --step 10        # also cut the frames for step 10

Author: Roni Das
Created: 2026-10-09
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from road import SUB, ffmpeg, frames_from_clip, make_clip, make_road  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--seed", type=int, default=7)
parser.add_argument("--steps", type=int, default=60)
parser.add_argument("--step", type=int, default=10)
parser.add_argument("--run", default="mine")
args = parser.parse_args()

out = HERE.parent / "results" / "race" / args.run
clip = out / f"clip-seed{args.seed}.mp4"
if not clip.exists():
    make_clip(make_road(args.seed, args.steps + 1), args.steps + 1, clip)
info = subprocess.run([ffmpeg(), "-i", str(clip)], capture_output=True, text=True).stderr
stream = next(line.strip() for line in info.splitlines() if "Video:" in line)
print(f"clip: {clip.relative_to(HERE.parent)}, {clip.stat().st_size:,} bytes")
print(f"  {stream[:110]}")
print(f"  {(args.steps + 1) * SUB} frames, {SUB} frames per 20 metres of road")
last = args.step * SUB
one = frames_from_clip(clip, [last], out / f"frames-seed{args.seed}")
three = frames_from_clip(clip, [last - 2, last - 1, last], out / f"frames-seed{args.seed}")
print(f"\nstep {args.step}, 1 frame:  {[p.name for p in one]}")
print(f"step {args.step}, 3 frames: {[p.name for p in three]}")
print("each frame goes into the request as one input_image, oldest first")
