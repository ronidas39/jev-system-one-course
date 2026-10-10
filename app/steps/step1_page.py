"""The web app, step 1 of 5: a page with a title and one text box.

No API call yet. Streamlit runs this whole file again, from the top, every time
something on the page changes. So when you edit the message and click outside
the box, the line under it is worked out again with your new text.

    streamlit run app/steps/step1_page.py

Author: Roni Das
Created: 2026-10-10
"""

import streamlit as st

st.set_page_config(page_title="Decisions API: three question types", layout="wide")
st.title("Decisions API: three question types")

text = st.text_area("Message", "I have asked three times now. Can I please just talk to a "
                    "real person?", key="p_text")
st.write(f"You typed {len(text)} characters. Nothing has been sent anywhere yet.")
