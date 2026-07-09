# ABOUTME: Tests for the chart payload builder - ISO timestamps to minutes-from-start,
# ABOUTME: meals/orphans/gaps carried through in the exact shape the artifact template consumes.
from chart_data import build_payload

PARSED = {
    "unit": "mmol/L",
    "readings": [
        {"t": "2026-06-01T08:00:00", "mmol": 5.0},
        {"t": "2026-06-01T08:05:00", "mmol": 5.2},
        {"t": "2026-06-01T09:00:00", "mmol": 9.1},
    ],
    "gaps": [{"start": "2026-06-01T08:05:00", "end": "2026-06-01T09:00:00"}],
}
ATTRIBUTION = {
    "meals": [
        {"time": "2026-06-01T08:10:00", "food": "toast", "status": "ok", "baseline": 5.0,
         "peak": 9.1, "peak_time": "2026-06-01T09:00:00", "delta": 4.1,
         "spiked": True, "notable_rise": False},
    ],
    "orphans": [{"time": "2026-06-01T09:00:00", "mmol": 9.1}],
}


def test_series_x_is_minutes_from_first_reading():
    p = build_payload(PARSED, ATTRIBUTION)
    assert p["startISO"] == "2026-06-01T08:00:00"
    assert [pt["x"] for pt in p["series"]] == [0, 5, 60]


def test_meal_marker_shape():
    p = build_payload(PARSED, ATTRIBUTION)
    assert p["meals"] == [{
        "x": 10, "food": "toast", "peak": 9.1, "delta": 4.1,
        "spiked": True, "notableRise": False, "status": "ok",
    }]


def test_gaps_and_orphans_in_minutes():
    p = build_payload(PARSED, ATTRIBUTION)
    assert p["gaps"] == [{"x1": 5, "x2": 60}]
    assert p["orphans"] == [{"x": 60, "mmol": 9.1}]


def test_threshold_default():
    assert build_payload(PARSED, ATTRIBUTION)["threshold"] == 7.8


def test_empty_readings_raises_clear_error():
    import pytest
    with pytest.raises(ValueError, match="no glucose readings"):
        build_payload({"unit": "mmol/L", "readings": [], "gaps": []},
                      {"meals": [], "orphans": []})


def test_meal_before_first_reading_gets_negative_x():
    # x is minutes from the first reading; a meal logged before the sensor
    # window is honestly negative (the chart clips it), never silently dropped.
    attribution = {
        "meals": [{"time": "2026-06-01T07:30:00", "food": "early toast", "status": "insufficient_data",
                   "baseline": None, "peak": None, "peak_time": None, "delta": None,
                   "spiked": False, "notable_rise": False}],
        "orphans": [],
    }
    p = build_payload(PARSED, attribution)
    assert p["meals"][0]["x"] == -30
