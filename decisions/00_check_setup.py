"""Decisions 0: check the setup. Is the key there, is the SDK new enough, can we reach OpenAI?

This makes no paid call. It asks OpenAI for the model's details, which is free.
It never prints the key.

Author: Roni Das
Created: 2026-10-09
"""

import sys

import openai

from common import MODEL, check_key_present, make_client, show

NEEDED = (3, 26, 0)
"""The Decisions guide: "use these OpenAI SDK versions or later: Python 3.26.0"."""

check_key_present()
show("Python", sys.version.split()[0])
show("openai SDK", openai.__version__)
have = tuple(int(x) for x in openai.__version__.split(".")[:3])
if have < NEEDED:
    raise SystemExit("This SDK is too old for client.decisions. Run: pip install -r requirements.txt")

client = make_client()
show("client.decisions exists", hasattr(client, "decisions"))
model = client.models.retrieve(MODEL)
show("model found", model.id)
show("key", "set (not printed)")
