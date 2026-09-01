from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

from config import HEALTH_TIMEOUT, TRANSIT_TIMEOUT, api_url


def post_json(path: str, payload: dict[str, Any], timeout: float = TRANSIT_TIMEOUT) -> Any:
    url = f"{api_url()}{path}"
    try:
        response = httpx.post(url, json=payload, timeout=timeout)
    except httpx.HTTPError as exc:
        st.error(f"No se pudo conectar a FastAPI ({url}): {exc}")
        return None
    if response.status_code >= 400:
        st.error(f"{response.status_code} {path}: {response.text}")
        return None
    return response.json()


def get_health(timeout: float = HEALTH_TIMEOUT) -> dict[str, Any] | None:
    url = f"{api_url()}/health"
    try:
        response = httpx.get(url, timeout=timeout)
    except httpx.HTTPError as exc:
        st.error(f"No se pudo conectar a FastAPI ({url}): {exc}")
        return None
    if response.status_code >= 400:
        st.error(f"{response.status_code} /health: {response.text}")
        return None
    return response.json()


def create_monthly_broadcast_draft(
    payload: dict[str, Any],
    timeout: float | None = None,
) -> Any:
    import config as config_mod

    timeout = float(getattr(config_mod, "MARKETING_TIMEOUT", 60.0) if timeout is None else timeout)
    url_fn = getattr(config_mod, "marketing_api_url", None)
    key_fn = getattr(config_mod, "marketing_api_key", None)
    base = url_fn() if callable(url_fn) else ""
    if not base:
        st.error("MARKETING_API_URL no está configurada.")
        return None
    url = f"{base}/v1/marketing/monthly-broadcasts"
    headers: dict[str, str] = {}
    token = key_fn() if callable(key_fn) else ""
    if token:
        headers["X-API-Key"] = token
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=timeout)
    except httpx.HTTPError as exc:
        st.error(f"No se pudo conectar a Marketing Backend ({url}): {exc}")
        return None
    if response.status_code >= 400:
        st.error(f"{response.status_code} /v1/marketing/monthly-broadcasts: {response.text}")
        return None
    return response.json()
