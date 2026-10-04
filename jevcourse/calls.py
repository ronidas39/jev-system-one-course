"""One timed call to Jev or to an OpenAI model, with its cost.

Both sides are called the same way: a client made once and reused (so the
connection stays open), no automatic retries (a retry would hide a slow
call inside a fast-looking number), and a clock around the call only.

Author: Roni Das
Created: 2026-10-04
"""

import json
import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from openai import OpenAI
from typesafe_sdk import Question, RetryPolicy, TypeSafeClient

from jevcourse.config import require_key
from jevcourse.prices import jev_cost_usd, openai_cost_usd

JEV_MODEL = "jev-1.13.0"
"""Pinned, so a model update cannot change results in the middle of a comparison."""

LOWEST_REASONING_EFFORT = {"gpt-6-luna": "none", "gpt-6.1-sol": "low"}
"""The fastest setting each OpenAI model accepts. Sol does not accept "none"."""


@dataclass
class CallResult:
    """What came back from one call, in the same shape for every model."""

    model: str
    answer: dict[str, Any]
    seconds: float
    input_tokens: int
    output_tokens: int
    usd: float
    raw_usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Plain dictionary, ready for json.dumps."""
        return asdict(self)


def make_jev_client() -> TypeSafeClient:
    """A Jev client with retries switched off."""
    require_key("TYPESAFE_API_KEY")
    return TypeSafeClient(model=JEV_MODEL, retry=RetryPolicy(max_retries=0), timeout=60.0)


def make_openai_client() -> OpenAI:
    """An OpenAI client with retries switched off."""
    require_key("OPENAI_API_KEY")
    return OpenAI(max_retries=0, timeout=120.0)


def ask_jev(client: TypeSafeClient, state: Any, questions: dict[str, Question]) -> CallResult:
    """Send one state and its questions to Jev, and time it."""
    start = time.perf_counter()
    response = client.system_one(state=state, questions=questions)
    seconds = time.perf_counter() - start
    dumped = response.model_dump()
    tokens_in = response.usage.input_tokens or 0
    return CallResult(
        model=response.model,
        answer=dumped["answers"],
        seconds=seconds,
        input_tokens=tokens_in,
        output_tokens=response.usage.output_tokens or 0,
        usd=jev_cost_usd(tokens_in),
        raw_usage=dumped["usage"],
    )


def ask_openai(
    client: OpenAI, model: str, system: str, user: str, schema: dict[str, Any]
) -> CallResult:
    """Ask an OpenAI model for JSON that must match `schema`, and time it.

    Strict structured output means the reply always parses, so the OpenAI
    model is never marked wrong just because its text had the wrong shape.
    """
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_schema", "json_schema": schema},
        reasoning_effort=LOWEST_REASONING_EFFORT[model],
    )
    seconds = time.perf_counter() - start
    usage = response.usage.model_dump() if response.usage else {}
    return CallResult(
        model=model,
        answer=json.loads(response.choices[0].message.content or "{}"),
        seconds=seconds,
        input_tokens=int(usage.get("prompt_tokens") or 0),
        output_tokens=int(usage.get("completion_tokens") or 0),
        usd=openai_cost_usd(model, usage),
        raw_usage=usage,
    )


def percentile(values: list[float], pct: float) -> float:
    """The value below which `pct` percent of the values fall (nearest rank)."""
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    rank = max(1, math.ceil(pct / 100 * len(ordered)))
    return ordered[rank - 1]
