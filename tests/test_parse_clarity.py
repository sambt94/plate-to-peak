# ABOUTME: Tests for the Dexcom Clarity CSV parser against a synthetic byte-faithful fixture.
# ABOUTME: Covers BOM, metadata filtering, Low/High sentinels, unit detection, gap detection.
from pathlib import Path

import pytest
from parse_clarity import parse_clarity_csv

FIXTURE = str(Path(__file__).parent / "fixtures" / "synthetic_clarity.csv")


def test_filters_to_egv_rows_only():
    out = parse_clarity_csv(FIXTURE)
    assert len(out["readings"]) == 9  # 9 EGV rows; 5 metadata rows dropped


def test_patient_info_never_in_output():
    out = parse_clarity_csv(FIXTURE)
    assert "Testa" not in str(out) and "Persona" not in str(out) and "1990-01-01" not in str(out)


def test_detects_mmol_unit_from_header():
    assert parse_clarity_csv(FIXTURE)["unit"] == "mmol/L"


def test_readings_sorted_with_time_and_value():
    out = parse_clarity_csv(FIXTURE)
    first = out["readings"][0]
    assert first == {"t": "2026-06-01T11:18:03", "mmol": 5.4}
    ts = [r["t"] for r in out["readings"]]
    assert ts == sorted(ts)


def test_low_sentinel_maps_to_2_1():
    out = parse_clarity_csv(FIXTURE)
    lows = [r for r in out["readings"] if r["t"].startswith("2026-06-01T12:2")]
    assert [r["mmol"] for r in lows] == [2.1, 2.1]


def test_gap_detected_between_1133_and_1213():
    out = parse_clarity_csv(FIXTURE)
    assert out["gaps"] == [{"start": "2026-06-01T11:33:03", "end": "2026-06-01T12:13:03"}]


def test_mg_dl_converts(tmp_path):
    p = tmp_path / "us.csv"
    p.write_text(
        '"Index","Timestamp (YYYY-MM-DDThh:mm:ss)","Event Type","Event Subtype","Patient Info",'
        '"Device Info","Source Device ID","Glucose Value (mg/dL)","Insulin Value (u)",'
        '"Carb Value (grams)","Duration (hh:mm:ss)","Glucose Rate of Change (mg/dL/min)",'
        '"Transmitter Time (Long Integer)","Transmitter ID"\n'
        '"1","2026-06-01T08:00:00","EGV","","","","iOS G7","108","","","","","100","1"\n',
        encoding="utf-8",
    )
    out = parse_clarity_csv(str(p))
    assert out["unit"] == "mg/dL"
    assert out["readings"][0]["mmol"] == 6.0  # 108 / 18


def test_unrecognised_header_raises():
    import tempfile, os
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("a,b,c\n1,2,3\n")
    try:
        with pytest.raises(ValueError, match="Clarity"):
            parse_clarity_csv(f.name)
    finally:
        os.unlink(f.name)
