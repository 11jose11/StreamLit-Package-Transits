from __future__ import annotations

import streamlit as st

from state import init_state
from views import render_report

st.set_page_config(page_title="Monthly Report", layout="wide")
init_state()

st.title("Monthly report")
st.caption("Gemini language from calculated facts and retrieved rules only.")

facts = st.session_state.facts
rules = st.session_state.rules
report = st.session_state.report
if facts is None or rules is None:
    st.info("Complete Calculate Transits and Retrieve Interpretation Rules on Home first.")
elif report is None:
    st.info("Generate the monthly report on Home after retrieving rules.")
else:
    render_report(report)
