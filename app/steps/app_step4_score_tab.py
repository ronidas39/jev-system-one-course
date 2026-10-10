"""The web app, step 4 of 5: add the Score tab.

The new tab asks how severe a ticket is, on three ordered levels. The answer has a
probability for each level, and a weighted score between 0 (cosmetic) and 2
(blocking), so a ticket that sits between two levels shows up as a number in between.

    streamlit run app/steps/app_step4_score_tab.py

Author: Roni Das
Created: 2026-10-10
"""

import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "decisions"))

from common import MODEL, cost_usd, image_data_url  # noqa: E402
from egg_questions import EGG_QUESTIONS  # noqa: E402

from jevcourse.config import load_env_file  # noqa: E402

load_env_file()
EGGS = ROOT / "decisions" / "eggs"
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


tab1, tab2, tab3 = st.tabs(["Predicate: yes or no", "Choice: one of a list", "Score: a level"])

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

with tab2:
    st.subheader("Choice: an egg photo, one bar per option, two cut-offs")
    names = sorted(p.stem for p in EGGS.glob("*.jpg"))
    pick = st.selectbox("Egg photo (CC0 and public domain, see decisions/eggs/CREDITS.md)", names,
                        index=names.index("tray-06"), key="c_pick")
    upload = st.file_uploader("Or upload your own JPEG or PNG (it is sent to OpenAI when you click Ask)",
                              type=["jpg", "jpeg", "png"], key="c_up")
    if upload:
        kind = "png" if upload.name.lower().endswith(".png") else "jpeg"
        import base64
        url = f"data:image/{kind};base64," + base64.b64encode(upload.getvalue()).decode("ascii")
        st.image(upload.getvalue(), width=220)
        source = upload.name
    else:
        url = image_data_url(EGGS / f"{pick}.jpg")
        st.image(str(EGGS / f"{pick}.jpg"), width=220)
        source = pick
    if st.button("Ask", key="c_go"):
        st.session_state["c"] = safe(ask_decisions, [{"role": "user", "content": [
            {"type": "input_text", "text": "One egg from a grading line."},
            {"type": "input_image", "image_url": url}]}], EGG_QUESTIONS[0])
        st.session_state["c_src"] = source
    low, high = st.slider("Not clean = 1 - P(clean). Pass below the left handle, reject above the right:",
                          0.0, 1.0, (0.30, 0.70), 0.05, key="c_cut")
    r = st.session_state.get("c")
    if r:
        st.caption(f"Answer for: {st.session_state.get('c_src')}")
        if r["answer"]["type"] == "refusal":
            st.warning("The API refused this question. Send it to a person.")
        else:
            probs = {x["value"]: x["probability"] for x in r["answer"]["probabilities"]}
            bars(probs)
            not_clean = 1.0 - probs.get("clean", 0.0)
            verdict = ("PASS" if not_clean < low else "REJECT" if not_clean > high
                       else "SEND TO A PERSON")
            st.markdown(f"**{verdict}**: not clean {not_clean:.2f}. Pass below {low:.2f}, "
                        f"reject above {high:.2f}, a person checks the band in between.")
        footer(r)

with tab3:
    st.subheader("Score: ordered levels, and a weighted score between them")
    text = st.text_area("Ticket", "The export button crashes the settings page in Safari. It works "
                        "in Chrome, but a few of our customers only use Safari.", key="s_text")
    levels = [("cosmetic", "Cosmetic; no impact to functionality"),
              ("workaround", "Broken or degraded feature, but workaround exists"),
              ("blocking", "Blocking issue; no workaround exists")]
    if st.button("Ask", key="s_go"):
        st.session_state["s"] = safe(ask_decisions, text, {
            "type": "score", "name": "severity", "instructions": "How severe is the reported issue?",
            "levels": [{"label": a, "description": b} for a, b in levels]})
    r = st.session_state.get("s")
    if r:
        if r["answer"]["type"] == "refusal":
            st.warning("The API refused this question. Send it to a person.")
        else:
            bars({x["label"]: x["probability"] for x in r["answer"]["probabilities"]})
            st.markdown(f"**Score {r['answer']['score']:.2f}** on a scale from 0 (cosmetic) to "
                        f"2 (blocking). Confidence {r['answer']['confidence']:.2f}.")
        footer(r)
