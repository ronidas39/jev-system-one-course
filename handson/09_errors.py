"""Exercise 9: what errors look like, and how to handle them.

Each case is sent on purpose to show a real error. Nothing here is faked.
The SDK retries 408, 429 and 5xx errors by itself (2 retries by default).

Author: Roni Das
Created: 2026-10-04
"""

import os

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAuthenticationError,
    TypeSafeClient,
    TypeSafeError,
    TypeSafeRateLimitError,
)

from common import check_key_present

check_key_present()
Q = {"x": Noul(instructions="Is this about billing?")}

print("1) No key at all")
saved = os.environ.pop("TYPESAFE_API_KEY")
try:
    TypeSafeClient()
except TypeSafeError as error:
    print(f"   {type(error).__name__}: {error}")
os.environ["TYPESAFE_API_KEY"] = saved

print("2) A wrong key")
try:
    with TypeSafeClient(api_key="ts-this-is-not-a-real-key") as bad:
        bad.system_one(state="I was charged twice.", questions=Q)
except TypeSafeAuthenticationError as error:
    print(f"   {type(error).__name__}: status {error.status}: {error}")

with TypeSafeClient() as client:
    print("3) A Score with 11 levels (the API accepts up to 10)")
    try:
        client.system_one(state="test", questions={
            "s": Score(instructions="How big?", criteria=[f"level {i}" for i in range(11)])})
        print("   no error was raised")
    except TypeSafeAPIError as error:
        print(f"   {type(error).__name__}: status {error.status}: {error}")

    print("4) A Choice with 256 options (the API accepts up to 255)")
    try:
        client.system_one(state="test", questions={
            "c": Choice(instructions="Which one?",
                        criteria={f"option_{i}": None for i in range(256)})})
        print("   no error was raised")
    except TypeSafeAPIError as error:
        print(f"   {type(error).__name__}: status {error.status}: {error}")

    print("5) No questions at all (the SDK stops this before sending)")
    try:
        client.system_one(state="test", questions={})
    except TypeSafeError as error:
        print(f"   {type(error).__name__}: {error}")

    print("6) A timeout that is far too short, with retries turned off")
    try:
        client.system_one(state="I was charged twice.", questions=Q, timeout=0.001,
                          retry=RetryPolicy(max_retries=0))
    except TypeSafeAPIConnectionError as error:
        print(f"   {type(error).__name__}: {error}")

print("7) The shape of a safe call in production")


def safe_ask(client: TypeSafeClient, state: str) -> float | None:
    """Return the noul, or None when the call failed and a person must look."""
    try:
        return client.system_one(state=state, questions=Q).answers["x"].noul
    except TypeSafeRateLimitError as error:
        # The SDK already retried. Slow down, queue the work, try later.
        print(f"   rate limited, server asked to wait {error.retry_after_ms} ms")
    except TypeSafeAPIError as error:
        print(f"   API error {error.status}, request id {error.request_id}")
    except TypeSafeAPIConnectionError as error:
        print(f"   network problem: {error}")
    return None


with TypeSafeClient(retry=RetryPolicy(max_retries=3, backoff_max=5.0)) as client:
    print(f"   safe_ask returned {safe_ask(client, 'I was charged twice. Please refund one.')}")
