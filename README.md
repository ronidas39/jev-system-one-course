# Jev, the AI model that answers with numbers

The code for the freeCodeCamp course by Roni Das (systemdesign.academy, YouTube: Total Technology
Zonne). Everything shown in the course is here: the hands-on exercises, four small projects, one
big project, the fair comparison with OpenAI models, the synthetic data, and every raw result.

**Jev** is a model from TypeSafe AI. It does not write text. You send it some material (the
*state*) and some typed questions, and it sends back typed answers with probabilities:
yes or no (**Noul**), one option from a list (**Choice**), or a level on a scale (**Score**).

Only TypeSafe's own platform is used: https://console.typesafe.ai and https://docs.typesafe.ai.

---

## What you need

| | |
|---|---|
| Python | 3.10 or newer. Check with `python3 --version` (Windows: `py --version`) |
| git | to clone this repository. Check with `git --version` |
| An editor | the course uses VS Code |
| A TypeSafe API key | from https://console.typesafe.ai/keys |
| An OpenAI API key | only for the comparisons (`compare/`, use case 2, hands-on 12) |

Money: every run in the course cost me under one US dollar on Jev in total. The full comparison
(`compare/run_all.sh`) cost about 6 US dollars on OpenAI, almost all of it on the larger model.

---

## Set up, step by step

These are the exact commands, in order. Every one was run on a fresh clone before it was put
here on a Mac. On Windows, the lines marked differ. The Windows forms were not run by me, so if
one fails, the easiest path on Windows is **Git Bash** (it comes with Git for Windows): there, the
Mac commands below work, with two changes: type `py` where they say `python3`, and activate with
`source .venv/Scripts/activate`.

```bash
git clone https://github.com/ronidas39/jev-system-one-course.git
cd jev-system-one-course
python3 -m venv .venv               # Windows: py -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env               # Windows: copy .env.example .env
```

Now open `.env` in your editor and paste your keys after the `=` signs. `.env` is in
`.gitignore`, so git never commits it. Never paste a key into a `.py` file.

Check that it works:

```bash
cd handson
python 00_check_setup.py
python 01_first_call.py
cd ..
```

The first call with curl reads the key from your shell, so load `.env` into the shell first.
This step needs bash (Mac, Linux, or Git Bash on Windows). You can skip it: `01_first_call.py`
above makes the same call from Python.

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
| `handson/` | 13 short exercises, one idea each: first call, Noul, Choice, Score, many questions in one call, confidence, thresholds, pinned versions, errors, weak spots, a small inbox, a first comparison, a cheat sheet | 8, 9 |
| `usecases/` | four small projects: ticket triage, a guardrail on an LLM's draft reply, tool routing for an agent, a duplicate check on two records | 10 |
| `capstone/` | the big project: messy company records from three systems, cheap blocking, Jev decides each pair, a merge policy, a knowledge graph, and measurement against the truth | 10 |
| `compare/` | the fair comparison of Jev with gpt-6-luna and gpt-6.1-sol: accuracy, latency, cost, parallel and sequential timing, many questions in one call | 7 |
| `data/` | the seeded generators, the data they made, and `DATA-CARD.md` | 7, 10 |
| `tools/` | `choose_register.py`: Jev picks the diagram style for every slide in the course | 11 |
| `jevcourse/` | small shared helpers: prices, timed calls, the shared questions | all |

---

## Run the four small projects

```bash
python usecases/01_ticket_triage.py
python usecases/02_answer_guardrail.py
python usecases/03_tool_routing.py
python usecases/04_duplicate_check.py
```

## Run the big project

```bash
python data/make_companies.py
python capstone/step1_block.py
python capstone/step2_decide.py
python capstone/step3_graph.py
open capstone/out/graph_after.html        # Windows: start capstone\out\graph_after.html
```

The default data is the **training set**, where the question wording was tuned. To see how the
tuned wording does on records it never saw, run the **test set**:

```bash
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python capstone/step2_decide.py --pairs capstone/out/candidate_pairs-fresh.jsonl
python capstone/step3_graph.py --data companies-fresh --focus orchid
```

`step2_decide.py --model gpt-6-luna` runs the same decisions on an OpenAI model.
`step2_decide.py --wording v1` uses the first wording of the question, the one that sent too many
pairs to a person. Part 10 explains why the wording matters.

## Run the comparison

```bash
bash compare/run_all.sh            # about 50 minutes, about 6 US dollars
python compare/summarize.py        # tables in compare/results/summary.md, charts in compare/results/charts/
```

To check the comparison on a fresh dataset the wording was never tuned on:

```bash
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python compare/run_compare.py --task pairs-v1-fresh --protocol accuracy
python compare/run_compare.py --task pairs-v2-fresh --protocol accuracy
python compare/summarize.py
```

## Let Jev choose the diagram style for each slide

```bash
python tools/choose_register.py
```

---

## How the comparison is made fair

- Same inputs, same questions, same machine, same network, same evening.
- OpenAI models use **strict structured output**, so their answers always parse.
- Each OpenAI model runs at the **fastest reasoning setting it accepts** (`none` for gpt-6-luna,
  `low` for gpt-6.1-sol).
- **No automatic retries** on either side, so a slow call is never hidden.
- **Sequential timing:** 5 warm-up calls per model are thrown away, then 40 items, 3 rounds,
  models take turns item by item and the order rotates. Median and 90th percentile reported.
- **Parallel timing:** every item once, 8 calls in flight, wall clock for the whole batch.
- **Cost** is each response's own token counts times the published price
  (`jevcourse/prices.py`, read 4 October 2026, with the page addresses).
- **Accuracy** is checked against labels written by the data generator, not by another model.

Your numbers will differ. Time depends on where you are: I ran everything from Kolkata, India,
and TypeSafe says its service is on the West Coast of the USA.

---

## Results from my runs (4 and 5 October 2026)

Full tables: `compare/results/summary.md`. Every raw call: `compare/results/*.jsonl`.
0 failed calls in every run.

**Support tickets** (300 tickets, 8 calls in flight):

| model | team right | urgency right | frustration right | median s per call | 300 tickets | $ per 1,000 |
|---|---|---|---|---|---|---|
| jev-1.13.0 | 94.0% | 72.0% | 77.3% | 0.344 | 12.6 s | $0.0246 |
| gpt-6-luna | 98.0% | 80.3% | 95.3% | 1.325 | 50.1 s | $0.0517 |
| gpt-6.1-sol | 96.7% | 82.0% | 94.3% | 2.528 | 92.8 s | $1.0679 |

**Three questions in one call, or one call per question** (30 tickets; tokens are the average per ticket, seconds the median):

| model | input tokens, one call | input tokens, three calls | seconds, one call | seconds, three calls in a row |
|---|---|---|---|---|
| jev-1.13.0 | 584 | 1,186 | 0.399 | 0.994 |
| gpt-6-luna | 363 | 531 | 1.357 | 3.459 |
| gpt-6.1-sol | 363 | 531 | 2.985 | 6.431 |

A large chat model was a little more accurate on this job, so test on your own data before you
switch. That is why Jev returns a confidence number with every answer.

Every other run (the record pairs, both question wordings, the fresh test set) is in
`compare/results/summary.md`, with every raw call next to it.

---

## Safety

- Keys live only in `.env` or in your shell. The code reads them and never prints them.
- `.env` is in `.gitignore`. Check with `git check-ignore -v .env` before you commit.
- If a key ever reaches GitHub, delete it in the console at once and make a new one.

## Licence

MIT. See `LICENSE`.
