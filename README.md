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
(`compare/run_all.sh`) cost about 3 US dollars on OpenAI, almost all of it on the larger model.

---

## Set up, step by step

These are the exact commands, in order. Every one was run on a fresh clone before it was put
here. On Windows, the two lines marked differ.

```bash
git clone https://github.com/ronidas39/jev-system-one-course.git
cd jev-system-one-course
python3 -m venv .venv
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

The first call with curl reads the key from your shell, so load `.env` into the shell first:

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
| `tools/` | `choose_register.py`: Jev picks the diagram style for every slide in the course | 5, 10 |
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

`step2_decide.py --model gpt-6-luna` runs the same decisions on an OpenAI model.
`step2_decide.py --wording v1` uses the first wording of the question, the one that sent too many
pairs to a person. Part 10 explains why the wording matters.

## Run the comparison

```bash
bash compare/run_all.sh            # about 35 minutes, about 3 US dollars
python compare/summarize.py        # tables in compare/results/summary.md, charts in compare/results/charts/
```

To check the comparison on a fresh dataset the wording was never tuned on:

```bash
python data/make_companies.py --seed 20261007 --out companies-fresh
python capstone/step1_block.py --data companies-fresh
python compare/run_compare.py --task pairs-v2-fresh --protocol accuracy
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

## Results from my runs (4 October 2026)

See `compare/results/summary.md` for the full tables and `compare/results/*.jsonl` for every raw
call.

---

## Safety

- Keys live only in `.env` or in your shell. The code reads them and never prints them.
- `.env` is in `.gitignore`. Check with `git check-ignore -v .env` before you commit.
- If a key ever reaches GitHub, delete it in the console at once and make a new one.

## Licence

MIT. See `LICENSE`.
