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
                    "gati": None,
                    "chesta_bala_virupa": None,
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
                    "gati": "Sheeghra",
                    "chesta_bala_virupa": 42.0,
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
    assert jupiter["Gati"] == "—"
    assert jupiter["Ceṣṭā Bala"] == "—"
    mars = rows[1]
    assert mars["Gati"] == "Sheeghra"
    assert mars["Ceṣṭā Bala"] == 42.0


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
            "fact": {"house_from_moon": 5},
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
    assert rows[1]["Similarity score"] == 0.8765
    assert retrieved_rule_count(rules) == 1


def test_interval_count() -> None:
    assert interval_count(None) == 0
    assert interval_count(FACTS) == 2
