from __future__ import annotations

import importlib

import streamlit as st

import flatten as flatten_mod
import state as state_mod
import views as views_mod
from api_client import get_health, post_json
from config import TRANSIT_TIMEOUT, api_url
from constants import MONTH_NAMES, SIGNS
from flatten import interval_count, retrieved_rule_count

flatten_mod = importlib.reload(flatten_mod)
state_mod = importlib.reload(state_mod)
views_mod = importlib.reload(views_mod)
render_facts = views_mod.render_facts
init_state = state_mod.init_state
reset_downstream_of_facts = state_mod.reset_downstream_of_facts
reset_report = state_mod.reset_report

st.set_page_config(page_title="Monthly Jyotish Transit Report", layout="wide")
init_state()

st.title("MONTHLY JYOTISH TRANSIT REPORT")
st.caption(
    "Calculate monthly transits, or open Muhūrta from the button below or the sidebar page list."
)

health = get_health()
api_ok = health is not None and health.get("status") == "ok"
ephemeris_ok = bool(health and health.get("ephemeris_path_set"))
rag_ok = bool(health and health.get("rag_configured"))
gemini_ok = bool(health and health.get("gemini_configured"))

with st.sidebar:
    st.subheader("API")
    st.caption(api_url())
    st.write("Status:", "ok" if api_ok else "unreachable")
    st.write("Ephemeris:", "ready" if ephemeris_ok else "not configured")
    st.write("RAG:", "ready" if rag_ok else "not configured")
    st.write("Gemini:", "ready" if gemini_ok else "not configured")
    facts = st.session_state.facts
    rules = st.session_state.rules
    report = st.session_state.report
    st.divider()
    st.subheader("Session")
    st.write("Intervals:", interval_count(facts) if facts else 0)
    st.write("Rules:", retrieved_rule_count(rules) if rules else 0)
    st.write("Report:", "yes" if report else "no")
    st.divider()
    st.page_link("pages/4_Muhurta.py", label="Muhūrta")

col1, col2, col3 = st.columns(3)
with col1:
    moon_sign = st.selectbox("Moon Sign", SIGNS, index=0)
with col2:
    month_name = st.selectbox("Month", MONTH_NAMES, index=9)
    month = MONTH_NAMES.index(month_name) + 1
with col3:
    year = st.number_input("Year", min_value=1900, max_value=2100, value=2026, step=1)

request_payload = {"year": int(year), "month": int(month), "moon_sign": moon_sign}

st.divider()
calculate_disabled = not ephemeris_ok
if st.button("1. Calculate Transits", type="primary", disabled=calculate_disabled):
    reset_downstream_of_facts()
    with st.spinner("Calculating transits and retrieving RAG notes..."):
        facts = post_json("/v1/transits/monthly", request_payload, timeout=TRANSIT_TIMEOUT)
        st.session_state.facts = facts
        if facts and rag_ok:
            retrieved = post_json("/v1/transits/monthly/rules", facts, timeout=TRANSIT_TIMEOUT)
            if retrieved is not None:
                st.session_state.rules = retrieved

facts = st.session_state.facts
if facts:
    st.success(f"Transit facts ready ({interval_count(facts)} intervals).")

st.divider()
retrieve_disabled = facts is None or not rag_ok
if st.button("2. Retrieve Interpretation Rules", disabled=retrieve_disabled):
    with st.spinner("Retrieving Jyotiṣa notes from the knowledge base..."):
        reset_report()
        retrieved = post_json("/v1/transits/monthly/rules", facts, timeout=TRANSIT_TIMEOUT)
        if retrieved is not None:
            st.session_state.rules = retrieved

rules = st.session_state.rules
if rules is not None:
    st.success(f"Retrieved {retrieved_rule_count(rules)} RAG notes — shown on the transits below.")

if facts:
    render_facts(facts, rules=rules)

st.divider()
studio_disabled = facts is None
col_studio, col_muhurta = st.columns(2)
with col_studio:
    if st.button("3. Open Monthly Report Studio", disabled=studio_disabled, use_container_width=True):
        st.switch_page("pages/3_Monthly_Report.py")
with col_muhurta:
    if st.button("4. Open Muhūrta", type="primary", use_container_width=True):
        st.switch_page("pages/4_Muhurta.py")
st.caption("Muhūrta finds election windows for one month. It does not need transit facts first.")
if facts:
    st.caption(
        "The studio prepares Spanish report text from selected transit ranges, "
        "house RAG notes, and retrieved Ceṣṭā Bala notes."
    )
