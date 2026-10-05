# Jev against OpenAI models: results

## tickets

| model | team right | urgency right | frustration right | median s | p90 s | 300 in parallel (8 at once) | $ per 1,000 |
|---|---|---|---|---|---|---|---|
| jev-1.13.0 | 94.0% | 72.0% | 77.3% | 0.344 | 0.403 | 12.6 s | $0.0246 |
| gpt-6-luna | 98.0% | 80.3% | 95.3% | 1.325 | 1.756 | 50.1 s | $0.0517 |
| gpt-6.1-sol | 96.7% | 82.0% | 94.3% | 2.528 | 3.362 | 92.8 s | $1.0679 |

Team answers right, by the model's own confidence (Jev: from its probabilities; OpenAI: the number the model writes):

| model | 0.9 or more | 0.7 to 0.9 | 0.5 to 0.7 | under 0.5 |
|---|---|---|---|---|
| jev-1.13.0 | 261 of 265 | 10 of 14 | 8 of 14 | 3 of 7 |
| gpt-6-luna | 276 of 276 | 18 of 22 | 0 of 2 | 0 of 0 |
| gpt-6.1-sol | 278 of 279 | 12 of 20 | 0 of 1 | 0 of 0 |

All questions in one call, against one call per question:

| model | tokens, one call | tokens, split | $ one call | $ split | median s one call | median s split |
|---|---|---|---|---|---|---|
| jev-1.13.0 | 584 | 1186 | $0.0000245 | $0.0000498 | 0.399 | 0.994 |
| gpt-6-luna | 363 | 531 | $0.0000516 | $0.0000801 | 1.357 | 3.459 |
| gpt-6.1-sol | 363 | 531 | $0.0010726 | $0.0017518 | 2.985 | 6.431 |

## pairs

| model | merged | merge precision | merge recall | wrong merges | sent to a person | median s | p90 s | 1,010 in parallel | $ per 1,000 |
|---|---|---|---|---|---|---|---|---|---|
| jev-1.13.0 | 324 | 100.0% | 68.5% | 0 | 159 | 0.348 | 0.430 | 42.3 s | $0.0308 |
| gpt-6-luna | 465 | 100.0% | 98.3% | 0 | 8 | 1.223 | 1.560 | 160.1 s | $0.0618 |
| gpt-6.1-sol | 470 | 100.0% | 99.4% | 0 | 3 | 2.177 | 2.790 | 271.6 s | $1.2548 |

All questions in one call, against one call per question:

| model | tokens, one call | tokens, split | $ one call | $ split | median s one call | median s split |
|---|---|---|---|---|---|---|
| jev-1.13.0 | 731 | 1814 | $0.0000307 | $0.0000762 | 0.373 | 1.010 |
| gpt-6-luna | 467 | 977 | $0.0000617 | $0.0001232 | 1.083 | 3.133 |
| gpt-6.1-sol | 467 | 977 | $0.0012844 | $0.0024972 | 2.194 | 6.694 |

## pairs-v1-fresh

| model | merged | merge precision | merge recall | wrong merges | sent to a person | median s | p90 s | 1,014 in parallel | $ per 1,000 |
|---|---|---|---|---|---|---|---|---|---|
| jev-1.13.0 | 313 | 100.0% | 67.6% | 0 | 156 | not timed | not timed | 41.5 s | $0.0309 |
| gpt-6-luna | 458 | 100.0% | 98.9% | 0 | 6 | not timed | not timed | 154.5 s | $0.0620 |
| gpt-6.1-sol | 463 | 100.0% | 100.0% | 0 | 0 | not timed | not timed | 324.8 s | $1.2674 |

## pairs-v2-fresh

| model | merged | merge precision | merge recall | wrong merges | sent to a person | median s | p90 s | 1,014 in parallel | $ per 1,000 |
|---|---|---|---|---|---|---|---|---|---|
| jev-1.13.0 | 443 | 100.0% | 95.7% | 0 | 28 | not timed | not timed | 41.8 s | $0.0331 |
| gpt-6-luna | 427 | 100.0% | 92.2% | 0 | 40 | not timed | not timed | 146.2 s | $0.0672 |
| gpt-6.1-sol | 462 | 100.0% | 99.8% | 0 | 1 | not timed | not timed | 323.0 s | $1.3628 |
