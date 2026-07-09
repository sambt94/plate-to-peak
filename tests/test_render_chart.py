# ABOUTME: Tests for the static-SVG chart renderer - full-resolution line, peak inclusion,
# ABOUTME: dot colours, orphan markers, gap splitting, and HTML escaping of food names.
import pytest
from render_chart import build_svg, build_html

PAYLOAD = {
    "startISO": "2026-06-01T08:00:00",
    "threshold": 7.8,
    "series": [
        {"x": 0, "mmol": 5.0}, {"x": 5, "mmol": 5.2}, {"x": 10, "mmol": 6.1},
        {"x": 15, "mmol": 9.6}, {"x": 20, "mmol": 8.0}, {"x": 25, "mmol": 6.0},
        # gap between x=25 and x=60
        {"x": 60, "mmol": 5.5}, {"x": 65, "mmol": 5.4}, {"x": 70, "mmol": 5.3},
    ],
    "gaps": [{"x1": 25, "x2": 60}],
    "meals": [
        {"x": 2, "food": "toast & jam <special>", "peak": 9.6, "delta": 4.6,
         "spiked": True, "notableRise": False, "status": "ok"},
        {"x": 62, "food": "eggs", "peak": 5.5, "delta": 0.1,
         "spiked": False, "notableRise": False, "status": "ok"},
        {"x": -30, "food": "pre-window meal", "peak": None, "delta": None,
         "spiked": False, "notableRise": False, "status": "insufficient_data"},
    ],
    "orphans": [{"x": 15, "mmol": 9.6}],
}


def test_every_reading_is_a_polyline_vertex():
    svg = build_svg(PAYLOAD)
    # 9 readings split by one gap -> two polylines with 6 + 3 vertices
    import re
    polys = re.findall(r'<polyline points="([^"]+)"', svg)
    assert len(polys) == 2
    counts = [len(p.split()) for p in polys]
    assert counts == [6, 3]


def test_peak_value_maps_to_highest_line_vertex():
    svg = build_svg(PAYLOAD)
    import re
    pts = [pt for poly in re.findall(r'<polyline points="([^"]+)"', svg) for pt in poly.split()]
    ys = [float(pt.split(",")[1]) for pt in pts]
    # smallest y (SVG is top-down) must belong to the 9.6 reading, above the threshold line
    thr_y = float(re.search(r'stroke-dasharray="4 4"/>', svg) and
                  re.search(r'<line x1="\d+" y1="([\d.]+)".*stroke-dasharray="4 4"', svg).group(1))
    assert min(ys) < thr_y


def test_meal_dot_colours_and_tooltips():
    svg = build_svg(PAYLOAD)
    assert '#c4553b' in svg  # spiked red dot
    assert '#6e8b5b' in svg  # calm green dot
    assert 'toast &amp; jam &lt;special&gt;' in svg  # food escaped into the tooltip
    assert 'peak 9.6 mmol/L' in svg


def test_pre_window_and_insufficient_meals_not_drawn():
    svg = build_svg(PAYLOAD)
    assert 'pre-window meal' not in svg


def test_orphan_marker_present_and_dashed():
    svg = build_svg(PAYLOAD)
    assert 'Unexplained spike - 9.6 mmol/L' in svg
    assert 'stroke-dasharray="2 2"' in svg


def test_gap_renders_shading_not_line():
    svg = build_svg(PAYLOAD)
    assert 'opacity="0.7"' in svg  # gap rect present


def test_html_is_self_contained():
    html = build_html(PAYLOAD)
    assert html.startswith("<!doctype html>")
    assert "<script" not in html  # no JS at all
    assert "Plate to Peak" in html


def test_empty_series_raises():
    with pytest.raises(ValueError, match="no series"):
        build_svg({"startISO": "2026-06-01T08:00:00", "threshold": 7.8,
                   "series": [], "gaps": [], "meals": [], "orphans": []})
