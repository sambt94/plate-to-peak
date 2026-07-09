# ABOUTME: Tests for deterministic spike attribution: baseline, peak, delta, spiked, notable rise,
# ABOUTME: overlapping-meal ambiguity, and insufficient-data verdicts on gapped windows.
from datetime import datetime, timedelta

from attribute import attribute

FMT = "%Y-%m-%dT%H:%M:%S"


def series(start="2026-06-01T08:00:00", *mmols, step_min=5):
    """5-min-cadence readings from start, one per value."""
    t0 = datetime.strptime(start, FMT)
    return [
        {"t": (t0 + timedelta(minutes=i * step_min)).strftime(FMT), "mmol": v}
        for i, v in enumerate(mmols)
    ]


def flat_then_spike():
    # 08:00-09:00 flat 5.0; meal at 09:00; rise from 09:20, peak 9.6 at 09:45, back down by 10:30
    vals = [5.0] * 13 + [5.1, 5.2, 5.3, 5.5, 5.8, 6.1, 7.4, 8.8, 9.6, 9.1, 8.0, 6.9, 6.0, 5.4, 5.1]
    return series("2026-06-01T08:00:00", *vals)


def test_clean_spike_attributed():
    out = attribute(flat_then_spike(), [{"time": "2026-06-01T09:00:00", "food": "croissant"}])
    m = out["meals"][0]
    assert m["status"] == "ok"
    assert m["spiked"] is True
    assert m["peak"] == 9.6
    assert m["peak_time"] == "2026-06-01T09:45:00"
    assert m["baseline"] == 5.0
    assert m["delta"] == 4.6
    assert m["notable_rise"] is False  # spiked outranks notable_rise


def test_notable_rise_under_threshold():
    vals = [4.5] * 13 + [5.0, 5.8, 6.5, 7.0, 7.2, 6.8, 6.0, 5.2, 4.8, 4.6, 4.5]
    out = attribute(
        series("2026-06-01T08:00:00", *vals),
        [{"time": "2026-06-01T09:00:00", "food": "oats"}],
    )
    m = out["meals"][0]
    assert m["spiked"] is False
    assert m["notable_rise"] is True  # delta 2.7 >= 2.0, peak 7.2 < 7.8
    assert m["delta"] == 2.7


def test_no_rise_is_quiet():
    out = attribute(
        series("2026-06-01T08:00:00", *([5.0] * 24)),
        [{"time": "2026-06-01T09:00:00", "food": "eggs"}],
    )
    m = out["meals"][0]
    assert m["spiked"] is False and m["notable_rise"] is False
    assert m["status"] == "ok"


def test_overlapping_meals_nearest_owns_peak():
    # Two meals 30 min apart; single peak lands in both windows -> later (nearer) meal owns it
    meals = [
        {"time": "2026-06-01T09:00:00", "food": "soup"},
        {"time": "2026-06-01T09:30:00", "food": "cake"},
    ]
    vals = [5.0] * 13 + [5.0, 5.0, 5.1, 5.3, 5.6, 6.4, 7.6, 8.9, 9.4, 8.8, 7.5, 6.4, 5.6, 5.2, 5.0, 5.0, 5.0, 5.0]
    out = attribute(series("2026-06-01T08:00:00", *vals), meals)
    soup, cake = out["meals"]
    assert cake["status"] == "ok" and cake["spiked"] is True
    assert soup["status"] == "ambiguous"


def test_meal_window_in_gap_is_insufficient_data():
    # readings end 09:10; meal 09:00 -> window [09:15, 10:30] has no readings
    out = attribute(
        series("2026-06-01T08:00:00", *([5.0] * 15)),
        [{"time": "2026-06-01T09:00:00", "food": "mystery"}],
    )
    m = out["meals"][0]
    assert m["status"] == "insufficient_data"
    assert m["spiked"] is False and m["peak"] is None and m["delta"] is None


def test_baseline_widens_to_30min_lookback():
    # No reading within 15 min before the meal, one at -25 min: baseline uses it
    readings = [{"t": "2026-06-01T08:35:00", "mmol": 5.5}] + [
        {"t": (datetime(2026, 6, 1, 9, 20) + timedelta(minutes=i * 5)).strftime(FMT), "mmol": v}
        for i, v in enumerate([6.0, 7.0, 8.5, 9.0, 8.1, 7.0, 6.2, 5.8, 5.5, 5.4, 5.3, 5.2, 5.1, 5.0])
    ]
    out = attribute(readings, [{"time": "2026-06-01T09:00:00", "food": "toast"}])
    assert out["meals"][0]["baseline"] == 5.5
