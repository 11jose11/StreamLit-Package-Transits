from __future__ import annotations

from typing import Any


def flatten_intervals(facts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for planet in facts.get("planets") or []:
        for interval in planet.get("intervals") or []:
            rows.append(
                {
                    "Planet": planet.get("planet"),
                    "Period": f"{interval.get('start', '')} → {interval.get('end', '')}",
                    "Sign": interval.get("sign"),
                    "House from Moon": interval.get("house_from_moon"),
                    "Degree": round(float(interval.get("degree_start") or 0), 4),
                    "Direction": interval.get("direction"),
                    "Speed": round(float(interval.get("speed_longitude") or 0), 5),
                    "Gati": interval.get("gati") or "—",
                    "Ceṣṭā Bala": interval.get("chesta_bala_virupa")
                    if interval.get("chesta_bala_virupa") is not None
                    else "—",
                }
            )
    return rows


def flatten_events(facts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in facts.get("events") or []:
        rows.append(
            {
                "Date": event.get("datetime_utc"),
                "Planet": event.get("planet"),
                "Event": event.get("event_type"),
                "From": event.get("from_sign") or "—",
                "To": event.get("to_sign") or "—",
            }
        )
    return rows


def flatten_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in rules:
        fact = item.get("fact") or {}
        retrieved = item.get("retrieved_rules") or []
        if not retrieved:
            rows.append(
                {
                    "Planet": item.get("planet"),
                    "House from Moon": fact.get("house_from_moon"),
                    "Retrieved rule": "(none)",
                    "Source": "—",
                    "Similarity score": "—",
                }
            )
            continue
        for rule in retrieved:
            content = (rule.get("content") or "").strip()
            preview = content if len(content) <= 400 else content[:400] + "…"
            score = rule.get("score")
            rows.append(
                {
                    "Planet": item.get("planet"),
                    "House from Moon": fact.get("house_from_moon"),
                    "Retrieved rule": preview,
                    "Source": rule.get("source") or rule.get("document_name") or "—",
                    "Similarity score": round(score, 4) if isinstance(score, (int, float)) else "—",
                }
            )
    return rows


def interval_count(facts: dict[str, Any] | None) -> int:
    if not facts:
        return 0
    return sum(len(planet.get("intervals") or []) for planet in facts.get("planets") or [])


def retrieved_rule_count(rules: list[dict[str, Any]] | None) -> int:
    if not rules:
        return 0
    return sum(len(item.get("retrieved_rules") or []) for item in rules)
