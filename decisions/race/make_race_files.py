"""Make the ready-made lane race files once: road pictures, the video clip, its frames, road.json.

The step files in steps/ only load these files and ask the API, so they stay
short. This helper is run once, off camera, and its output is saved in the repo
in decisions/race_images/. Same seed, same road, every time.

Run it from the decisions folder:
    python race/make_race_files.py

Author: Roni Das
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from road import SUB, blocked_at_20m, describe, draw, ffmpeg, make_clip, make_road  # noqa: E402

SEED, STEPS = 7, 60
out = HERE.parent / "race_images"
if out.exists():
    shutil.rmtree(out)
(out / "frames").mkdir(parents=True)

road = make_road(SEED, STEPS)

# Step 1: one picture of the road ahead for every step
for step in range(STEPS):
    draw(road, step).save(out / f"step_{step:02d}.png")

# Step 2: the drive as a short video clip, then every frame of it as a JPEG
clip = make_clip(road, STEPS + 1, out / "clip.mp4")
subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(clip), "-q:v", "3",
                "-start_number", "0", str(out / "frames" / "frame_%05d.jpg")], check=True)

# Step 3: road.json, what is really on the road at each step
steps = [{"step": s, "picture": f"step_{s:02d}.png", "frame": s * SUB,
          "blocked_20m": sorted(blocked_at_20m(road, s)), "text": describe(road, s)}
         for s in range(STEPS)]
json.dump({"seed": SEED, "frames_per_step": SUB, "steps": steps},
          open(out / "road.json", "w"), indent=1)

frames = len(list((out / "frames").glob("*.jpg")))
print(f"{STEPS} pictures, clip.mp4 with {frames} frames, road.json -> {out.relative_to(HERE.parent)}")
