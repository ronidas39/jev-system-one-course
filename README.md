# Decision AI Models: TypeSafe Jev and the OpenAI Decisions API

The source code for a freeCodeCamp course by Roni Das. The slides are in `slides/deck.pdf`.

## What you need

- Python 3.12 or newer. Check with `python3 --version` (Windows: `py --version`).
- git.
- A TypeSafe API key, from https://console.typesafe.ai/keys
- An OpenAI API key, from https://platform.openai.com/api-keys (needed for `decisions/`,
  `compare_decisions/`, `app/`, `compare/`, use case 2 and hands-on script 12).

## Set up

```bash
git clone https://github.com/ronidas39/jev-system-one-course.git
cd jev-system-one-course
python3 -m venv .venv               # Windows: py -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env               # Windows: copy .env.example .env
```

Open `.env` and paste your two keys after the `=` signs: `TYPESAFE_API_KEY` and
`OPENAI_API_KEY`. `.env` is in `.gitignore`, so git never saves it. Never paste a key into a
`.py` file.

## Run

Run from the repo root, except two folders that you run from inside:

- `handson/`: `cd handson`, then `python 00_check_setup.py`, `python 01_first_call.py`, and so on.
- `decisions/`: `cd decisions`, then `python 00_check_setup.py`, `python steps/desk_step1_one_photo.py`,
  `python race/play.py --player text`, and so on.

Everything else, from the repo root:

```bash
python usecases/01_ticket_triage.py
python data/make_companies.py
python capstone/step1_block.py
python capstone/step2_decide.py
python capstone/step3_graph.py
streamlit run app/app.py
```

Scripts that save results write them into `out/` or `results/` folders. Those folders are made
when you run the scripts.

## Folders

| Folder | What it is |
|---|---|
| `handson/` | short scripts, one idea each, numbered in course order |
| `usecases/` | four small projects, with step-by-step versions in `steps/` |
| `capstone/` | the big project: company records become a knowledge graph |
| `compare/` | speed, cost and accuracy test of Jev against OpenAI models (`run_all.sh`, then `summarize.py`) |
| `decisions/` | the OpenAI Decisions API: questions, egg photos, a refund desk, a lane race |
| `compare_decisions/` | the same 300 tickets on Jev and on the Decisions API |
| `app/` | a Streamlit web app, one tab per question type |
| `data/` | the scripts that make the synthetic data, and the data |
| `tools/` | `choose_register.py`: Jev picks a drawing style for each slide |
| `jevcourse/` | small shared helpers |
| `slides/` | the course slide deck |

## Licence

MIT. See `LICENSE`.
