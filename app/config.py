from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

DEFAULT_API_URL = "http://127.0.0.1:8000"
TRANSIT_TIMEOUT = 180.0
MUHURTA_TIMEOUT = 300.0
HEALTH_TIMEOUT = 10.0


def api_url() -> str:
    try:
        import streamlit as st

        secret = st.secrets.get("TRANSIT_API_URL")
        if secret:
            return str(secret).rstrip("/")
    except Exception:
        pass
    return os.environ.get("TRANSIT_API_URL", DEFAULT_API_URL).rstrip("/")
