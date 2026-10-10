"""Run each web-app step file headless with Streamlit's AppTest, and print what it shows.

AppTest runs a Streamlit file without a browser. This script loads one step,
clicks one thing on it (the same click you would make on camera), and prints the
text of every element on the page in order. Steps 2 to 5 make one or two real
calls, each costing a few thousandths of a cent.

    python app/steps/test_steps.py step1    (or step2 ... step5, or all)

Author: Roni Das
Created: 2026-10-10
"""

import logging
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

# AppTest prints a harmless "missing ScriptRunContext" warning; keep the output clean.
QUIET = "streamlit.runtime.scriptrunner_utils.script_run_context"
logging.getLogger(QUIET).setLevel(logging.ERROR)

HERE = Path(__file__).resolve().parent
FILES = {"step1": "app_step1_page.py", "step2": "app_step2_yes_no_tab.py", "step3": "app_step3_egg_photo_tab.py",
         "step4": "app_step4_score_tab.py", "step5": "app_step5_also_ask_jev.py"}
TIMEOUT = 90  # seconds; a real call is well under this


def page_text(at: AppTest) -> list[str]:
    """Every element on the page that shows text, in page order, one line each."""
    return walk(at.main)


def walk(node) -> list[str]:
    """Depth-first: a block's children, or one element's kind and visible text."""
    kids = getattr(node, "children", None)
    if isinstance(kids, dict) and node.type not in ("text_area", "text_input"):
        out = []
        if node.type == "tab":
            out.append(f"[tab] {node.label}")
        for child in kids.values():
            out += walk(child)
        return out
    kind = node.type
    if kind in ("text_area", "text_input", "slider", "selectbox", "checkbox"):
        return [f"[{kind}] {node.label} = {node.value!r}"]
    if kind == "button":
        return [f"[button] {node.label}"]
    if kind == "progress":
        return []  # the bar itself; its number is printed next to it
    if kind == "imgs":
        return ["[image]"]
    value = getattr(node, "value", None)
    if isinstance(value, str) and value.strip():
        return [f"[{kind}] {value}"]
    return []


def run_step(step: str) -> int:
    """Load one step, make its one click, print the page. Returns the number of errors."""
    at = AppTest.from_file(str(HERE / FILES[step]), default_timeout=TIMEOUT)
    at.run()
    if step == "step1":
        at.text_area(key="p_text").input("Is there any way to speak to someone about my invoice?")
        action = "typed a new message (no click, no call)"
    elif step == "step2":
        at.button(key="p_go").click()
        action = "clicked Ask on the Predicate tab"
    elif step == "step3":
        at.button(key="c_go").click()
        action = "clicked Ask on the Choice tab (photo tray-06)"
    elif step == "step4":
        at.button(key="s_go").click()
        action = "clicked Ask on the Score tab"
    else:
        at.checkbox(key="p_jev").check()
        at.button(key="p_go").click()
        action = "ticked 'Also ask Jev' and clicked Ask on the Predicate tab"
    at.run()
    print(f"== {FILES[step]}: {action}")
    for line in page_text(at):
        print("  " + line)
    errors = len(at.exception) + len(at.error)
    print(f"  errors on page: {errors}")
    return errors


def main() -> None:
    """Run the steps named on the command line; exit 1 if any page shows an error."""
    names = sys.argv[1:] or ["all"]
    steps = list(FILES) if names == ["all"] else names
    bad = sum(run_step(s) for s in steps)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
