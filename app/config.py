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
    configured = _secret_or_env("MARKETING_API_URL", "").rstrip("/")
    return configured or api_url()


def marketing_api_key() -> str:
    return _secret_or_env("MARKETING_API_KEY") or os.environ.get("INGEST_API_KEY", "")


def is_local_marketing_url(url: str) -> bool:
    host = (url or "").strip().lower()
    return host.startswith("http://127.0.0.1") or host.startswith("http://localhost")


def marketing_ready(url: str, key: str = "") -> bool:
    url = (url or "").strip().rstrip("/")
    if not url:
        return False
    if is_local_marketing_url(url):
        return True
    return bool((key or "").strip())


def marketing_configured() -> bool:
    return marketing_ready(marketing_api_url(), marketing_api_key())


def marketing_setup_hint() -> str:
    url = marketing_api_url()
    if not url:
        return (
            "En Cloud: App settings → Secrets con MARKETING_API_URL "
            "(la URL pública de Transit Intelligence) y MARKETING_API_KEY "
            "(la misma INGEST_API_KEY del API). "
            "En local: StreamLit Package/.env. Nunca pongas RESEND_API_KEY aquí."
        )
    if not marketing_ready(url, marketing_api_key()):
        return (
            "Falta MARKETING_API_KEY. En Cloud es obligatoria "
            "(la misma INGEST_API_KEY del API)."
        )
    return ""
