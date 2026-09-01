from __future__ import annotations

import importlib

import streamlit as st

import flatten as flatten_mod
import views as views_mod
from state import init_state

flatten_mod = importlib.reload(flatten_mod)
views_mod = importlib.reload(views_mod)
render_facts = views_mod.render_facts
render_retrieve_button = views_mod.render_retrieve_button

st.set_page_config(page_title="Transit Facts", layout="wide")
init_state()

st.title("Transit facts")
st.caption("Swiss Ephemeris intervals with RAG notes attached after retrieval.")

facts = st.session_state.facts
rules = st.session_state.rules
if not facts:
    st.info("Calculate transits on Home first.")
else:
    reference = facts.get("reference") or {}
    month = facts.get("month")
    month_label = f"{month:02d}" if isinstance(month, int) else "—"
    st.markdown(
        f"**{facts.get('year', '—')}-{month_label}** · Moon {reference.get('sign', '—')}"
    )
    render_retrieve_button(facts, key="retrieve_on_facts")
    render_facts(facts, rules=rules)
