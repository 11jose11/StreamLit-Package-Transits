from __future__ import annotations

from typing import Any

import streamlit as st

from flatten import flatten_events, flatten_intervals, flatten_rules


def render_facts(facts: dict[str, Any]) -> None:
    st.subheader("Transit facts")
    st.dataframe(flatten_intervals(facts), use_container_width=True, hide_index=True)
    st.subheader("Events")
    events = flatten_events(facts)
    if events:
        st.dataframe(events, use_container_width=True, hide_index=True)
    else:
        st.info("No ingress or station events in this month.")
    with st.expander("Raw MonthlyTransitContext JSON"):
        st.json(facts)


def render_rules(rules: list[dict[str, Any]]) -> None:
    st.subheader("Retrieved RAG rules")
    st.dataframe(flatten_rules(rules), use_container_width=True, hide_index=True)
    with st.expander("Raw ApplicableRuleContext JSON"):
        st.json(rules)


def render_report(report: dict[str, Any]) -> None:
    st.subheader(report.get("title") or "Monthly report")
    st.markdown(
        f"**Month:** {report.get('month', '')}  \n"
        f"**Moon sign:** {report.get('moon_sign', '')}"
    )
    st.markdown("### Overview")
    st.write(report.get("overview") or "—")
    st.markdown("### Major transits")
    for item in report.get("major_transits") or []:
        st.markdown(f"**{item.get('planet', '')}** — {item.get('period', '')}")
        st.markdown(f"*{item.get('title', '')}*")
        st.write(item.get("interpretation") or "")
    st.markdown("### Ceṣṭā Bala interpretation")
    commentary = report.get("chesta_bala_commentary") or []
    if commentary:
        for item in commentary:
            st.markdown(f"**{item.get('planet', '')}**")
            st.write(item.get("commentary") or "")
    else:
        st.info("No Ceṣṭā Bala commentary (Gati remains unclassified until thresholds exist).")
    st.markdown("### Recommendations")
    st.write(report.get("recommendations") or "—")
    st.markdown("### Email")
    st.markdown(f"**Subject:** {report.get('email_subject') or '—'}")
    st.markdown(f"**Preheader:** {report.get('email_preheader') or '—'}")
    st.write(report.get("email_body") or "—")
