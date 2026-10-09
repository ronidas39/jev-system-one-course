# Jev and the OpenAI Decisions API on the same 300 tickets

Same tickets (`data/tickets.jsonl`), same labels, same three questions as `compare/`.
The Decisions API questions are built from `jevcourse/tasks.py`, word for word.

- `run_decisions.py`: four protocols (baseline, accuracy, latency, batching). Hard stop at 1,200
  calls per run. Every raw response is saved in `results/<protocol>.jsonl`.
- `summarize.py`: `results/summary.md` and `results/summary.json`, computed from the raw files.

Prices, read 9 October 2026:

- Jev: $0.042 per million input tokens, output free. https://docs.typesafe.ai/models
- Decisions API, gpt-6-luna: $0.10 per million input tokens, no output charge.
  https://developers.openai.com/api/docs/guides/decisions

The Decisions API was called with plain HTTP through the OpenAI client (`client.post`), because
the pinned `openai` 3.24.0 has no `decisions` method yet (the guide asks for Python SDK 3.26.0).

Note on tokens: the input `"."` with the three questions billed 270 tokens on Decisions, but the
fitted fixed part on real tickets is about 466. So the per-ticket text tokens are fitted from all
300 tickets (tokens against characters), not taken from the `"."` call.
