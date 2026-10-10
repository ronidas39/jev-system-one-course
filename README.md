# Decision AI Models: Complete Tutorial on TypeSafe Jev and the OpenAI Decisions API

The full course. Learn both from zero, then build real projects with them. For engineers.
Jev is TypeSafe's model, and the Decisions API is an API from OpenAI that runs on GPT-6 Luna.
Both answer with numbers, not with text.

This is the code for a course by Roni Das, made for the freeCodeCamp community. I teach at systemdesign.academy. My
YouTube channel is Total Technology Zonne.

Everything in the course is here:

- the hands-on scripts.
- four small projects.
- one big project: messy company records become a knowledge graph.
- a speed and cost test on support tickets.
- the OpenAI Decisions API, hands-on: `decisions/`. Text, photos, cut-offs, a refund desk, and a
  lane race that reads pictures, video frames and text.
- a working web app with Streamlit: `app/`. One tab per question type.
- the same 300 tickets on Jev and on the Decisions API: `compare_decisions/`.
- the made-up (synthetic) data.
- every raw result.

**Jev** is an AI model from TypeSafe AI. It does not write text. You send it some material. That
material is called the *state*. You also send typed questions. Jev sends back typed answers with
probabilities. A probability is a number from 0 to 1. It says how likely something is.

There are three kinds of question:

- **Noul**: yes or no.
- **Choice**: one option from a list.
- **Score**: a level on a scale.

This course uses only TypeSafe's own platform: https://console.typesafe.ai and
https://docs.typesafe.ai.

---

## What you need

| | |
|---|---|
| Python | 3.12 or newer (networkx 3.7 needs 3.12). I ran the course on 3.13, and checked a few scripts on 3.12. Check with `python3 --version` (Windows: `py --version`) |
| git | to copy (clone) this repository. Check with `git --version` |
| An editor | the course uses VS Code |
| A TypeSafe API key | from https://console.typesafe.ai/keys |
| An OpenAI API key | for Parts 11 to 16 (`decisions/`, `compare_decisions/`, `app/`), and for `compare/`, use case 2 and hands-on script 12. Your OpenAI account needs a little credit |

An API key is a secret password for a program. It lets your code use the service.

Money: everything I ran on Jev cost less than one US dollar in total. The full comparison
(`compare/run_all.sh`) cost about 5 US dollars on OpenAI. Almost all of that was the larger model.

---

## Set up, step by step

These are the exact commands, in order. I ran every one on a fresh copy, on a Mac.

On Windows, some lines differ. The comments show the Windows form. I did not run the Windows
forms myself. If one fails, use **Git Bash**. Git Bash comes with Git for Windows. In Git Bash the
Mac commands work, with two changes:

- type `py` where a command says `python3`.
- turn the environment on with `source .venv/Scripts/activate`.

```bash
git clone https://github.com/ronidas39/jev-system-one-course.git
cd jev-system-one-course
python3 -m venv .venv               # Windows: py -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env               # Windows: copy .env.example .env
```

Now open `.env` in your editor. Paste your keys after the `=` signs. `.env` is listed in
`.gitignore`. So git never saves it. Never paste a key into a `.py` file.

Check that it works:

```bash
cd handson
python 00_check_setup.py
python 01_first_call.py
cd ..
```

The next step makes the same first call with curl. It needs bash: Mac, Linux, or Git Bash on
Windows. You can skip it. `01_first_call.py` above already made the same call from Python. The
curl call reads the key from your terminal. So load `.env` into the terminal first:

```bash
cd handson
set -a; source ../.env; set +a
bash 01_first_call.sh
cd ..
```

---

## What is in here

| Folder | What it is | Course part |
|---|---|---|
| `handson/` | 14 short scripts, 00 to 13. One idea each: setup check, first call, Noul, Choice, Score, many questions in one call, confidence, thresholds, pinned versions, errors, asking well, a small inbox, a speed test, a short example file | 8, 9 |
| `usecases/` | four small projects: ticket triage, a check on a chat model's draft reply, tool choice for an AI agent, a duplicate check on two records | 10 |
| `capstone/` | the big project: messy company records, cheap blocking, Jev decides each pair, a merge rule, a knowledge graph, and a check against the truth | 10 |
| `compare/` | the speed and cost test of Jev, gpt-6-luna and gpt-6.1-sol on the same tickets. Every other run is here too, with accuracy | 7 |
| `decisions/` | the OpenAI Decisions API, hands-on: first call, the three question types, many questions, refusals, cost, photos of eggs, cut-offs, a refund desk, the lane race (`race/`) | 11 to 14 |
| `app/` | the final project: a Streamlit web app with one tab per question type | 16 |
| `compare_decisions/` | the same 300 tickets on Jev and on OpenAI's Decisions API (added 9 October 2026) | 15 |
| `data/` | the data makers, the data they made, and `DATA-CARD.md` | 7, 10 |
| `tools/` | `choose_register.py`: Jev picks the drawing style for every slide in the course | 15 |
| `jevcourse/` | small shared helpers: prices, timed calls, the shared questions | all |

