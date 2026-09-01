from __future__ import annotations

from typing import Any

GATI_LABELS = {
    "vakra": "Vakra",
    "anuvakra": "Anuvakra",
    "kutila": "Kutila / Kutilaka",
    "mandatara": "Mandatara",
    "manda": "Manda",
    "sama": "Sama",
    "sighra": "Śīghra",
    "sighratara": "Śīghratara / Atiśīghra",
}
GATI_STATUS_LABELS = {
    "classified": "classified",
    "unclassified": "unclassified",
    "not_applicable": "n/a",
}


def format_gati(value: Any) -> str:
    if value is None or value == "":
        return "—"
    key = str(value).strip().casefold()
    return GATI_LABELS.get(key, str(value))


def format_gati_status(value: Any) -> str:
    if value is None or value == "":
        return "—"
    key = str(value).strip().casefold()
    return GATI_STATUS_LABELS.get(key, str(value))


def format_virupa(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value)


def format_score(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(round(float(value), 4))
    return "—"


def _preview_text(content: str, limit: int = 180) -> str:
    text = " ".join((content or "").split())
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def rag_meaning_for_planet(planet: str, rules: list[dict[str, Any]] | None) -> str:
    return rag_meaning_index(rules).get((planet,)) or ""


def rag_meaning_index(rules: list[dict[str, Any]] | None) -> dict[tuple[Any, ...], str]:
    index: dict[tuple[Any, ...], str] = {}
    for item in rules or []:
        fact = item.get("fact") or {}
        retrieved = item.get("retrieved_rules") or []
        if not retrieved:
            continue
        preview = _preview_text(retrieved[0].get("content") or "")
        if not preview:
            continue
        planet = item.get("planet")
        house = _as_int(fact.get("house_from_moon"))
        gati = fact.get("gati")
        index[(planet, house, gati)] = preview
        index.setdefault((planet, house), preview)
        index.setdefault((planet,), preview)
    return index


def _as_int(value: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def flatten_intervals(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    meanings = rag_meaning_index(rules)
    rows: list[dict[str, Any]] = []
    for planet in facts.get("planets") or []:
        name = planet.get("planet")
        for interval in planet.get("intervals") or []:
            house = _as_int(interval.get("house_from_moon"))
            gati = interval.get("gati")
            meaning = (
                meanings.get((name, house, gati))
                or meanings.get((name, house))
                or meanings.get((name,))
                or "—"
            )
            rows.append(
                {
                    "Planet": name,
                    "Period": f"{interval.get('start', '')} → {interval.get('end', '')}",
                    "Sign": interval.get("sign"),
                    "House from Moon": house,
                    "Degree": round(float(interval.get("degree_start") or 0), 4),
                    "Direction": interval.get("direction"),
                    "Speed": round(float(interval.get("speed_longitude") or 0), 5),
                    "Gati": format_gati(gati),
                    "Gati status": format_gati_status(interval.get("gati_status")),
                    "Ceṣṭā Bala (virūpa)": format_virupa(interval.get("chesta_bala_virupa")),
                    "RAG meaning": meaning,
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
                "From": event.get("from_sign") or format_gati(event.get("from_gati")),
                "To": event.get("to_sign") or format_gati(event.get("to_gati")),
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
                    "Sign": fact.get("sign") or "—",
                    "House from Moon": fact.get("house_from_moon"),
                    "Direction": fact.get("direction") or "—",
                    "Gati": format_gati(fact.get("gati")),
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
                    "Sign": fact.get("sign") or "—",
                    "House from Moon": fact.get("house_from_moon"),
                    "Direction": fact.get("direction") or "—",
                    "Gati": format_gati(fact.get("gati")),
                    "Retrieved rule": preview,
                    "Source": rule.get("source") or rule.get("document_name") or "—",
                    "Similarity score": format_score(score),
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
