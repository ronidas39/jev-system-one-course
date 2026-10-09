"""Small helpers shared by every script in the decisions/ folder.

The OpenAI key is read from the OPENAI_API_KEY environment variable, or from
the repository's .env file. It is never printed, never written to a file and
never logged.

Price: OpenAI's Decisions API guide, read 9 October 2026:
"With gpt-6-luna, input costs $0.10 per 1M tokens. You pay only for input
tokens: there are no cache-read, cache-write, or output-token charges."
https://developers.openai.com/api/docs/guides/decisions#pricing-and-availability

Author: Roni Das
Created: 2026-10-09
"""

import base64
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MODEL = "gpt-6-luna"
"""The only model the Decisions API accepts while it is in beta."""

USD_PER_MILLION_INPUT_TOKENS = 0.10
"""Decisions API price for gpt-6-luna, read 9 October 2026. Output is not billed."""

PRICE_READ_ON = "2026-10-09"
REPO_ROOT = Path(__file__).resolve().parents[1]
SPEND_LOG_ENV = "JEV_SPEND_LOG"
"""If this environment variable names a file, every call's cost is added to it."""


def check_key_present() -> None:
    """Stop early, with a short message, when the OpenAI key is missing."""
    try:
        from jevcourse.config import load_env_file
        load_env_file()
    except ImportError:
        pass  # jevcourse is not installed; an exported variable still works
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit(
            "OPENAI_API_KEY is not set. Put your key in the .env file (see the README). "
            "Never paste the key into the code."
        )


def make_client() -> Any:
    """An OpenAI client with retries off, so every time we print is one real call."""
    from openai import OpenAI
    return OpenAI(max_retries=0, timeout=60.0)


def cost_usd(input_tokens: int | None) -> float:
    """Price of one call in US dollars. Only input tokens are billed."""
    return (input_tokens or 0) * USD_PER_MILLION_INPUT_TOKENS / 1_000_000


def ask(client: Any, input: Any, questions: list[dict[str, Any]],
        script: str = "", note: str = "") -> tuple[Any, float]:
    """One call to POST /v1/decisions. Returns (decision, seconds on this machine)."""
    start = time.perf_counter()
    decision = client.decisions.create(model=MODEL, input=input, questions=questions)
    seconds = time.perf_counter() - start
    log_call(script, decision.usage.input_tokens, seconds, note)
    return decision, seconds


def by_name(decision: Any) -> dict[str, Any]:
    """The answers, keyed by the name we gave each question."""
    return {answer.name: answer for answer in decision.answers}


def odds(answer: Any) -> dict[str, float]:
    """For a choice or score answer: each option and its probability."""
    out: dict[str, float] = {}
    for p in answer.probabilities:
        key = getattr(p, "label", None) or str(p.value)
        out[key] = p.probability
    return out


def image_data_url(path: Path) -> str:
    """A photo as an inline base64 data URL.

    The guide says: "Images must be inline base64 data URLs." The API reference
    also mentions public HTTP(S) URLs. The two pages disagree, so this course
    always sends base64, which both pages accept.
    """
    kind = "png" if path.suffix.lower() == ".png" else "jpeg"
    return f"data:image/{kind};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def log_call(script: str, input_tokens: int | None, seconds: float, note: str = "",
             provider: str = "openai-decisions", output_tokens: int = 0,
             usd: float | None = None) -> None:
    """Add one call's cost to the spend log named by JEV_SPEND_LOG, if it is set."""
    path = os.environ.get(SPEND_LOG_ENV)
    if not path:
        return
    log_file = Path(path)
    rows: list[dict[str, Any]] = json.loads(log_file.read_text()) if log_file.exists() else []
    rows.append({
        "time_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": script,
        "provider": provider,
        "model": MODEL,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "seconds": round(seconds, 3),
        "usd": round(cost_usd(input_tokens) if usd is None else usd, 8),
        "note": note,
    })
    log_file.write_text(json.dumps(rows, indent=1))


def show(label: str, value: Any) -> None:
    """Print one labelled line, so the outputs are easy to read."""
    print(f"{label:<28} {value}")
