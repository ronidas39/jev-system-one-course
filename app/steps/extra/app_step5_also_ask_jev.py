"""The web app, step 5 of 5: the optional "also ask Jev" box.

The yes or no tab and the score tab each get a tick box. When it is ticked, Ask
also sends the same text and the same question to Jev, TypeSafe's model, and its
answer is drawn under the Decisions API answer. This file now does everything
app/app.py does.

Run it from the course folder:
    streamlit run app/steps/app_step5_also_ask_jev.py

Author: Roni Das
"""

import base64
import os
import time
from pathlib import Path

import streamlit as st
from openai import OpenAI
from typesafe_sdk import Noul, RetryPolicy, Score, TypeSafeClient

# Read the two API keys from the .env file in the course folder.
for line in open(".env"):
    for name in ("OPENAI_API_KEY", "TYPESAFE_API_KEY"):
        if line.startswith(name + "="):
            os.environ[name] = line.split("=", 1)[1].strip()

st.set_page_config(page_title="Decisions API: three question types", layout="wide")
st.title("Decisions API: three question types")

# ---------------------------------------------------------------------------
# Step 1: one call to each API, with its time and cost
# ---------------------------------------------------------------------------
@st.cache_resource
def openai_client():
    return OpenAI(max_retries=0, timeout=60.0)       # made once, reused on every rerun


@st.cache_resource
def jev_client():
    return TypeSafeClient(model="jev-1.13.0", retry=RetryPolicy(max_retries=0), timeout=60.0)


def ask_decisions(input, question):
    start = time.perf_counter()
    d = openai_client().decisions.create(model="gpt-6-luna", input=input, questions=[question])
    ms = (time.perf_counter() - start) * 1000
    tokens = d.usage.input_tokens
    return {"answer": d.answers[0].model_dump(), "ms": ms, "tokens": tokens,
            "usd": tokens * 0.10 / 1_000_000, "model": d.model}


def ask_jev(text, question):
    start = time.perf_counter()
    j = jev_client().system_one(state=text, questions={"answer": question})
    ms = (time.perf_counter() - start) * 1000
    tokens = j.usage.input_tokens
    return {"answer": j.answers["answer"].model_dump(), "ms": ms, "tokens": tokens,
            "usd": tokens * 0.042 / 1_000_000, "model": j.model}


def footer(r):
    st.caption(f"{r['model']} · {r['ms']:.0f} ms · {r['tokens']} input tokens · "
               f"${r['usd']:.8f} (from the usage in this answer)")


def bars(probs):
    for label, p in probs.items():
        a, b, c = st.columns([2, 6, 1])
        a.write(label)
        b.progress(min(p, 1.0))
        c.write(f"{p:.2f}")


tab1, tab2, tab3 = st.tabs(["Predicate: yes or no", "Choice: one of a list", "Score: a level"])

# ---------------------------------------------------------------------------
# Step 2: the yes or no tab, with a cut-off slider
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Predicate: one probability that the statement is true")
    text = st.text_area("Message", "I have asked three times now. Can I please just talk to a "
                        "real person?", key="p_text")
    instr = st.text_input("Question", "Is the customer asking for a human agent?", key="p_q")
    also_jev = st.checkbox("Also ask Jev (its Noul question)", key="p_jev")
    if st.button("Ask", key="p_go"):
        st.session_state["p"] = ask_decisions(text, {"type": "predicate", "name": "answer",
                                                     "instructions": instr})
        if also_jev:
            st.session_state["pj"] = ask_jev(text, Noul(instructions=instr))
        else:
            st.session_state.pop("pj", None)
    cut = st.slider("Act when the probability is at least", 0.0, 1.0, 0.80, 0.05, key="p_cut")
    r = st.session_state.get("p")
    if r:
        p = r["answer"]["probability"]
        bars({"yes": p})
        st.markdown(f"**{'ACT' if p >= cut else 'DO NOT ACT'}**: {p:.2f} against the cut-off {cut:.2f}")
        footer(r)
    rj = st.session_state.get("pj")
    if rj:
        st.markdown("**Jev, same message and question**")
        bars({"yes": rj["answer"]["noul"]})
        footer(rj)

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

# ---------------------------------------------------------------------------
# Step 4: the score tab, three ordered levels
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Score: ordered levels, and a weighted score between them")
    text = st.text_area("Ticket", "The export button crashes the settings page in Safari. It works "
                        "in Chrome, but a few of our customers only use Safari.", key="s_text")
    levels = [("cosmetic", "Cosmetic; no impact to functionality"),
              ("workaround", "Broken or degraded feature, but workaround exists"),
              ("blocking", "Blocking issue; no workaround exists")]
    also_jev = st.checkbox("Also ask Jev (its Score question)", key="s_jev")
    if st.button("Ask", key="s_go"):
        st.session_state["s"] = ask_decisions(text, {
            "type": "score", "name": "severity", "instructions": "How severe is the reported issue?",
            "levels": [{"label": a, "description": b} for a, b in levels]})
        if also_jev:
            st.session_state["sj"] = ask_jev(text, Score(
                instructions="How severe is the reported issue?", criteria=[b for _, b in levels]))
        else:
            st.session_state.pop("sj", None)
    r = st.session_state.get("s")
    if r:
        bars({x["label"]: x["probability"] for x in r["answer"]["probabilities"]})
        st.markdown(f"**Score {r['answer']['score']:.2f}** on a scale from 0 (cosmetic) to "
                    f"2 (blocking). Confidence {r['answer']['confidence']:.2f}.")
        footer(r)
    rj = st.session_state.get("sj")
    if rj:
        st.markdown("**Jev, same ticket and levels**")
        st.markdown(f"Score {rj['answer']['score']:.2f}, confidence {rj['answer']['confidence']:.2f}")
        footer(rj)
