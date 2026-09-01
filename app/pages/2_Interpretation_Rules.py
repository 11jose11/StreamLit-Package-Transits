from __future__ import annotations

import streamlit as st

from flatten import retrieved_rule_count
from state import init_state
from views import render_rules

st.set_page_config(page_title="Interpretation Rules", layout="wide")
init_state()

st.title("Interpretation rules")
st.caption("Jyotiṣa notes retrieved from the knowledge base. The dashboard does not invent rules.")

facts = st.session_state.facts
rules = st.session_state.rules
if facts is None:
    st.info("Calculate transits on Home first, then retrieve interpretation rules.")
elif rules is None:
    st.info("Retrieve interpretation rules on Home after calculating transits.")
else:
    st.markdown(f"**{retrieved_rule_count(rules)}** retrieved chunks")
    render_rules(rules)
