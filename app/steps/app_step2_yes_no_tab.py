"""The web app, step 2 of 5: the Predicate tab calls the Decisions API.

The message box from step 1 moves into a tab, and gets a question box, an Ask
button and a cut-off slider. Clicking Ask makes one real call. The answer is kept
in st.session_state, the page's memory between runs, so moving the slider only
runs the cut-off rule again and never calls the API.

    streamlit run app/steps/app_step2_yes_no_tab.py

Author: Roni Das
Created: 2026-10-10
"""

import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "decisions"))

from common import MODEL, cost_usd  # noqa: E402

from jevcourse.config import load_env_file  # noqa: E402

load_env_file()
st.set_page_config(page_title="Decisions API: three question types", layout="wide")
st.title("Decisions API: three question types")


@st.cache_resource
def openai_client():
    from openai import OpenAI
    return OpenAI(max_retries=0, timeout=60.0)


def ask_decisions(input, question: dict) -> dict:
    """One real call. Returns the answer as a dict, plus time, tokens and cost."""
    start = time.perf_counter()
    d = openai_client().decisions.create(model=MODEL, input=input, questions=[question])
    ms = (time.perf_counter() - start) * 1000
    return {"answer": d.answers[0].model_dump(), "ms": ms, "tokens": d.usage.input_tokens,
            "usd": cost_usd(d.usage.input_tokens), "model": d.model}


def safe(fn, *args):
    """Run a call; show an API error on the page instead of crashing."""
    try:
        return fn(*args)
    except (Exception, SystemExit) as error:  # noqa: BLE001  a missing key raises SystemExit
        st.error(f"The call failed: {type(error).__name__}: {str(error)[:300]}")
        return None


def footer(r: dict) -> None:
    st.caption(f"{r['model']} · {r['ms']:.0f} ms · {r['tokens']} input tokens · "
               f"${r['usd']:.8f} (from the usage in this answer)")


def bars(probs: dict[str, float]) -> None:
    for label, p in probs.items():
        a, b, c = st.columns([2, 6, 1])
        a.write(label)
        b.progress(min(max(p, 0.0), 1.0))
        c.write(f"{p:.2f}")


[tab1] = st.tabs(["Predicate: yes or no"])

with tab1:
    st.subheader("Predicate: one probability that the statement is true")
    text = st.text_area("Message", "I have asked three times now. Can I please just talk to a "
                        "real person?", key="p_text")
    instr = st.text_input("Question", "Is the customer asking for a human agent?", key="p_q")
    if st.button("Ask", key="p_go"):
        st.session_state["p"] = safe(ask_decisions, text,
                                     {"type": "predicate", "name": "answer", "instructions": instr})
    cut = st.slider("Act when the probability is at least", 0.0, 1.0, 0.80, 0.05, key="p_cut")
    r = st.session_state.get("p")
    if r:
        if r["answer"]["type"] == "refusal":
            st.warning("The API refused this question. Send it to a person.")
        else:
            p = r["answer"]["probability"]
            bars({"yes": p})
            st.markdown(f"**{'ACT' if p >= cut else 'DO NOT ACT'}**: {p:.2f} against the cut-off {cut:.2f}")
        footer(r)
