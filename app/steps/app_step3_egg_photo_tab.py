"""The web app, step 3 of 4: add the Choice tab, an egg photo with two cut-offs.

The new tab sends one egg photo with an egg question, and draws one bar per
option. "Not clean" is 1 minus the probability of clean. Below the left handle
the egg is sold, above the right handle it is thrown away, and in the band between
the two handles a person looks at it.

Run it from the course folder:
    streamlit run app/steps/app_step3_egg_photo_tab.py

Author: Roni Das
"""

import base64
import os
import time
from pathlib import Path

import streamlit as st
from openai import OpenAI

# Read the OpenAI key from the .env file in the course folder.
for line in open(".env"):
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()

st.set_page_config(page_title="Decisions API: three question types", layout="wide")
st.title("Decisions API: three question types")

# ---------------------------------------------------------------------------
# Step 1: one call to the Decisions API, with its time and cost
# ---------------------------------------------------------------------------
@st.cache_resource
def openai_client():
    return OpenAI(max_retries=0, timeout=60.0)       # made once, reused on every rerun


def ask(message, question):
    start = time.perf_counter()
    decision = openai_client().decisions.create(model="gpt-6-luna", input=message,
                                                questions=[question])
    milliseconds = (time.perf_counter() - start) * 1000
    tokens = decision.usage.input_tokens
    return {"answer": decision.answers[0].model_dump(), "milliseconds": milliseconds,
            "tokens": tokens, "cost": tokens * 0.10 / 1_000_000, "model": decision.model}


def show_time_and_cost(result):
    st.caption(f"{result['model']} · {result['milliseconds']:.0f} ms · {result['tokens']} input "
               f"tokens · ${result['cost']:.8f} (from the usage in this answer)")


def show_bars(probabilities):
    for label, probability in probabilities.items():
        name_column, bar_column, number_column = st.columns([2, 6, 1])
        name_column.write(label)
        bar_column.progress(min(probability, 1.0))
        number_column.write(f"{probability:.2f}")


tab1, tab2 = st.tabs(["Predicate: yes or no", "Choice: one of a list"])

# ---------------------------------------------------------------------------
# Step 2: the yes or no tab, with a cut-off slider
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Predicate: one probability that the statement is true")
    message = st.text_area("Message", "I have asked three times now. Can I please just talk to a "
                           "real person?", key="p_text")
    question = st.text_input("Question", "Is the customer asking for a human agent?", key="p_q")
    if st.button("Ask", key="p_go"):
        st.session_state["yes_no"] = ask(message, {"type": "predicate", "name": "answer",
                                                   "instructions": question})
    cutoff = st.slider("Act when the probability is at least", 0.0, 1.0, 0.80, 0.05, key="p_cut")
    result = st.session_state.get("yes_no")
    if result:
        yes = result["answer"]["probability"]
        show_bars({"yes": yes})
        verdict = "ACT" if yes >= cutoff else "DO NOT ACT"
        st.markdown(f"**{verdict}**: {yes:.2f} against the cut-off {cutoff:.2f}")
        show_time_and_cost(result)

# ---------------------------------------------------------------------------
# Step 3: the egg photo tab, with two cut-offs
# ---------------------------------------------------------------------------
EGG_QUESTION = {
    "type": "choice", "name": "condition",
    "instructions": "What is the condition of the egg shell in this photo?",
    "choices": [
        {"value": "clean", "description": "Shell is intact with no dirt, stains or droppings."},
        {"value": "dirty", "description": "Shell is intact but has dirt, stains or droppings."},
        {"value": "cracked", "description": "Shell has a crack, hole, or is broken open."},
        {"value": "unclear", "description": "The photo does not show the shell well enough."},
    ],
}

with tab2:
    st.subheader("Choice: an egg photo, one bar per option, two cut-offs")
    photo_names = sorted(path.stem for path in Path("decisions/eggs").glob("*.jpg"))
    photo_name = st.selectbox("Egg photo (CC0 and public domain, see decisions/eggs/CREDITS.md)",
                              photo_names, index=photo_names.index("tray-06"), key="c_pick")
    photo = open(f"decisions/eggs/{photo_name}.jpg", "rb").read()
    st.image(photo, width=220)
    photo_as_text = "data:image/jpeg;base64," + base64.b64encode(photo).decode("ascii")
    if st.button("Ask", key="c_go"):
        st.session_state["egg"] = ask([{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": photo_as_text}]}], EGG_QUESTION)
        st.session_state["egg_name"] = photo_name
    low, high = st.slider("Chance the egg is NOT clean. Sell below the left handle, throw away above the right one:",
                          0.0, 1.0, (0.30, 0.70), 0.05, key="c_cut")
    result = st.session_state.get("egg")
    if result:
        st.caption(f"Answer for: {st.session_state['egg_name']}")
        probabilities = {x["value"]: x["probability"] for x in result["answer"]["probabilities"]}
        show_bars(probabilities)
        not_clean = 1.0 - probabilities["clean"]
        if not_clean < low:
            verdict = "SELL"
        elif not_clean > high:
            verdict = "THROW AWAY"
        else:
            verdict = "A PERSON CHECKS"
        st.markdown(f"**{verdict}**: chance it is not clean {not_clean:.2f}. Sell below {low:.2f}, "
                    f"throw away above {high:.2f}, a person checks anything in between.")
        show_time_and_cost(result)
