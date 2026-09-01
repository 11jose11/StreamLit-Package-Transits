from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

DEFAULT_API_URL = "http://127.0.0.1:8000"
TRANSIT_TIMEOUT = 180.0
HEALTH_TIMEOUT = 10.0
MARKETING_TIMEOUT = 60.0


def _secret_or_env(name: str, default: str = "") -> str:
    try:
        import streamlit as st

        secret = st.secrets.get(name)
        if secret:
            return str(secret)
    except Exception:
        pass
    return os.environ.get(name, default)


def api_url() -> str:
    return _secret_or_env("TRANSIT_API_URL", DEFAULT_API_URL).rstrip("/")


def marketing_api_url() -> str:
    return _secret_or_env("MARKETING_API_URL", "").rstrip("/")


def marketing_api_key() -> str:
    return _secret_or_env("MARKETING_API_KEY") or os.environ.get("INGEST_API_KEY", "")


def marketing_configured() -> bool:
    return bool(marketing_api_url())
