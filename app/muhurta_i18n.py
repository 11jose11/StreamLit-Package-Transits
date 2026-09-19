from __future__ import annotations

STRINGS = {
    "en": {
        "page_title": "Muhūrta Intelligence",
        "subtitle": "Find the strongest astrological windows for an important activity.",
        "language": "Language",
        "purpose": "Muhūrta type",
        "custom_purpose": "Custom purpose",
        "natal_nakshatra": "Natal Moon Nakṣatra (Tārābala)",
        "city": "City",
        "search_city": "Search city",
        "month": "Month",
        "year": "Year",
        "hours_range": "Practical hours (local time)",
        "hours_range_help": "Only search these hours. 6–18 means 06:00 to 18:59.",
        "hours_range_caption": "Searching {start:02d}:00 to {end:02d}:59",
        "preferred_hours": "Preferred hours inside the range (0–23)",
        "generate": "Find Muhūrtas",
        "interpret": "Explain selected window with Gemini",
        "view_data": "Astrological Data",
        "why_best": "Why this window",
        "strengths": "Strengths",
        "warnings": "Warnings",
        "hard_failures": "Hard failures",
        "score": "Score",
        "status": "Status",
        "advanced": "Advanced Settings",
        "step1": "STEP 1 — Search one month",
        "step2": "STEP 2 — Select a window and explain",
        "no_gemini_yet": "Select a candidate, then explain with Gemini.",
        "ready": "Top Muhūrtas ready. Ranking is deterministic. Gemini does not calculate.",
        "preparing": "Building the month profile and scanning windows...",
        "rank": "Rank",
        "window": "Time window",
        "lmt": "LMT",
        "lagna": "Lagna",
        "chandra_lagna": "Chandra Lagna",
        "hora": "Horā",
        "karaka": "Primary Kāraka",
        "tara": "Tārā",
        "sources": "Sources",
        "cautions": "Cautions",
        "recommendation": "Recommended exact window",
        "none": "none",
        "location_needed": "Search and select a city so latitude, longitude, and timezone are set.",
        "select_candidate": "Selected window",
        "go": "Go",
        "panchanga": "Pañcāṅga",
        "tithi": "Tithi",
        "vara": "Vāra",
        "nakshatra": "Nakṣatra",
        "karana": "Karaṇa",
        "yoga": "Yoga",
        "pada": "Pāda",
        "panchanga_notes": "Pañcāṅga notes",
        "planetary_notes": "Planetary notes",
        "natal_notes": "Natal compatibility",
        "flags": "Flags",
    },
    "es": {
        "page_title": "Muhūrta Intelligence",
        "subtitle": "Encuentra las ventanas astrológicas más sólidas para una actividad importante.",
        "language": "Idioma",
        "purpose": "Tipo de Muhūrta",
        "custom_purpose": "Propósito personalizado",
        "natal_nakshatra": "Nakṣatra lunar natal (Tārābala)",
        "city": "Ciudad",
        "search_city": "Buscar ciudad",
        "month": "Mes",
        "year": "Año",
        "hours_range": "Horario práctico (hora local)",
        "hours_range_help": "Solo busca entre estas horas. 6–18 significa de 06:00 a 18:59.",
        "hours_range_caption": "Buscar de {start:02d}:00 a {end:02d}:59",
        "preferred_hours": "Horas preferidas dentro del rango (0–23)",
        "generate": "Buscar Muhūrtas",
        "interpret": "Explicar la ventana seleccionada con Gemini",
        "view_data": "Datos astrológicos",
        "why_best": "Por qué esta ventana",
        "strengths": "Fortalezas",
        "warnings": "Advertencias",
        "hard_failures": "Fallos estructurales",
        "score": "Puntuación",
        "status": "Estado",
        "advanced": "Ajustes avanzados",
        "step1": "PASO 1 — Buscar un mes",
        "step2": "PASO 2 — Selecciona una ventana y explica",
        "no_gemini_yet": "Selecciona un candidato y luego explica con Gemini.",
        "ready": "Muhūrtas listas. El ranking es determinista. Gemini no calcula.",
        "preparing": "Armando el perfil del mes y recorriendo ventanas...",
        "rank": "Rango",
        "window": "Ventana horaria",
        "lmt": "LMT",
        "lagna": "Lagna",
        "chandra_lagna": "Chandra Lagna",
        "hora": "Horā",
        "karaka": "Kāraka principal",
        "tara": "Tārā",
        "sources": "Fuentes",
        "cautions": "Precauciones",
        "recommendation": "Ventana exacta recomendada",
        "none": "ninguno",
        "location_needed": "Busca y selecciona una ciudad para fijar latitud, longitud y zona horaria.",
        "select_candidate": "Ventana seleccionada",
        "go": "Buscar",
        "panchanga": "Pañcāṅga",
        "tithi": "Tithi",
        "vara": "Vāra",
        "nakshatra": "Nakṣatra",
        "karana": "Karaṇa",
        "yoga": "Yoga",
        "pada": "Pāda",
        "panchanga_notes": "Notas de Pañcāṅga",
        "planetary_notes": "Notas planetarias",
        "natal_notes": "Compatibilidad natal",
        "flags": "Marcas",
    },
}


def t(language: str, key: str) -> str:
    table = STRINGS["es"] if language.startswith("es") else STRINGS["en"]
    return table.get(key, key)


def tithi_label(panch: dict) -> str:
    name = (panch.get("tithi_name") or "").strip()
    if not name:
        raw = (panch.get("tithi_id") or "").split("_")[-1]
        name = raw.replace("_", " ").title() if raw else "—"
    paksha = (panch.get("paksha") or "").lower()
    if paksha == "shukla":
        return f"Śukla {name}"
    if paksha == "krishna":
        return f"Kṛṣṇa {name}"
    return name or "—"


def panchanga_flags(panch: dict) -> list[str]:
    flags: list[str] = []
    mapping = (
        ("is_amavasya", "Amāvasyā"),
        ("is_krishna_chaturdashi", "Kṛṣṇa Caturdaśī"),
        ("is_rikta", "Riktā"),
        ("is_ashtami", "Aṣṭamī"),
        ("is_visti", "Viṣṭi"),
        ("is_vaidhrti", "Vaidhṛti"),
        ("is_vyatipata", "Vyatipāta"),
    )
    for key, label in mapping:
        if panch.get(key):
            flags.append(label)
    return flags
