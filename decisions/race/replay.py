"""Write a replay page for one saved race, to open in a browser.

Reads results/race/mine/<player>-seed7.jsonl (written by the race step files)
and writes <player>-seed7.html next to it: the road with our car, and the
three lane bars, one step at a time.

Run it from the decisions folder:
    python race/replay.py picture
    python race/replay.py clip1

Author: Roni Das
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from play import write_replay  # noqa: E402
from road import make_road  # noqa: E402

player = sys.argv[1] if len(sys.argv) > 1 else "picture"
folder = HERE.parent / "results" / "race" / "mine"
meta, *rows = [json.loads(line) for line in open(folder / f"{player}-seed7.jsonl")]
page = folder / f"{player}-seed7.html"
write_replay(make_road(meta["seed"], meta["steps"]), rows, meta, page)
print(f"replay: {page.relative_to(HERE.parent)} ({len(rows)} steps)")
