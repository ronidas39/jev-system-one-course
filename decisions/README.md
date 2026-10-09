# The OpenAI Decisions API, hands-on

This folder is Part C of the course: Parts 11, 12 and 13.

The **Decisions API** is from OpenAI. Like Jev, it does not write text. You send some material and
typed questions. You get back a probability for every answer you allowed. It can also read photos.
It came out in public beta on 6 October 2026. The address is `POST /v1/decisions`. The only model
is `gpt-6-luna`.

Source: https://developers.openai.com/api/docs/guides/decisions (read 9 October 2026).

## What you need

- The course set up as in the main README. That gives you the `openai` SDK 3.26.1.
  The Decisions guide asks for 3.26.0 or newer.
- An OpenAI API key in `.env`, on the line `OPENAI_API_KEY=`. Your OpenAI account needs credit.
- Everything in this folder cost me less than 1 US cent per full run.

## Price

$0.10 per million input tokens. Output is not billed. Each script prints its cost. The cost
comes from the `usage` block in each answer, times that price.

## The scripts, in course order

Run them from this folder, with the virtual environment on:

```bash
cd decisions
python 00_check_setup.py          # SDK version, key present, model found. Free.
bash 01_first_call.sh             # first call with curl (bash only; needs the key in the terminal)
python 01_first_call_httpx.py     # the same call as plain HTTP, and the raw JSON
python 02_first_call_sdk.py       # the same call with the SDK
python 03_predicate.py            # yes or no: one probability
python 04_choice.py               # one option from a list, with confidence
python 05_score.py                # ordered levels, a score that can fall between levels
python 06_many_questions.py       # eight questions in one call, against eight calls
python 07_refusals_and_errors.py  # a real refusal, and two real errors
python 08_cost.py                 # cost from usage, on 20 course tickets
python 09_one_photo.py            # a photo as base64, three questions about one egg
python 10_egg_grading.py plan     # the egg lab: count the cost first
python 10_egg_grading.py classify # 33 photos, one call each
python 10_egg_grading.py sweep    # two cut-offs, and the "not sure" band for a person
python 11_returns_desk.py         # a refund desk: message plus photo, a written policy
python 11_returns_desk.py --separate
```

For `01_first_call.sh`, load `.env` into the terminal first: `set -a; source ../.env; set +a`.

## The egg photos and the labels

`eggs/` has 33 photos of single eggs. They are crops of CC0 and public domain photos from
Wikimedia Commons. `eggs/CREDITS.md` names every source and author.

`eggs/labels.csv` says if each egg is clean, dirty or cracked. **These are the course author's
labels, made by eye. They are drafts, not an expert's grades.** The lab uses them to show how to
pick cut-offs. The cut-offs are picked and checked on the same 33 photos. That is a demo, not a
proof. For real use, pick cut-offs on one set of labelled photos and check them on another.

`results/reference/` is the run recorded for the course (9 October 2026). Your own runs go to
`results/mine/`. You can compare the two.

## Two things the docs disagree on

- **Image links.** The guide says images must be inline base64 data URLs. The API reference says
  public HTTP(S) URLs work too. So this course always sends base64. Both pages accept that.
- **Speed.** OpenAI says the Decisions API is "about 10x faster than the Responses API". That is
  OpenAI's claim. Script 10 `compare` times both on 10 egg photos from my laptop. It is a small
  test, not a proof of OpenAI's number.
