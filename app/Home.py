from __future__ import annotations

import streamlit as st

from api_client import get_health, post_json
from config import TRANSIT_TIMEOUT, api_url
from constants import MONTH_NAMES, SIGNS
from flatten import interval_count, retrieved_rule_count
from state import init_state, reset_downstream_of_facts, reset_report

st.set_page_config(page_title="Monthly Jyotish Transit Report", layout="wide")
init_state()

st.title("MONTHLY JYOTISH TRANSIT REPORT")
st.caption("Calculate → review facts → retrieve RAG rules → generate Gemini report.")

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
    facts = post_json("/v1/transits/monthly", request_payload, timeout=TRANSIT_TIMEOUT)
    st.session_state.facts = facts

facts = st.session_state.facts
if facts:
    st.success(
        f"Transit facts ready ({interval_count(facts)} intervals). "
        "Open **Transit Facts** in the sidebar to review them."
    )

st.divider()
retrieve_disabled = facts is None or not rag_ok
if st.button("2. Retrieve Interpretation Rules", disabled=retrieve_disabled):
    reset_report()
    rules = post_json("/v1/transits/monthly/rules", facts, timeout=TRANSIT_TIMEOUT)
    st.session_state.rules = rules

rules = st.session_state.rules
if rules is not None:
    st.success(
        f"Retrieved {retrieved_rule_count(rules)} RAG rules. "
        "Open **Interpretation Rules** in the sidebar to review them."
    )

st.divider()
generate_disabled = facts is None or rules is None or not gemini_ok
if st.button("3. Generate Monthly Report", disabled=generate_disabled):
    report = post_json(
        "/v1/reports/monthly",
        {
            "calculated_facts": facts,
            "retrieved_rules": rules,
            "locale": "es",
        },
        timeout=TRANSIT_TIMEOUT,
    )
    st.session_state.report = report

report = st.session_state.report
if report:
    st.success("Monthly report ready. Open **Monthly Report** in the sidebar.")
    st.markdown(f"**{report.get('title') or 'Monthly report'}**")
    st.write(report.get("overview") or "")
