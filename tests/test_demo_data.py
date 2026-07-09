# ABOUTME: Runs the real pipeline over the shipped demo dataset and asserts the planted
# ABOUTME: story holds - so the demo and the pipeline can never drift apart silently.
from pathlib import Path

from parse_clarity import parse_clarity_csv
from attribute import attribute

DEMO_DIR = Path(__file__).parent.parent / "plugins" / "plate-to-peak" / "assets" / "demo"

DEMO_MEALS = [
    {"time": "2026-06-01T07:45:00", "food": "white toast with jam, orange juice"},
    {"time": "2026-06-01T12:30:00", "food": "chicken salad with olive oil"},
    {"time": "2026-06-01T16:00:00", "food": "banana & mango smoothie"},
    {"time": "2026-06-01T19:30:00", "food": "spaghetti bolognese"},
    {"time": "2026-06-02T08:00:00", "food": "scrambled eggs, avocado, rye toast"},
    {"time": "2026-06-02T13:00:00", "food": "porridge with honey"},
    {"time": "2026-06-02T20:15:00", "food": "grilled salmon, greens"},
    {"time": "2026-06-03T08:15:00", "food": "greek yogurt with berries"},
    {"time": "2026-06-03T12:45:00", "food": "sweet & sour chicken with white rice"},
    {"time": "2026-06-03T17:30:00", "food": "apple with peanut butter"},
    {"time": "2026-06-03T19:45:00", "food": "lentil dahl, wholegrain flatbread"},
]

# The planted story: food -> (spiked, notable_rise)
EXPECTED = {
    "white toast with jam, orange juice": (True, False),
    "chicken salad with olive oil": (False, False),
    "banana & mango smoothie": (True, False),
    "spaghetti bolognese": (True, False),
    "scrambled eggs, avocado, rye toast": (False, False),
    "porridge with honey": (False, True),
    "grilled salmon, greens": (False, False),
    "greek yogurt with berries": (False, False),
    "sweet & sour chicken with white rice": (True, False),
    "apple with peanut butter": (False, False),
    "lentil dahl, wholegrain flatbread": (False, True),
}


def run_pipeline():
    parsed = parse_clarity_csv(str(DEMO_DIR / "demo-clarity-export.csv"))
    return parsed, attribute(parsed["readings"], DEMO_MEALS, threshold=7.8)


def test_demo_csv_parses_clean():
    parsed, _ = run_pipeline()
    assert parsed["unit"] == "mmol/L"
    assert len(parsed["readings"]) == 864  # 3 days at 5-min cadence
    assert parsed["gaps"] == []


def test_demo_patient_metadata_is_synthetic_and_ignored():
    parsed, _ = run_pipeline()
    assert "Demo" not in str(parsed) and "Persona" not in str(parsed)


def test_demo_story_verdicts_hold():
    _, attr = run_pipeline()
    for m in attr["meals"]:
        want_spiked, want_notable = EXPECTED[m["food"]]
        assert m["spiked"] is want_spiked, f'{m["food"]}: spiked={m["spiked"]}, want {want_spiked}'
        assert m["notable_rise"] is want_notable, (
            f'{m["food"]}: notable_rise={m["notable_rise"]}, want {want_notable}')


def test_demo_has_exactly_one_orphan_the_gym_spike():
    _, attr = run_pipeline()
    assert len(attr["orphans"]) == 1
    o = attr["orphans"][0]
    assert o["time"].startswith("2026-06-02T18") or o["time"].startswith("2026-06-02T19")
    assert o["mmol"] >= 7.8


def test_demo_biggest_spike_is_the_white_rice():
    _, attr = run_pipeline()
    top = max((m for m in attr["meals"] if m["peak"]), key=lambda m: m["peak"])
    assert top["food"] == "sweet & sour chicken with white rice"
