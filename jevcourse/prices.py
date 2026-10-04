"""Published prices used to turn token counts into US dollars.

Every price here was read from the vendor's own page on 4 October 2026.
Prices change. Check both pages again before you trust a cost number.

  TypeSafe: https://docs.typesafe.ai/models
  OpenAI:   https://developers.openai.com/api/docs/pricing  (Standard tier, short context)

Author: Roni Das
Created: 2026-10-04
"""

from dataclasses import dataclass

PRICES_READ_ON = "2026-10-04"

JEV_INPUT_USD_PER_MILLION = 0.042
"""Jev charges for input tokens only. Output tokens are free."""


@dataclass(frozen=True)
class OpenAIPrice:
    """US dollars per one million tokens for one OpenAI model."""

    input: float
    cached_input: float
    cache_write: float
    output: float


OPENAI_PRICES: dict[str, OpenAIPrice] = {
    "gpt-6-luna": OpenAIPrice(input=0.10, cached_input=0.01, cache_write=0.125, output=0.50),
    "gpt-6.1-sol": OpenAIPrice(input=2.00, cached_input=0.10, cache_write=2.50, output=10.00),
}


def jev_cost_usd(input_tokens: int | None) -> float:
    """Cost of one Jev call from its input token count."""
    return (input_tokens or 0) * JEV_INPUT_USD_PER_MILLION / 1_000_000


def openai_cost_usd(model: str, usage: dict[str, object]) -> float:
    """Cost of one OpenAI call from the usage block the API sent back.

    Cached tokens and cache-write tokens have their own prices, so they are
    taken out of the normal input count before it is priced.
    """
    price = OPENAI_PRICES[model]
    details = usage.get("prompt_tokens_details") or {}
    assert isinstance(details, dict)
    prompt = int(usage.get("prompt_tokens") or 0)
    cached = int(details.get("cached_tokens") or 0)
    written = int(details.get("cache_write_tokens") or 0)
    plain = max(prompt - cached - written, 0)
    output = int(usage.get("completion_tokens") or 0)
    dollars = (
        plain * price.input
        + cached * price.cached_input
        + written * price.cache_write
        + output * price.output
    )
    return dollars / 1_000_000
