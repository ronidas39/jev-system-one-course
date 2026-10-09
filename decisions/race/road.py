"""The lane race: a seeded road, drawn as pictures, as a video clip, and as text.

The road has three lanes. Every 20 metres there is a row. A row can hold a barrier
or a cone in up to two lanes, never all three. The same seed always makes the
same road, so every player drives the same race.

Three ways to show the road ahead, so different models can play:
  - frame(): a picture, drawn with Pillow (for the Decisions API, which reads images).
  - make_clip(): a short video of the drive, written with ffmpeg.
  - describe(): plain text (for Jev, which reads text only).

Author: Roni Das
Created: 2026-10-09
"""

import random
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LANES = 3
ROW_M = 20
"""Metres between two rows of the road."""
SEE_ROWS = 3
"""The picture shows the next 3 rows: 20, 40 and 60 metres ahead."""
SUB = 4
"""Video frames between two rows, so the clip shows the road moving."""
W, H = 340, 400
MARGIN = 44
"""Space on the left for the distance labels."""
TOP, BOTTOM = 40, 360
"""The road ahead runs from y=TOP (60 m) down to y=BOTTOM (our car's bumper)."""
KINDS = ["barrier", "cone"]


@dataclass
class Road:
    seed: int
    rows: list[dict[int, str]]
    """rows[r] maps a lane (1 to 3) to an obstacle kind. Row 0 is where the car starts."""


def make_road(seed: int, steps: int) -> Road:
    """A seeded road: about half the rows hold one obstacle, about a third hold two."""
    rng = random.Random(seed)
    rows: list[dict[int, str]] = [{}]
    for _ in range(steps + SEE_ROWS + 1):
        n = rng.choices([0, 1, 2], weights=[2, 5, 3])[0]
        lanes = rng.sample(range(1, LANES + 1), n)
        rows.append({lane: rng.choice(KINDS) for lane in lanes})
    return Road(seed, rows)


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("Arial.ttf", "DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _y(distance_m: float) -> float:
    """Screen y for a distance ahead of the car (0 m at the bottom, 60 m at the top)."""
    return BOTTOM - (BOTTOM - TOP) * distance_m / (ROW_M * SEE_ROWS)


def draw(road: Road, step: int, sub: int = 0, car_lane: int | None = None) -> Image.Image:
    """The road ahead at row `step`, `sub` video frames after it. Optionally the car."""
    img = Image.new("RGB", (W, H), (236, 236, 232))
    d = ImageDraw.Draw(img)
    lane_w = (W - MARGIN) / LANES
    small = _font(16)
    for lane in range(1, LANES + 1):
        d.text((MARGIN + (lane - 0.5) * lane_w, 14), str(lane), fill=(90, 90, 90), font=small, anchor="mm")
    for i in range(1, LANES):
        x = MARGIN + i * lane_w
        y = TOP
        while y < H:
            d.line([(x, y), (x, y + 14)], fill=(160, 160, 160), width=2)
            y += 28
    shift = sub / SUB
    for r in range(step + 1, step + SEE_ROWS + 2):
        dist = (r - step - shift) * ROW_M
        if not 0 < dist <= ROW_M * SEE_ROWS:
            continue
        y = _y(dist)
        for lane, kind in road.rows[r].items():
            cx = MARGIN + (lane - 0.5) * lane_w
            if kind == "barrier":
                d.rectangle([cx - 38, y - 9, cx + 38, y + 9], fill=(240, 170, 60),
                            outline=(120, 70, 20), width=2)
                for k in range(-32, 28, 14):
                    d.line([(cx + k, y + 9), (cx + k + 10, y - 9)], fill=(60, 50, 40), width=4)
            else:
                d.polygon([(cx, y - 18), (cx - 14, y + 12), (cx + 14, y + 12)],
                          fill=(245, 120, 30), outline=(120, 60, 10))
                d.line([(cx - 8, y), (cx + 8, y)], fill=(255, 255, 255), width=3)
    for dist in (20, 40, 60):
        d.text((4, _y(dist)), f"{dist} m", fill=(110, 110, 110), font=_font(14), anchor="lm")
    if car_lane is not None:
        cx = MARGIN + (car_lane - 0.5) * lane_w
        d.rounded_rectangle([cx - 16, BOTTOM - 4, cx + 16, BOTTOM + 34], radius=8,
                            fill=(110, 150, 230), outline=(40, 70, 140), width=2)
    return img


def describe(road: Road, step: int) -> str:
    """The same road ahead, in words, for a model that reads text only."""
    parts = []
    for lane in range(1, LANES + 1):
        seen = [f"{road.rows[step + k].get(lane)} at {k * ROW_M} m"
                for k in range(1, SEE_ROWS + 1) if road.rows[step + k].get(lane)]
        parts.append(f"Lane {lane}: {', '.join(seen) if seen else 'clear'}.")
    return "Road ahead of our car, next 60 metres. " + " ".join(parts)


def blocked_at_20m(road: Road, step: int) -> set[int]:
    """Lanes with something in the very next row. Driving into one is a crash."""
    return set(road.rows[step + 1])


def ffmpeg() -> str:
    """The ffmpeg program that comes with the imageio-ffmpeg package (no separate install)."""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def make_clip(road: Road, steps: int, out: Path, fps: int = 8) -> Path:
    """Write the drive as an MP4: SUB frames per row, the road scrolling toward the car."""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / f"_frames_{road.seed}"
    tmp.mkdir(exist_ok=True)
    n = 0
    for step in range(steps):
        for sub in range(SUB):
            draw(road, step, sub).save(tmp / f"f{n:05d}.png")
            n += 1
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", str(tmp / "f%05d.png"), "-pix_fmt", "yuv420p", "-c:v", "libx264",
                    str(out)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    return out


def frames_from_clip(clip: Path, indexes: list[int], out_dir: Path) -> list[Path]:
    """Pull single frames out of the video with ffmpeg, by frame number."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in indexes:
        p = out_dir / f"frame_{i:05d}.jpg"
        if not p.exists():
            subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", str(clip),
                            "-vf", f"select=eq(n\\,{i})", "-frames:v", "1", "-q:v", "3", str(p)],
                           check=True)
        paths.append(p)
    return paths
