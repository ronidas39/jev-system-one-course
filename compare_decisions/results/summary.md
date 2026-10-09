# Jev against the OpenAI Decisions API: 300 support tickets

Computed by `compare_decisions/summarize.py` from the raw calls in this folder.

| measure | decisions/gpt-6-luna | jev-1.13.0 |
|---|---|---|
| team right | 295/300 (98.3%) | 290/300 (96.7%) |
| urgency right | 239/300 (79.7%) | 217/300 (72.3%) |
| frustration right | 239/300 (79.7%) | 226/300 (75.3%) |
| calls / failed / refusals | 300 / 0 / 0 | 300 / 0 / 0 |
| input tokens, all 300 | 151,847 | 175,412 |
| cost, all 300 | $0.015185 | $0.007367 |
| cost per 1,000 tickets | $0.0506 | $0.0246 |
| 300 tickets, 8 in flight | 7.7 s | 12.5 s |
| per call p50 / p95, one at a time | 0.189 / 0.233 s | 0.323 / 0.369 s |
| per call p50 / p95, 8 in flight | 0.192 / 0.265 s | 0.321 / 0.404 s |
| tokens per ticket (text + questions) | 506 | 585 |
| fixed tokens per call (questions + wrapping, fitted) | 466 | 543 |
| tokens for the ticket text alone (fitted) | 40.1 | 41.5 |
| input tokens billed for the input "." with the same questions | 270 | 543 |
| characters per text token | 4.33 | 4.19 |
| batching (40 tickets): tokens per ticket, one call vs 3 calls | 505 vs 594 | 583 vs 1184 |
| output tokens reported, all 300 (not billed by either) | 0 | 24,600 |

Team answers right, by the API's own confidence:

| API | 0.9 or more | 0.7 to 0.9 | 0.5 to 0.7 | under 0.5 |
|---|---|---|---|---|
| decisions/gpt-6-luna | 267 of 267 | 18 of 18 | 6 of 11 | 4 of 4 |
| jev-1.13.0 | 272 of 272 | 8 of 12 | 8 of 13 | 2 of 3 |
