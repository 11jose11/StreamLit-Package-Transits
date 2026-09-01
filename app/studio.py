from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from constants import MONTH_NAMES
from flatten import (
    format_gati,
    format_gati_status,
    format_virupa,
    interval_count,
    is_moon_transit,
    rag_meaning_for_planet,
    rag_meaning_index,
    retrieved_rule_count,
    without_moon_rules,
    without_moon_transits,
)


def month_label(facts: dict[str, Any] | None) -> str:
    if not facts:
        return ""
    month = facts.get("month")
    year = facts.get("year")
    if isinstance(month, int) and 1 <= month <= 12:
        return f"{MONTH_NAMES[month - 1]} {year}"
    return f"{year}-{month}"


def moon_sign(facts: dict[str, Any] | None) -> str:
    if not facts:
        return ""
    reference = facts.get("reference") or {}
    return str(reference.get("sign") or "")


def facts_fingerprint(facts: dict[str, Any] | None) -> str:
    if not facts:
        return ""
    return "|".join(
        [
            str(facts.get("year") or ""),
            str(facts.get("month") or ""),
            moon_sign(facts),
            str(interval_count(facts)),
        ]
    )


def iter_intervals(facts: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    for planet in facts.get("planets") or []:
        name = str(planet.get("planet") or "")
        if is_moon_transit(name):
            continue
        for interval in planet.get("intervals") or []:
            yield name, interval


def interval_key(planet: str, interval: dict[str, Any]) -> str:
    return "|".join(
        [
            planet,
            str(interval.get("start") or ""),
            str(interval.get("end") or ""),
            str(interval.get("house_from_moon") or ""),
        ]
    )


def interval_key_from_row(row: dict[str, Any]) -> str:
    stored = str(row.get("_key") or "").strip()
    if stored:
        return stored
    period = str(row.get("Period") or "")
    start, end = period.split(" → ", 1) if " → " in period else ("", "")
    return "|".join(
        [
            str(row.get("Planet") or ""),
            start,
            end,
            str(row.get("House from Moon") or ""),
        ]
    )


def default_interval_keys(facts: dict[str, Any]) -> list[str]:
    return [interval_key(planet, interval) for planet, interval in iter_intervals(facts)]


def rule_chunk_key(item_index: int, chunk_index: int) -> str:
    return f"{item_index}|{chunk_index}"


def default_rule_keys(rules: list[dict[str, Any]]) -> list[str]:
    return [entry["key"] for entry in iter_rule_entries(rules)]


def iter_rule_entries(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item_index, item in enumerate(without_moon_rules(rules)):
        fact = item.get("fact") or {}
        retrieved = item.get("retrieved_rules") or []
        if not retrieved:
            entries.append(
                {
                    "key": rule_chunk_key(item_index, -1),
                    "item_index": item_index,
                    "chunk_index": -1,
                    "planet": item.get("planet"),
                    "sign": fact.get("sign"),
                    "house_from_moon": fact.get("house_from_moon"),
                    "gati": fact.get("gati"),
                    "content": "",
                    "source": "",
                    "score": None,
                }
            )
            continue
        for chunk_index, rule in enumerate(retrieved):
            entries.append(
                {
                    "key": rule_chunk_key(item_index, chunk_index),
                    "item_index": item_index,
                    "chunk_index": chunk_index,
                    "planet": item.get("planet"),
                    "sign": fact.get("sign"),
                    "house_from_moon": fact.get("house_from_moon"),
                    "gati": fact.get("gati"),
                    "content": rule.get("content") or "",
                    "source": rule.get("source") or rule.get("document_name") or "",
                    "score": rule.get("score"),
                }
            )
    return entries


def filter_facts(
    facts: dict[str, Any], include_keys: list[str] | None
) -> dict[str, Any]:
    facts = without_moon_transits(facts) or {}
    if include_keys is None:
        return facts
    allowed = set(include_keys)
    planets: list[dict[str, Any]] = []
    selected_planets: set[str] = set()
    for planet in facts.get("planets") or []:
        name = str(planet.get("planet") or "")
        intervals = [
            interval
            for interval in planet.get("intervals") or []
            if interval_key(name, interval) in allowed
        ]
        if intervals:
            planets.append({**planet, "intervals": intervals})
            selected_planets.add(name)
    events = [
        event
        for event in facts.get("events") or []
        if str(event.get("planet") or "") in selected_planets
    ]
    return {**facts, "planets": planets, "events": events}


def filter_rules(
    rules: list[dict[str, Any]], include_keys: list[str] | None
) -> list[dict[str, Any]]:
    rules = without_moon_rules(rules)
    if include_keys is None:
        return list(rules)
    allowed = set(include_keys)
    selected: list[dict[str, Any]] = []
    for item_index, item in enumerate(rules):
        retrieved = item.get("retrieved_rules") or []
        if not retrieved:
            if rule_chunk_key(item_index, -1) in allowed:
                selected.append(item)
            continue
        kept = [
            rule
            for chunk_index, rule in enumerate(retrieved)
            if rule_chunk_key(item_index, chunk_index) in allowed
        ]
        if kept:
            selected.append({**item, "retrieved_rules": kept})
    return selected


def included_interval_rows(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None,
    include_keys: list[str] | None,
) -> list[dict[str, Any]]:
    allowed = None if include_keys is None else set(include_keys)
    return [
        row
        for row in interval_picker_rows(facts, rules, include_keys)
        if allowed is None or interval_key_from_row(row) in allowed
    ]


def interval_picker_rows(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None,
    include_keys: list[str] | None,
) -> list[dict[str, Any]]:
    meanings = rag_meaning_index(rules)
    allowed = None if include_keys is None else set(include_keys)
    rows: list[dict[str, Any]] = []
    for planet, interval in iter_intervals(facts):
        key = interval_key(planet, interval)
        house = interval.get("house_from_moon")
        gati = interval.get("gati")
        meaning = (
            meanings.get((planet, house, gati))
            or meanings.get((planet, house))
            or meanings.get((planet,))
            or ""
        )
        rows.append(
            {
                "Include": allowed is None or key in allowed,
                "Planet": planet,
                "Period": f"{interval.get('start', '')} → {interval.get('end', '')}",
                "Sign": interval.get("sign"),
                "House from Moon": house,
                "Gati": format_gati(gati),
                "Gati status": format_gati_status(interval.get("gati_status")),
                "Ceṣṭā Bala (virūpa)": format_virupa(interval.get("chesta_bala_virupa")),
                "RAG meaning": meaning or "—",
                "_key": key,
            }
        )
    return rows


def rule_picker_rows(
    rules: list[dict[str, Any]], include_keys: list[str] | None
) -> list[dict[str, Any]]:
    allowed = None if include_keys is None else set(include_keys)
    rows: list[dict[str, Any]] = []
    for entry in iter_rule_entries(rules):
        content = " ".join(str(entry.get("content") or "").split())
        preview = content if len(content) <= 220 else content[:220] + "…"
        rows.append(
            {
                "Include": allowed is None or entry["key"] in allowed,
                "Planet": entry.get("planet"),
                "Sign": entry.get("sign") or "—",
                "House from Moon": entry.get("house_from_moon"),
                "Gati": format_gati(entry.get("gati")),
                "Source": entry.get("source") or "—",
                "RAG note": preview or "(none)",
                "_key": entry["key"],
            }
        )
    return rows


def as_records(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if hasattr(value, "to_dict"):
        return list(value.to_dict("records"))
    return [row for row in value if isinstance(row, dict)]


def selected_rule_keys_from_rows(rows: Any) -> list[str]:
    return [
        str(row.get("_key") or "")
        for row in as_records(rows)
        if row.get("Include") and row.get("_key")
    ]


def selected_interval_keys_from_rows(rows: Any) -> list[str]:
    keys: list[str] = []
    for row in as_records(rows):
        if not row.get("Include"):
            continue
        if is_moon_transit(row.get("Planet")):
            continue
        key = interval_key_from_row(row)
        if key:
            keys.append(key)
    return keys


def selection_from_editor(
    rows: Any,
    fallback: list[str] | None,
    *,
    kind: str,
    expected: int | None = None,
) -> list[str] | None:
    records = as_records(rows)
    if not records:
        return fallback
    if expected is not None and len(records) < expected:
        return fallback
    if kind == "rules":
        return selected_rule_keys_from_rows(records)
    return selected_interval_keys_from_rows(records)


def chesta_rows(facts: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for planet, interval in iter_intervals(facts):
        if not planet or planet in seen:
            continue
        seen.add(planet)
        rows.append(
            {
                "Planet": planet,
                "Gati": format_gati(interval.get("gati")),
                "Status": format_gati_status(interval.get("gati_status")),
                "Ceṣṭā Bala (virūpa)": format_virupa(interval.get("chesta_bala_virupa")),
            }
        )
    return rows


def classified_chesta_planets(facts: dict[str, Any]) -> list[str]:
    planets: list[str] = []
    seen: set[str] = set()
    for planet, interval in iter_intervals(facts):
        if planet in seen:
            continue
        if str(interval.get("gati_status") or "") != "classified":
            continue
        seen.add(planet)
        planets.append(planet)
    return planets


def is_chesta_source(source: str | None) -> bool:
    text = (source or "").casefold()
    return "chesta" in text or text == "regla global rag"


def chesta_notes_for_planet(planet: str, rules: list[dict[str, Any]] | None) -> str:
    parts: list[str] = []
    for item in rules or []:
        if str(item.get("planet") or "") != planet:
            continue
        for rule in item.get("retrieved_rules") or []:
            if not is_chesta_source(rule.get("source") or rule.get("document_name")):
                continue
            content = (rule.get("content") or "").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts[:3])


def seed_chesta_commentary(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        {
            "planet": planet,
            "commentary": chesta_notes_for_planet(planet, rules),
        }
        for planet in classified_chesta_planets(facts)
    ]


def merge_chesta_rules(
    all_rules: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = [dict(item) for item in selected]
    index = {str(item.get("planet") or ""): i for i, item in enumerate(merged)}
    for item in all_rules:
        chesta = [
            rule
            for rule in item.get("retrieved_rules") or []
            if is_chesta_source(rule.get("source") or rule.get("document_name"))
        ]
        if not chesta:
            continue
        planet = str(item.get("planet") or "")
        if planet in index:
            current = list(merged[index[planet]].get("retrieved_rules") or [])
            seen = {(rule.get("content") or "")[:80] for rule in current}
            extra = [rule for rule in chesta if (rule.get("content") or "")[:80] not in seen]
            merged[index[planet]] = {
                **merged[index[planet]],
                "retrieved_rules": current + extra,
            }
        else:
            merged.append({**item, "retrieved_rules": chesta})
    return merged


def chesta_note_rows(rules: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in rules or []:
        for rule in item.get("retrieved_rules") or []:
            source = rule.get("source") or rule.get("document_name") or ""
            if not is_chesta_source(source):
                continue
            content = " ".join((rule.get("content") or "").split())
            rows.append(
                {
                    "Planet": item.get("planet"),
                    "Source": source,
                    "Gati note": content[:220] + ("…" if len(content) > 220 else ""),
                }
            )
    return rows


def empty_draft(facts: dict[str, Any] | None = None) -> dict[str, Any]:
    label = month_label(facts)
    moon = moon_sign(facts)
    title = "Informe mensual"
    if label and moon:
        title = f"Informe mensual · {label} · Luna en {moon}"
    elif label:
        title = f"Informe mensual · {label}"
    return {
        "title": title,
        "month": label,
        "moon_sign": moon,
        "overview": "",
        "major_transits": [],
        "chesta_bala_commentary": [],
        "recommendations": "",
        "email_subject": "",
        "email_preheader": "",
        "email_body": "",
    }


def seed_draft(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None,
    include_interval_keys: list[str] | None,
) -> dict[str, Any]:
    draft = empty_draft(facts)
    included = included_interval_rows(facts, rules, include_interval_keys)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in included:
        grouped.setdefault(str(row.get("Planet") or ""), []).append(row)

    major: list[dict[str, Any]] = []
    for planet, rows in grouped.items():
        periods = [str(row.get("Period") or "") for row in rows if row.get("Period")]
        starts = [period.split(" → ", 1)[0] for period in periods if " → " in period]
        ends = [period.split(" → ", 1)[1] for period in periods if " → " in period]
        signs = list(dict.fromkeys(str(row.get("Sign") or "") for row in rows if row.get("Sign")))
        houses = list(
            dict.fromkeys(
                str(row.get("House from Moon") or "")
                for row in rows
                if row.get("House from Moon") not in (None, "")
            )
        )
        gatis = list(
            dict.fromkeys(
                str(row.get("Gati") or "")
                for row in rows
                if row.get("Gati") not in (None, "—", "")
            )
        )
        meaning = rag_meaning_for_planet(planet, rules)
        house_label = ", ".join(f"casa {house}" for house in houses) if houses else ""
        title_parts = [planet]
        if signs:
            title_parts.append(", ".join(signs))
        if house_label:
            title_parts.append(f"{house_label} desde la Luna")
        major.append(
            {
                "planet": planet,
                "period": f"{min(starts)} → {max(ends)}" if starts and ends else "",
                "title": " · ".join(title_parts),
                "interpretation": meaning,
                "working_notes": _working_notes(rows, meaning, gatis),
            }
        )
    draft["major_transits"] = major
    draft["chesta_bala_commentary"] = seed_chesta_commentary(facts, rules)
    return draft


def _working_notes(rows: list[dict[str, Any]], meaning: str, gatis: list[str]) -> str:
    lines = [
        f"- {row.get('Period')}: {row.get('Sign')}, "
        f"casa {row.get('House from Moon')} desde la Luna"
        for row in rows
    ]
    if gatis:
        lines.append(f"- Gati en el mes: {', '.join(gatis)}")
    lines.append(f"- Nota RAG: {meaning}" if meaning else "- Nota RAG: (vacía)")
    return "\n".join(lines)


def apply_gemini_report(draft: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    merged = dict(draft)
    for key in (
        "title",
        "month",
        "moon_sign",
        "overview",
        "recommendations",
        "email_subject",
        "email_preheader",
        "email_body",
    ):
        if report.get(key):
            merged[key] = report[key]
    incoming = report.get("major_transits") or []
    if incoming:
        notes = {
            item.get("planet"): item.get("working_notes")
            for item in draft.get("major_transits") or []
        }
        merged["major_transits"] = [
            {**item, "working_notes": notes.get(item.get("planet"), "")}
            for item in incoming
            if not is_moon_transit(item.get("planet"))
        ]
    incoming_chesta = report.get("chesta_bala_commentary") or []
    if incoming_chesta:
        merged["chesta_bala_commentary"] = [
            item for item in incoming_chesta if not is_moon_transit(item.get("planet"))
        ]
    else:
        merged["chesta_bala_commentary"] = [
            item
            for item in draft.get("chesta_bala_commentary") or []
            if not is_moon_transit(item.get("planet"))
        ]
    return merged


def report_payload(draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": draft.get("title") or "",
        "month": draft.get("month") or "",
        "moon_sign": draft.get("moon_sign") or "",
        "overview": draft.get("overview") or "",
        "major_transits": [
            {
                "planet": item.get("planet") or "",
                "period": item.get("period") or "",
                "title": item.get("title") or "",
                "interpretation": item.get("interpretation") or "",
            }
            for item in draft.get("major_transits") or []
            if not is_moon_transit(item.get("planet"))
        ],
        "chesta_bala_commentary": [
            {
                "planet": item.get("planet") or "",
                "commentary": item.get("commentary") or "",
            }
            for item in draft.get("chesta_bala_commentary") or []
            if not is_moon_transit(item.get("planet"))
        ],
        "recommendations": draft.get("recommendations") or "",
        "email_subject": draft.get("email_subject") or "",
        "email_preheader": draft.get("email_preheader") or "",
        "email_body": draft.get("email_body") or "",
    }


def resend_email_payload(draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "month": str(draft.get("month") or "").strip(),
        "moon_sign": str(draft.get("moon_sign") or "").strip(),
        "email_subject": str(draft.get("email_subject") or "").strip(),
        "email_preheader": str(draft.get("email_preheader") or "").strip(),
        "email_body": str(draft.get("email_body") or "").strip(),
        "language": "es",
    }


def can_push_resend_draft(draft: dict[str, Any] | None) -> bool:
    if not draft:
        return False
    payload = resend_email_payload(draft)
    return bool(payload["email_body"] and payload["moon_sign"])


def gemini_brief(
    facts: dict[str, Any],
    rules: list[dict[str, Any]],
    include_interval_keys: list[str] | None,
    include_rule_keys: list[str] | None,
) -> dict[str, Any]:
    selected_facts = filter_facts(facts, include_interval_keys)
    selected_rules = filter_rules(rules, include_rule_keys)
    ranges = included_interval_rows(facts, rules, include_interval_keys)
    return {
        "locale": "es",
        "month": month_label(facts),
        "moon_sign": moon_sign(facts),
        "calculated_facts": selected_facts,
        "retrieved_rules": selected_rules,
        "transit_ranges": ranges,
        "chesta_bala": {
            "status": "on",
            "note": (
                "Write chesta_bala_commentary for every classified planet. "
                "Use retrieved Ceṣṭā Bala / Gati notes. "
                "Use only classified gati / virūpa already present on transit ranges. "
                "Do not invent commentary."
            ),
            "classifications": chesta_rows(facts),
            "notes": chesta_note_rows(selected_rules),
        },
        "counts": {
            "transit_ranges": len(ranges),
            "rag_notes": retrieved_rule_count(selected_rules),
            "all_transit_ranges": interval_count(facts),
            "all_rag_notes": retrieved_rule_count(rules),
        },
    }


def generate_request(
    facts: dict[str, Any],
    rules: list[dict[str, Any]] | None,
    include_interval_keys: list[str] | None,
    include_rule_keys: list[str] | None,
) -> dict[str, Any]:
    brief = gemini_brief(facts, rules or [], include_interval_keys, include_rule_keys)
    return {
        "calculated_facts": brief["calculated_facts"],
        "retrieved_rules": merge_chesta_rules(rules or [], brief["retrieved_rules"]),
        "locale": "es",
    }


def studio_readiness(
    facts: dict[str, Any] | None,
    rules: list[dict[str, Any]] | None,
    include_interval_keys: list[str] | None,
    include_rule_keys: list[str] | None,
) -> dict[str, Any]:
    rules = rules or []
    brief = gemini_brief(facts, rules, include_interval_keys, include_rule_keys) if facts else None
    selected_ranges = brief["counts"]["transit_ranges"] if brief else 0
    return {
        "has_facts": bool(facts),
        "has_rules": retrieved_rule_count(rules) > 0,
        "can_generate": bool(facts) and selected_ranges > 0,
        "month": month_label(facts),
        "moon_sign": moon_sign(facts),
        "selected_ranges": selected_ranges,
        "selected_rag": brief["counts"]["rag_notes"] if brief else 0,
        "chesta_status": "on",
    }


def draft_markdown(draft: dict[str, Any]) -> str:
    lines = [
        f"# {draft.get('title') or 'Informe mensual'}",
        "",
        f"**Mes:** {draft.get('month') or '—'}",
        f"**Luna:** {draft.get('moon_sign') or '—'}",
        "",
        "## Overview",
        draft.get("overview") or "—",
        "",
        "## Tránsitos mayores",
    ]
    for item in draft.get("major_transits") or []:
        lines.extend(
            [
                "",
                f"### {item.get('planet') or '—'}",
                f"*{item.get('period') or ''}*",
                "",
                f"**{item.get('title') or ''}**",
                "",
                item.get("interpretation") or "—",
            ]
        )
    lines.extend(["", "## Ceṣṭā Bala", ""])
    commentary = [
        item
        for item in draft.get("chesta_bala_commentary") or []
        if item.get("commentary")
    ]
    if commentary:
        for item in commentary:
            lines.extend([f"**{item.get('planet')}**", "", item.get("commentary") or "", ""])
    else:
        lines.append("_Sin comentario de Ceṣṭā Bala en este borrador._")
        lines.append("")
    lines.extend(
        [
            "## Recomendaciones",
            draft.get("recommendations") or "—",
            "",
            "## Email",
            f"**Asunto:** {draft.get('email_subject') or '—'}",
            f"**Preheader:** {draft.get('email_preheader') or '—'}",
            "",
            draft.get("email_body") or "—",
        ]
    )
    return "\n".join(lines)
