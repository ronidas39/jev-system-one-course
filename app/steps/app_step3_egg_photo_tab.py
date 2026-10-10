"""The web app, step 3 of 5: add the Choice tab, an egg photo with two cut-offs.

The new tab sends one egg photo with an egg question, and draws one bar per
option. "Not clean" is 1 minus the probability of clean. Below the left handle
the egg passes, above the right handle it is rejected, and in the band between
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


def ask_decisions(input, question):
    start = time.perf_counter()
    d = openai_client().decisions.create(model="gpt-6-luna", input=input, questions=[question])
    ms = (time.perf_counter() - start) * 1000
    tokens = d.usage.input_tokens
    return {"answer": d.answers[0].model_dump(), "ms": ms, "tokens": tokens,
            "usd": tokens * 0.10 / 1_000_000, "model": d.model}


def footer(r):
    st.caption(f"{r['model']} · {r['ms']:.0f} ms · {r['tokens']} input tokens · "
               f"${r['usd']:.8f} (from the usage in this answer)")


def bars(probs):
    for label, p in probs.items():
        a, b, c = st.columns([2, 6, 1])
        a.write(label)
        b.progress(min(p, 1.0))
        c.write(f"{p:.2f}")


tab1, tab2 = st.tabs(["Predicate: yes or no", "Choice: one of a list"])

# ---------------------------------------------------------------------------
# Step 2: the yes or no tab, with a cut-off slider
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Predicate: one probability that the statement is true")
    text = st.text_area("Message", "I have asked three times now. Can I please just talk to a "
                        "real person?", key="p_text")
    instr = st.text_input("Question", "Is the customer asking for a human agent?", key="p_q")
    if st.button("Ask", key="p_go"):
        st.session_state["p"] = ask_decisions(text, {"type": "predicate", "name": "answer",
                                                     "instructions": instr})
    cut = st.slider("Act when the probability is at least", 0.0, 1.0, 0.80, 0.05, key="p_cut")
    r = st.session_state.get("p")
    if r:
        p = r["answer"]["probability"]
        bars({"yes": p})
        st.markdown(f"**{'ACT' if p >= cut else 'DO NOT ACT'}**: {p:.2f} against the cut-off {cut:.2f}")
        footer(r)

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
    names = sorted(p.stem for p in Path("decisions/eggs").glob("*.jpg"))
    pick = st.selectbox("Egg photo (CC0 and public domain, see decisions/eggs/CREDITS.md)", names,
                        index=names.index("tray-06"), key="c_pick")
    upload = st.file_uploader("Or upload your own JPEG or PNG (it is sent to OpenAI when you click Ask)",
                              type=["jpg", "jpeg", "png"], key="c_up")
    photo = upload.getvalue() if upload else open(f"decisions/eggs/{pick}.jpg", "rb").read()
    kind = "png" if upload and upload.name.lower().endswith(".png") else "jpeg"
    url = f"data:image/{kind};base64," + base64.b64encode(photo).decode("ascii")
    st.image(photo, width=220)
    if st.button("Ask", key="c_go"):
        st.session_state["c"] = ask_decisions([{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url}]}], EGG_QUESTION)
        st.session_state["c_src"] = upload.name if upload else pick
    low, high = st.slider("Not clean = 1 - P(clean). Pass below the left handle, reject above the right:",
                          0.0, 1.0, (0.30, 0.70), 0.05, key="c_cut")
    r = st.session_state.get("c")
    if r:
        st.caption(f"Answer for: {st.session_state['c_src']}")
        probs = {x["value"]: x["probability"] for x in r["answer"]["probabilities"]}
        bars(probs)
        not_clean = 1.0 - probs["clean"]
        verdict = ("PASS" if not_clean < low else "REJECT" if not_clean > high
                   else "SEND TO A PERSON")
        st.markdown(f"**{verdict}**: not clean {not_clean:.2f}. Pass below {low:.2f}, "
                    f"reject above {high:.2f}, a person checks the band in between.")
        footer(r)
