"""The web app, step 2 of 4: the yes or no tab calls the Decisions API.

The message box from step 1 moves into a tab, and gets a question box, an Ask
button and a cut-off slider. Clicking Ask makes one real call. The answer is kept
in st.session_state, the page's memory between runs, so moving the slider only
runs the cut-off rule again and never calls the API.

Run it from the course folder:
    streamlit run app/steps/app_step2_yes_no_tab.py

Author: Roni Das
"""

import os
import time

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


[tab1] = st.tabs(["Predicate: yes or no"])

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
