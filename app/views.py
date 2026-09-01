from __future__ import annotations

from typing import Any

import streamlit as st

from api_client import post_json
from config import TRANSIT_TIMEOUT
from flatten import flatten_events, flatten_intervals, flatten_rules, format_gati
from state import reset_report


def render_facts(facts: dict[str, Any], rules: list[dict[str, Any]] | None = None) -> None:
    st.subheader("Transit facts")
    st.dataframe(
        flatten_intervals(facts, rules),
        width="stretch",
        hide_index=True,
    )
    if rules:
        st.subheader("Jyotiṣa notes for these transits")
        render_rule_meanings(rules)
    else:
        st.info("Retrieve interpretation rules to attach RAG notes to these transits.")
    st.subheader("Events")
    events = flatten_events(facts)
    if events:
        st.dataframe(events, width="stretch", hide_index=True)
    else:
        st.info("No ingress or station events in this month.")
    with st.expander("Raw MonthlyTransitContext JSON"):
        st.json(facts)


def render_retrieve_button(facts: dict[str, Any] | None, *, key: str) -> None:
    if facts is None:
        return
    if st.button("Retrieve interpretation rules", key=key, type="primary"):
        with st.spinner("Retrieving Jyotiṣa notes from the knowledge base..."):
            reset_report()
            rules = post_json("/v1/transits/monthly/rules", facts, timeout=TRANSIT_TIMEOUT)
            if rules is not None:
                st.session_state.rules = rules
                st.rerun()


def render_rule_meanings(rules: list[dict[str, Any]]) -> None:
    for item in rules:
        fact = item.get("fact") or {}
        planet = item.get("planet") or "—"
        house = fact.get("house_from_moon")
        gati = format_gati(fact.get("gati"))
        virupa = fact.get("chesta_bala_virupa")
        heading = f"{planet} · house {house} from Moon"
        if gati != "—":
            heading += f" · {gati}"
        if virupa is not None:
            heading += f" · Ceṣṭā Bala {virupa:g}"
        retrieved = item.get("retrieved_rules") or []
        with st.expander(heading, expanded=bool(retrieved)):
            if not retrieved:
                st.info("No knowledge-base chunks for this transit.")
                continue
            for rule in retrieved:
                source = rule.get("source") or rule.get("document_name") or "—"
                st.markdown(rule.get("content") or "")
                st.caption(source)
                st.divider()


def render_rules(rules: list[dict[str, Any]]) -> None:
    st.subheader("Retrieved RAG rules")
    st.dataframe(flatten_rules(rules), width="stretch", hide_index=True)
    st.subheader("Meanings")
    render_rule_meanings(rules)
    with st.expander("Raw ApplicableRuleContext JSON"):
        st.json(rules)


def render_report(report: dict[str, Any], *, reserved_chesta: bool = False) -> None:
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
    commentary = [
        item
        for item in report.get("chesta_bala_commentary") or []
        if item.get("commentary")
    ]
    if commentary:
        for item in commentary:
            st.markdown(f"**{item.get('planet', '')}**")
            st.write(item.get("commentary") or "")
    elif reserved_chesta:
        st.info(
            "No Ceṣṭā Bala commentary yet. "
            "Generate with Gemini after retrieving rules."
        )
    else:
        st.info("No Ceṣṭā Bala commentary in this report.")
    st.markdown("### Recommendations")
    st.write(report.get("recommendations") or "—")
    st.markdown("### Email")
    st.markdown(f"**Subject:** {report.get('email_subject') or '—'}")
    st.markdown(f"**Preheader:** {report.get('email_preheader') or '—'}")
    st.write(report.get("email_body") or "—")
