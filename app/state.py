from __future__ import annotations

import streamlit as st

SESSION_KEYS = ("facts", "rules", "report")


def init_state() -> None:
    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None


def reset_downstream_of_facts() -> None:
    st.session_state.rules = None
    st.session_state.report = None


def reset_report() -> None:
    st.session_state.report = None
