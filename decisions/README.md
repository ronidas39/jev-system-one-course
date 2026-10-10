# The OpenAI Decisions API, hands-on

This folder is Part C of the course: Parts 11 to 14. The web app for the final project is in `../app/`.

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
python 10_egg_grading.py          # 33 photos; choose two cut-offs on half, check them on the other half
python 10_ask_again.py            # the same photo three times: does the answer move?
python 10_speed_test.py           # ten photos: Decisions API against a JSON answer
python steps/desk_step1_one_photo.py    # refund desk, step 1: one photo, one question
python steps/desk_step2_add_message.py  # step 2: the customer's message and a second question
python steps/desk_step3_policy.py       # step 3: the shop's policy, in plain code
python steps/desk_step4_all_claims.py   # step 4: all eight claims
python steps/desk_step5_photo_alone.py  # step 5: ask about the photo on its own
python 11_returns_desk.py         # the whole refund desk in one file, with options
```

For `01_first_call.sh`, load `.env` into the terminal first: `set -a; source ../.env; set +a`.

## The egg photos and the labels

`eggs/` has 33 photos of single eggs. They are crops of CC0 and public domain photos from
Wikimedia Commons. `eggs/CREDITS.md` names every source and author.

`eggs/labels.csv` says if each egg is clean, dirty or cracked. **These are the course author's
labels, made by eye. They are drafts, not an expert's grades.** The lab uses them to show how to
pick cut-offs. `10_egg_grading.py` picks the cut-offs on every other photo and checks them on
the rest, the photos it did not use to pick them. With 33 photos and draft labels, that is a
demo, not a proof.

`results/reference/` holds the raw answers of an earlier run (9 October 2026), kept for reference.

## Two things the docs disagree on

- **Image links.** The guide says images must be inline base64 data URLs. The API reference says
  public HTTP(S) URLs work too. So this course always sends base64. Both pages accept that.
- **Speed.** OpenAI says the Decisions API is "about 10x faster than the Responses API". That is
  OpenAI's claim. `10_speed_test.py` times both on 10 egg photos from my laptop. It is a small
  test, not a proof of OpenAI's number.

## The lane race (Part 14): pictures, video clips, and text

`race/` is a small game. A seeded road has three lanes, with barriers and cones. At every step a
model answers one choice question: which lane should the car drive in? Our code drives into that
lane only when its probability is at or above a cut-off (0.80 by default). Below the cut-off, or on
a refusal, the car slows down and stays in its lane. In this game, slowing down never crashes. It
only costs time.

```bash
python race/make_clip.py                 # the race as a video, and frames cut out of it
python race/play.py --player text        # Decisions API, road as text
python race/play.py --player jev         # Jev, road as text (Jev reads text only)
python race/play.py --player picture     # Decisions API, one drawn picture per step
python race/play.py --player clip1       # Decisions API, one frame from the video
python race/play.py --player clip3       # Decisions API, the last three frames in one request
python race/compare.py                   # all your runs side by side
python race/compare.py --run reference   # the runs recorded for the course
```

Each run also writes a replay page (`results/race/<run>/<player>-seed7.html`). Open it in a
browser to watch the race with the three probability bars.

**Video.** The Decisions API takes text and images. It has no video input. A video is a stack of
pictures, so your code cuts out the frames it needs and sends them as images. `make_clip.py` and the
`clip` players do exactly that, with the ffmpeg program that comes with the `imageio-ffmpeg` package.

**Speed.** A call took about 0.2 seconds from my laptop in India. That is fine for a turn-based
game or a review queue. It is far too slow, and too unreliable, for a real car's control loop.
This is a toy, not a driving system.

## The web app (Part 16)

```bash
streamlit run app/app.py
```

Three tabs, one per question type: a predicate with one cut-off, a choice on an egg photo with
two cut-offs and a "send to a person" band, and a score with its level probabilities. The text tabs
can also ask Jev. Keys come from `.env`. Moving a slider never calls the API.
