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
