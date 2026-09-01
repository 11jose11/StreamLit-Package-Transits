from __future__ import annotations

from flatten import (
    flatten_events,
    flatten_intervals,
    flatten_rules,
    interval_count,
    retrieved_rule_count,
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
                    "degree_start": 12.54321,
                    "direction": "direct",
                    "speed_longitude": 0.123456,
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
            "planet": "Mercury",
            "event_type": "sign_ingress",
            "from_sign": "Virgo",
            "to_sign": "Libra",
        }
    ],
}


def test_flatten_intervals_formats_rows() -> None:
    rows = flatten_intervals(FACTS)
    assert len(rows) == 2
    jupiter = rows[0]
    assert jupiter["Planet"] == "Jupiter"
    assert jupiter["Sign"] == "Cancer"
    assert jupiter["House from Moon"] == 4
    assert jupiter["Degree"] == 12.5432
    assert jupiter["Gati"] == "Sama"
    assert jupiter["Gati status"] == "classified"
    assert jupiter["Ceṣṭā Bala (virūpa)"] == "7.5"
    assert jupiter["RAG meaning"] == "—"
    mars = rows[1]
    assert mars["Gati"] == "Śīghra"
    assert mars["Ceṣṭā Bala (virūpa)"] == "45"


def test_flatten_not_applicable_gati() -> None:
    rows = flatten_intervals(
        {
            "planets": [
                {
                    "planet": "Sun",
                    "intervals": [
                        {
                            "start": "2026-10-01T00:00:00Z",
                            "end": "2026-10-31T23:59:00Z",
                            "sign": "Virgo",
                            "house_from_moon": 6,
                            "degree_start": 10.0,
                            "direction": "direct",
                            "speed_longitude": 0.98,
                            "gati": None,
                            "gati_status": "not_applicable",
                            "chesta_bala_virupa": None,
                        }
                    ],
                }
            ]
        }
    )
    assert rows[0]["Gati"] == "—"
    assert rows[0]["Gati status"] == "n/a"
    assert rows[0]["Ceṣṭā Bala (virūpa)"] == "—"
    assert rows[0]["RAG meaning"] == "—"


def test_flatten_events() -> None:
    rows = flatten_events(FACTS)
    assert rows == [
        {
            "Date": "2026-10-10T08:00:00Z",
            "Planet": "Mercury",
            "Event": "sign_ingress",
            "From": "Virgo",
            "To": "Libra",
        }
    ]


def test_flatten_events_empty() -> None:
    assert flatten_events({"events": []}) == []


def test_flatten_rules_none_and_preview() -> None:
    rules = [
        {
            "planet": "Jupiter",
            "fact": {"house_from_moon": 4},
            "retrieved_rules": [],
        },
        {
            "planet": "Mars",
            "fact": {"house_from_moon": 5, "gati": "sighra", "sign": "Leo", "direction": "direct"},
            "retrieved_rules": [
                {
                    "content": "x" * 410,
                    "source": "Brihat Parashara",
                    "score": 0.87654,
                }
            ],
        },
    ]
    rows = flatten_rules(rules)
    assert rows[0]["Retrieved rule"] == "(none)"
    assert rows[1]["Retrieved rule"].endswith("…")
    assert len(rows[1]["Retrieved rule"]) == 401
    assert rows[1]["Similarity score"] == "0.8765"
    assert rows[1]["Gati"] == "Śīghra"
    assert retrieved_rule_count(rules) == 1


def test_flatten_intervals_applies_rag_meaning() -> None:
    rules = [
        {
            "planet": "Jupiter",
            "fact": {"house_from_moon": 4, "gati": "sama"},
            "retrieved_rules": [
                {
                    "content": "### Tránsito en la Casa 4\nPhaladeepika: Aumento de la felicidad."
                }
            ],
        }
    ]
    rows = flatten_intervals(FACTS, rules)
    assert "Phaladeepika" in rows[0]["RAG meaning"]
    assert rows[1]["RAG meaning"] == "—"


def test_interval_count() -> None:
    assert interval_count(None) == 0
    assert interval_count(FACTS) == 2


def test_flatten_skips_moon_from_moon() -> None:
    facts = {
        **FACTS,
        "planets": [
            *FACTS["planets"],
            {
                "planet": "Moon",
                "intervals": [
                    {
                        "start": "2026-10-01T00:00:00Z",
                        "end": "2026-10-02T00:00:00Z",
                        "sign": "Aries",
                        "house_from_moon": 1,
                    }
                ],
            },
        ],
        "events": [
            *FACTS["events"],
            {"datetime_utc": "2026-10-03T00:00:00Z", "planet": "Moon", "event_type": "sign_ingress"},
        ],
    }
    assert interval_count(facts) == 2
    assert [row["Planet"] for row in flatten_intervals(facts)] == ["Jupiter", "Mars"]
    assert [row["Planet"] for row in flatten_events(facts)] == ["Mercury"]
    assert flatten_rules([{"planet": "Moon", "fact": {}, "retrieved_rules": []}]) == []