---

## Run the four small projects

```bash
python usecases/01_ticket_triage.py
python usecases/02_answer_guardrail.py
python usecases/03_tool_routing.py
python usecases/04_duplicate_check.py
```

## Run the Decisions API part (Parts 11 to 14) and the web app (Part 16)

```bash
cd decisions
python 00_check_setup.py
python 02_first_call_sdk.py
python 10_egg_grading.py
python steps/desk_step4_all_claims.py
python steps/extra/desk_step5_photo_alone.py
python race/play.py --player text
python race/compare.py --run reference
cd ..
streamlit run app/app.py
```

The full list, in course order, is in `decisions/README.md`.

## Run the big project

```bash
python data/make_companies.py
python capstone/step1_block.py
python capstone/step2_decide.py
python capstone/step3_graph.py
open capstone/out/graph_after.html        # Windows: start capstone\out\graph_after.html
```

This first data is the **training set**. I tuned the wording of the question on it. The **test
set** is new data that the wording never saw. Run the test set like this:

```bash
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python capstone/step2_decide.py --data companies-fresh
python capstone/step3_graph.py --data companies-fresh --focus orchid
python capstone/show_review.py --data companies-fresh
```

`show_review.py` prints the pairs that wait for a person. It shows the highest and lowest scores.

- `step2_decide.py --model gpt-6-luna` runs the same decisions on an OpenAI model.
- `step2_decide.py --wording v1` uses my first wording of the question. That wording sent too many
  pairs to a person. Part 10 explains why.

## Run the comparison

```bash
bash compare/run_all.sh            # about 50 minutes, about 5 US dollars
python compare/summarize.py        # tables in compare/results/summary.md, charts in compare/results/charts/
```

To check the record pairs on the test set, with both wordings:

```bash
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python compare/run_compare.py --task pairs-v1-fresh --protocol accuracy
python compare/run_compare.py --task pairs-v2-fresh --protocol accuracy
python compare/summarize.py
```

## Let Jev choose the drawing style for each slide

```bash
python tools/choose_register.py
```

---

## How the test is kept fair

- Same inputs, same questions, same laptop, same network, same evening.
- OpenAI models use **strict structured output**. This setting forces a fixed answer shape. It is
  like a form with fixed boxes. So their answers always come in the right shape.
- Each OpenAI model uses its **fastest thinking setting**: `none` for gpt-6-luna, `low` for
  gpt-6.1-sol. (gpt-6.1-sol does not accept `none`.)
- **No automatic retries** on any side. A slow call is never hidden.
- **One call at a time:** 5 warm-up calls per model are not counted. Then 40 tickets, 3 rounds.
  The models take turns, and the order changes every round. I report the median, the middle
  time. I also report the 90th percentile: 9 in 10 calls were this fast or faster.
- **Many calls at once:** every ticket once, 8 calls at the same time. I time the whole batch.
- **Cost:** each answer's own token count times the published price. The prices are in
  `jevcourse/prices.py`. I read them on 4 October 2026.
- **Accuracy:** checked against the right answers that the data maker wrote. No model grades
  another model.

Your numbers will differ. Time depends on where you are. I ran everything from Kolkata, India.
TypeSafe says its service runs on the West Coast of the USA.

---

## Results from my runs (4 and 5 October 2026)

Full tables: `compare/results/summary.md`. Every raw call: `compare/results/*.jsonl`. No call
failed in any run.

**Support tickets** (300 tickets, 8 calls at a time):

| model | team right | urgency right | frustration right | median seconds per call | 300 tickets | $ per 1,000 |
|---|---|---|---|---|---|---|
| jev-1.13.0 | 96.7% | 72.3% | 75.7% | 0.344 | 13.5 s | $0.0246 |
| gpt-6-luna | 99.7% | 82.0% | 95.3% | 1.325 | 53.7 s | $0.0517 |
| gpt-6.1-sol | 99.7% | 80.7% | 93.3% | 2.528 | 91.6 s | $1.0566 |

The 300-ticket run was repeated on 5 October, after a labelling fix. See `CHANGELOG.md`.

