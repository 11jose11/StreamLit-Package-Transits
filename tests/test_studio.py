from __future__ import annotations

from studio import (
    apply_gemini_report,
    default_interval_keys,
    default_rule_keys,
    filter_facts,
    filter_rules,
    generate_request,
    report_payload,
    seed_draft,
    studio_readiness,
)

FACTS = {
    "year": 2026,
    "month": 10,
    "reference": {"sign": "Aries"},
    "planets": [
        {
            "planet": "Jupiter",
            "intervals": [
                {
                    "start": "2026-10-01T00:00:00Z",
                    "end": "2026-10-31T23:59:00Z",
                    "sign": "Cancer",
                    "house_from_moon": 4,
                    "degree_start": 12.5,
                    "direction": "direct",
                    "speed_longitude": 0.12,
                    "gati": "sama",
                    "gati_status": "classified",
                    "chesta_bala_virupa": 7.5,
                }
            ],
        },
        {
            "planet": "Mars",
            "intervals": [
                {
                    "start": "2026-10-01T00:00:00Z",
                    "end": "2026-10-15T12:00:00Z",
                    "sign": "Leo",
                    "house_from_moon": 5,
                    "degree_start": 3.0,
                    "direction": "direct",
                    "speed_longitude": 0.5,
                    "gati": "sighra",
                    "gati_status": "classified",
                    "chesta_bala_virupa": 45.0,
                }
            ],
        },
    ],
    "events": [
        {
            "datetime_utc": "2026-10-10T08:00:00Z",
            "planet": "Mars",
            "event_type": "sign_ingress",
        }
    ],
}

RULES = [
    {
        "planet": "Jupiter",
        "fact": {"sign": "Cancer", "house_from_moon": 4, "direction": "direct", "gati": "sama"},
        "retrieved_rules": [
            {
                "content": "Jupiter in the 4th house increases comfort at home.",
                "source": "Phaladeepika",
            }
        ],
    },
    {
        "planet": "Mars",
        "fact": {"sign": "Leo", "house_from_moon": 5, "direction": "direct", "gati": "sighra"},
        "retrieved_rules": [
            {"content": "Mars in the 5th house heats creativity.", "source": "Phaladeepika"},
            {"content": "Śīghra Mars acts quickly.", "source": "Marte Chesta Bala"},
        ],
    },
]


def test_seed_draft_uses_ranges_and_rag() -> None:
    draft = seed_draft(FACTS, RULES, None)
    assert draft["month"] == "October 2026"
    assert draft["moon_sign"] == "Aries"
    assert draft["title"].startswith("Informe mensual")
    planets = [item["planet"] for item in draft["major_transits"]]
    assert planets == ["Jupiter", "Mars"]
    jupiter = draft["major_transits"][0]
    assert "Cancer" in jupiter["title"]
    assert "casa 4" in jupiter["title"]
    assert "comfort at home" in jupiter["interpretation"]
    assert "Nota RAG" in jupiter["working_notes"]
    chesta_planets = [item["planet"] for item in draft["chesta_bala_commentary"]]
    assert chesta_planets == ["Jupiter", "Mars"]
    mars_chesta = next(item for item in draft["chesta_bala_commentary"] if item["planet"] == "Mars")
    assert "Śīghra Mars acts quickly" in mars_chesta["commentary"]
    jupiter_chesta = next(
        item for item in draft["chesta_bala_commentary"] if item["planet"] == "Jupiter"
    )
    assert jupiter_chesta["commentary"] == ""


def test_filter_facts_keeps_selected_ranges_only() -> None:
    keys = default_interval_keys(FACTS)
    mars_only = filter_facts(FACTS, [keys[1]])
    assert [planet["planet"] for planet in mars_only["planets"]] == ["Mars"]
    assert mars_only["events"][0]["planet"] == "Mars"
    empty = filter_facts(FACTS, [])
    assert empty["planets"] == []
    assert empty["events"] == []


def test_filter_rules_keeps_selected_chunks() -> None:
    keys = default_rule_keys(RULES)
    assert len(keys) == 3
    selected = filter_rules(RULES, [keys[2]])
    assert len(selected) == 1
    assert selected[0]["planet"] == "Mars"
    assert selected[0]["retrieved_rules"] == [RULES[1]["retrieved_rules"][1]]


def test_generate_request_uses_selected_material() -> None:
    interval_keys = default_interval_keys(FACTS)
    rule_keys = default_rule_keys(RULES)
    payload = generate_request(FACTS, RULES, [interval_keys[0]], [rule_keys[0]])
    assert payload["locale"] == "es"
    assert [planet["planet"] for planet in payload["calculated_facts"]["planets"]] == ["Jupiter"]
    planets = [item["planet"] for item in payload["retrieved_rules"]]
    assert "Jupiter" in planets
    assert "Mars" in planets
    mars = next(item for item in payload["retrieved_rules"] if item["planet"] == "Mars")
    assert mars["retrieved_rules"] == [RULES[1]["retrieved_rules"][1]]


def test_apply_gemini_keeps_chesta_from_report() -> None:
    draft = seed_draft(FACTS, RULES, None)
    report = {
        "title": "Informe de octubre",
        "overview": "Mes de casa y fuego.",
        "major_transits": [
            {
                "planet": "Jupiter",
                "period": "octubre",
                "title": "Júpiter en Casa 4",
                "interpretation": "Más paz en casa.",
            }
        ],
        "chesta_bala_commentary": [{"planet": "Mars", "commentary": "invented"}],
        "recommendations": "Pausa.",
        "email_subject": "Octubre",
        "email_preheader": "Luna en Aries",
        "email_body": "Cuerpo",
    }
    merged = apply_gemini_report(draft, report)
    assert merged["title"] == "Informe de octubre"
    assert merged["overview"] == "Mes de casa y fuego."
    assert merged["major_transits"][0]["interpretation"] == "Más paz en casa."
    assert merged["major_transits"][0]["working_notes"]
    assert merged["chesta_bala_commentary"] == [{"planet": "Mars", "commentary": "invented"}]


def test_report_payload_keeps_chesta_entries() -> None:
    draft = seed_draft(FACTS, RULES, None)
    payload = report_payload(draft)
    assert [item["planet"] for item in payload["chesta_bala_commentary"]] == [
        "Jupiter",
        "Mars",
    ]
    assert payload["chesta_bala_commentary"][1]["commentary"]
    assert "working_notes" not in payload["major_transits"][0]


def test_readiness_requires_selected_ranges() -> None:
    ready = studio_readiness(FACTS, RULES, None, None)
    assert ready["can_generate"] is True
    assert ready["selected_ranges"] == 2
    assert ready["selected_rag"] == 3
    assert ready["chesta_status"] == "on"
    blocked = studio_readiness(FACTS, RULES, [], None)
    assert blocked["can_generate"] is False
