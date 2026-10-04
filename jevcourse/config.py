"""Read the two API keys from the environment, or from a local .env file.

The keys are never printed, never logged and never written anywhere.
If a key is missing, the scripts stop with a short message that says what to do.

Author: Roni Das
Created: 2026-10-04
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"


def load_env_file() -> None:
    """Copy KEY=value lines from .env into the environment, without overwriting.

    A value you exported in the terminal always wins over the file.
    """
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value and not os.environ.get(name.strip()):
            os.environ[name.strip()] = value


def require_key(name: str) -> None:
    """Stop early, with a friendly message, when a key is missing."""
    load_env_file()
    if not os.environ.get(name, "").strip():
        raise SystemExit(
            f"{name} is not set. Copy .env.example to .env and put your key there, "
            f"or run: export {name}=your-key"
        )