**Three questions in one call, or one call per question.** 30 tickets. Tokens are the average
per ticket. Seconds are the median.

| model | input tokens, one call | input tokens, three calls | seconds, one call | seconds, three calls in a row |
|---|---|---|---|---|
| jev-1.13.0 | 584 | 1,186 | 0.399 | 0.994 |
| gpt-6-luna | 363 | 531 | 1.357 | 3.459 |
| gpt-6.1-sol | 363 | 531 | 2.985 | 6.431 |

On this job the chat models were more accurate. On the team question they got 299 of 300 right.
Jev got 290. They were clearly better on urgency and frustration. So test on your own data before you switch.
That is why Jev gives a confidence number with every answer.

Every other run is in `compare/results/summary.md`. That means the record pairs, both question
wordings, and the test set. Every raw call is next to it.

---

## Update, 9 October 2026: OpenAI's Decisions API

On 6 October 2026 OpenAI released the Decisions API in public beta: `POST /v1/decisions`,
model gpt-6-luna. It works like Jev. You send text (or images) and typed questions. You get
probabilities back, not written text. It bills input tokens only: $0.10 per million.
Source: https://developers.openai.com/api/docs/guides/decisions (read 9 October 2026).

The tables above were made before it existed. So I ran the same 300 tickets again, with the same
labels and the same three questions, on Jev and on the Decisions API. Code and every raw response:
`compare_decisions/`.

```bash
python compare_decisions/run_decisions.py --protocol baseline
python compare_decisions/run_decisions.py --protocol accuracy
python compare_decisions/run_decisions.py --protocol latency
python compare_decisions/run_decisions.py --protocol batching
python compare_decisions/summarize.py      # compare_decisions/results/summary.md
```

All four runs together cost about 3 US cents on OpenAI and about 1.3 US cents on Jev.

| | Decisions API (gpt-6-luna) | Jev (jev-1.13.0) |
|---|---|---|
| team right | 295 of 300 (98.3%), every run | 290 or 291 of 300 |
| urgency right | 79.7%, every run | 72.0% to 72.3% |
| frustration right | 79.7%, every run | 75.3% to 75.7% |
| failed calls, refusals (each run) | 0, 0 | 0, 0 |
| cost per 1,000 tickets | $0.0506 | $0.0246 |
| 300 tickets, 8 calls at a time | 7.7 s, then 13.3 s and 13.4 s | 12.5 s, 12.9 s, 12.6 s |
| one call at a time, median | 0.189, 0.389, 0.190 s | 0.323, 0.329, 0.324 s |
| input tokens per ticket | 506 | 585 |
| three questions in one call | yes | yes |

What this shows, in plain words:

- I ran it three times on 9 October: at 11:25, 12:02 (from a fresh clone) and 12:06, India time.
  The speed rows above show all three runs, in that order.
- Accuracy and cost came out the same every time. The Decisions API was more accurate: a little on team, clearly on urgency and frustration.
  Jev cost about half as much.
- Speed did not repeat. In the first run the Decisions API was faster on every speed measure. In
  the two later runs, Jev finished the 300 tickets first. I do not know why. The Decisions API is
  a public beta, and I measured from India. Measure speed at your own time and place.
- Both tokenizers read the ticket text at about the same rate: about 4.2 to 4.3 characters per
  token, about 40 tokens per ticket. Most tokens per call are the questions and each API's own
  wrapping (fitted: about 466 for Decisions, about 543 for Jev).
- So per ticket, Decisions cost 2.1 times Jev here. Per token the price gap is 2.4 times.
- Jev's scores move a little between runs. Your numbers will differ.

What each can do that the other cannot (from each vendor's docs, read 9 October 2026):

- **Images:** the Decisions API takes images, up to 128 per request. Jev takes text only.
- **Structured state:** Jev's state can be a JSON object, and questions can point at fields by
  name. Decisions takes a string or user messages with text and image parts.
- **Yes or no:** Jev's Noul returns one probability. Decisions' predicate does the same.
- **Confidence:** both return a probability for every option of a choice or score, and a
  confidence number. A Decisions predicate returns only the probability.
- **Refusals:** a Decisions answer can be a refusal for one question. Jev has no refusal type.
  Neither refused any ticket here.

---

## Safety

- Keys live only in `.env` or in your terminal. The code reads them. It never prints them.
- `.env` is listed in `.gitignore`. Check with `git check-ignore -v .env` before you commit.
- Did a key reach GitHub? Delete that key in the console at once. Then make a new one.

## Licence

MIT. See `LICENSE`.
