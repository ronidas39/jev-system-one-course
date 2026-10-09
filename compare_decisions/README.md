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

The Decisions API is called with plain HTTP through the OpenAI client (`client.post`). This file
was written when the course pinned `openai` 3.24.0, which had no `decisions` method. The course now
pins 3.26.1; `decisions/` uses `client.decisions.create`. Both send the same request.

Note on tokens: the input `"."` with the three questions billed 270 tokens on Decisions, but the
fitted fixed part on real tickets is about 466. So the per-ticket text tokens are fitted from all
300 tickets (tokens against characters), not taken from the `"."` call.

## Three runs on 9 October 2026

`results/runs/` keeps three accuracy and latency runs from the same day: 11:25, 12:02 (from a fresh
clone of this repo) and 12:06, India time. Accuracy and cost were the same every time. Decisions
speed was not: its 300-ticket batch took 7.7 s in the first run and 13.3 s and 13.4 s in the
other two (Jev: 12.5, 12.9 and 12.6 s). The files directly in `results/` are the first run.
