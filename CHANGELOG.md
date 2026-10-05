# Changelog

## 5 October 2026: ticket labels fixed

**What was wrong.** `data/make_tickets.py` had one urgency phrase that named a problem:
"This looks like someone is in my account at this moment." That is an account security problem.
The ticket prompt says the account team handles security. But the phrase was added at random to
tickets of every team. It appeared in 15 tickets. In 13 of them the label was billing, technical,
shipping or sales. So a model that followed the prompt was marked wrong.

These 15 tickets held many of the misses:

| model | team misses (old run) | misses on those 15 tickets |
|---|---|---|
| jev-1.13.0 | 18 | 10 |
| gpt-6-luna | 6 | 6 |
| gpt-6.1-sol | 10 | 9 |

**What changed.** The phrase is now "Nothing works for us until this is fixed." It sits in the
same place in the list. So the same seed makes the same 300 tickets. Only those 15 texts changed.
No label changed.

**What was run again.** The 300-ticket accuracy run, for all three models, 8 calls at a time.
That run also gives the batch time and the cost.

| model | team right, before | team right, now | 300 tickets, before | now | $ per 1,000, before | now |
|---|---|---|---|---|---|---|
| jev-1.13.0 | 94.0% | 96.7% | 12.6 s | 13.5 s | $0.0246 | $0.0246 |
| gpt-6-luna | 98.0% | 99.7% | 50.1 s | 53.7 s | $0.0517 | $0.0517 |
| gpt-6.1-sol | 96.7% | 99.7% | 92.8 s | 91.6 s | $1.0679 | $1.0566 |

**What was not run again.** The one-at-a-time timing (40 tickets) and the one-call-or-three test
(30 tickets). They measure seconds and tokens, not labels. Two of those 40 tickets and one of the
30 still had the old phrase when they were measured. A re-run was started, but the OpenAI account
ran out of credit part way. So the earlier, complete files are kept.
