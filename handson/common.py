"""Small helpers shared by every hands-on script in the Jev study book.

The API key is read from the TYPESAFE_API_KEY environment variable by the
SDK itself. It is never printed, never written to a file, never logged.
Cost uses TypeSafe's published price for jev-1.13.0: $0.042 per million
input tokens, output tokens free (docs.typesafe.ai/models, read 2026-10-04).

Author: Roni Das
Created: 2026-10-04
"""

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PRICE_PER_MILLION_INPUT_TOKENS_USD = 0.042
"""TypeSafe's published Jev 1.13 price. Output tokens are free."""

SPEND_LOG_ENV = "JEV_SPEND_LOG"
"""If this environment variable names a file, every call's cost is appended there."""


def check_key_present() -> None:
    """Stop early with a friendly message when the key is missing. Never prints the key.

    Keys in the repository's .env file are loaded first, so you can use either the
    .env file or an exported environment variable.
    """
    try:
        from jevcourse.config import load_env_file
        load_env_file()
    except ImportError:
        pass  # jevcourse is not installed; exported variables still work
    if not os.environ.get("TYPESAFE_API_KEY", "").strip():
        raise SystemExit(
            "TYPESAFE_API_KEY is not set. Put your key in an environment variable first "
            "(see the README). Never paste the key into the code."
        )


def cost_usd(input_tokens: int | None) -> float:
    """Price of one call in US dollars from its input token count."""
    return (input_tokens or 0) * PRICE_PER_MILLION_INPUT_TOKENS_USD / 1_000_000


def timed(func: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Run func and return (result, wall-clock seconds) measured on this machine."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    return result, time.perf_counter() - start


def log_call(script: str, model: str, input_tokens: int | None, output_tokens: int | None,
             seconds: float, note: str = "", provider: str = "typesafe",
             usd: float | None = None) -> None:
    """Append one call's cost to the spend log named by JEV_SPEND_LOG, if set."""
    path = os.environ.get(SPEND_LOG_ENV)
    if not path:
        return
    log_file = Path(path)
    rows: list[dict[str, Any]] = json.loads(log_file.read_text()) if log_file.exists() else []
    rows.append({
        "time_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "script": script,
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "seconds": round(seconds, 3),
        "usd": round(cost_usd(input_tokens) if usd is None else usd, 8),
        "note": note,
    })
    log_file.write_text(json.dumps(rows, indent=1))


def show(label: str, value: Any) -> None:
    """Print one labelled line, so outputs are easy to read in the book."""
    print(f"{label:<28} {value}")
