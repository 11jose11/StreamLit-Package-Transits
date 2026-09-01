from __future__ import annotations

import streamlit as st

SESSION_KEYS = (
    "facts",
    "rules",
    "report",
    "studio_draft",
    "studio_interval_include",
    "studio_rule_include",
    "studio_facts_id",
    "studio_rules_id",
    "studio_draft_rev",
)


def init_state() -> None:
    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = 0 if key == "studio_draft_rev" else None


def reset_studio() -> None:
    st.session_state.studio_draft = None
    st.session_state.studio_interval_include = None
    st.session_state.studio_rule_include = None
    st.session_state.studio_facts_id = None
    st.session_state.studio_rules_id = None
    st.session_state.studio_draft_rev = 0


def reset_downstream_of_facts() -> None:
    st.session_state.rules = None
    st.session_state.report = None
    reset_studio()


def reset_report() -> None:
    st.session_state.report = None
