from __future__ import annotations

import streamlit as st

from state import init_state
from views import render_facts

st.set_page_config(page_title="Transit Facts", layout="wide")
init_state()

st.title("Transit facts")
st.caption("Swiss Ephemeris intervals and events for the selected Moon sign and month.")

facts = st.session_state.facts
if not facts:
    st.info("Calculate transits on Home first.")
else:
    reference = facts.get("reference") or {}
    month = facts.get("month")
    month_label = f"{month:02d}" if isinstance(month, int) else "—"
    st.markdown(
        f"**{facts.get('year', '—')}-{month_label}** · Moon {reference.get('sign', '—')}"
    )
    render_facts(facts)
