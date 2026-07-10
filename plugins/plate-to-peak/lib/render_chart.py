# ABOUTME: Renders the meal-to-spike chart as a self-contained HTML file with static inline SVG.
# ABOUTME: No React, no JS, no libraries - the full-resolution glucose line is baked in, so it
# ABOUTME: renders as plain markup anywhere and physically cannot miss a spike's peak.
import json
import sys
from datetime import datetime, timedelta

FMT = "%Y-%m-%dT%H:%M:%S"

# Warm-bone palette (phase2-theme.ts, sambt.dev)
C = {
    "bone": "#f2eee4", "card": "#fbf9f4", "border": "#e6e0d0", "hair": "#efe9dc",
    "ink": "#2a2622", "muted": "#6b6355", "faint": "#8a8070", "key": "#a89f8c",
    "amber": "#d8971e", "green": "#6e8b5b", "red": "#c4553b",
}
MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

# Plot geometry (SVG user units; the SVG scales responsively to its container).
W, H = 1000, 440
M = {"top": 16, "right": 20, "bottom": 34, "left": 40}
PW = W - M["left"] - M["right"]
PH = H - M["top"] - M["bottom"]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_svg(payload):
    series = payload["series"]
    if not series:
        raise ValueError("no series to chart")
    threshold = payload["threshold"]
    t0 = datetime.strptime(payload["startISO"], FMT)

    xs = [p["x"] for p in series]
    x_min, x_max = min(xs), max(xs)
    y_top = max([p["mmol"] for p in series] + [m["peak"] for m in payload["meals"] if m.get("peak")]
                + [threshold]) + 1
    y_bot = 2.0

    def sx(x):
        return M["left"] + (x - x_min) / (x_max - x_min or 1) * PW

    def sy(mmol):
        return M["top"] + (y_top - mmol) / (y_top - y_bot) * PH

    def nearest_mmol(x):
        best, bd = series[0]["mmol"], abs(series[0]["x"] - x)
        for p in series:
            d = abs(p["x"] - x)
            if d < bd:
                bd, best = d, p["mmol"]
        return best

    gaps = payload.get("gaps", [])

    # Full-resolution glucose line, split at data gaps so it never bridges a hole.
    cuts = [x_min] + [g["x2"] for g in gaps]
    polylines = []
    for i, start in enumerate(cuts):
        end = gaps[i]["x1"] if i < len(gaps) else x_max
        seg = [p for p in series if start <= p["x"] <= end]
        if len(seg) > 1:
            pts = " ".join(f"{sx(p['x']):.1f},{sy(p['mmol']):.1f}" for p in seg)
            polylines.append(
                f'<polyline points="{pts}" fill="none" stroke="{C["ink"]}" '
                f'stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round"/>'
            )

    parts = []

    # Gap shading
    for g in gaps:
        gx1, gx2 = sx(g["x1"]), sx(g["x2"])
        parts.append(f'<rect x="{gx1:.1f}" y="{M["top"]}" width="{gx2 - gx1:.1f}" '
                     f'height="{PH}" fill="{C["hair"]}" opacity="0.7"/>')

    # Day gridlines + labels (local midnights derived from startISO)
    start_min_of_day = t0.hour * 60 + t0.minute
    first_midnight = (1440 - start_min_of_day) % 1440
    d = first_midnight
    while d <= x_max:
        if d >= x_min:
            gx = sx(d)
            parts.append(f'<line x1="{gx:.1f}" y1="{M["top"]}" x2="{gx:.1f}" '
                         f'y2="{M["top"] + PH}" stroke="{C["hair"]}" stroke-width="1"/>')
        d += 1440
    # Day names at each day's noon
    noon = first_midnight - 720  # first noon may be before the first midnight
    while noon <= x_max:
        if noon >= x_min:
            label = (t0 + timedelta(minutes=noon)).strftime("%a %-d")
            parts.append(f'<text x="{sx(noon):.1f}" y="{H - 12}" text-anchor="middle" '
                         f'font-size="12" fill="{C["muted"]}" font-family="{MONO}">{label}</text>')
        noon += 1440

    # Y axis ticks + gridlines (every 2 mmol from 2 up)
    tick = 2
    while tick <= y_top:
        gy = sy(tick)
        parts.append(f'<text x="{M["left"] - 8}" y="{gy + 4:.1f}" text-anchor="end" '
                     f'font-size="11" fill="{C["key"]}" font-family="{MONO}">{tick}</text>')
        tick += 2

    # Threshold line
    ty = sy(threshold)
    parts.append(f'<line x1="{M["left"]}" y1="{ty:.1f}" x2="{M["left"] + PW}" y2="{ty:.1f}" '
                 f'stroke="{C["red"]}" stroke-width="1" stroke-dasharray="4 4"/>')
    parts.append(f'<text x="{M["left"] + PW}" y="{ty - 5:.1f}" text-anchor="end" font-size="11" '
                 f'fill="{C["red"]}" font-family="{MONO}">{threshold}</text>')

    # The glucose line
    parts.extend(polylines)

    # Orphan markers (unexplained spikes) - hollow dashed amber circles
    for o in payload.get("orphans", []):
        if o["x"] < x_min:
            continue
        ox, oy = sx(o["x"]), sy(o["mmol"])
        otip = f'Unexplained spike - {o["mmol"]} mmol/L, nothing logged before it'
        parts.append(
            f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="5.5" fill="none" stroke="{C["amber"]}" '
            f'stroke-width="2" stroke-dasharray="2 2" data-tip="{_esc(otip)}" style="cursor:pointer">'
            f'<title>{_esc(otip)}</title></circle>'
        )

    # Meal dots
    for m in payload["meals"]:
        if m["x"] < 0 or m.get("status") == "insufficient_data":
            continue
        mx, my = sx(m["x"]), sy(nearest_mmol(m["x"]))
        fill = C["red"] if m["spiked"] else (C["amber"] if m.get("notableRise") else C["green"])
        clock = (t0 + timedelta(minutes=m["x"])).strftime("%a %-d, %H:%M")
        peak = f'{m["peak"]}' if m.get("peak") is not None else "?"
        delta = f', +{m["delta"]} from baseline' if m.get("delta") is not None else ""
        tip = f'{clock} - {m["food"]} - peak {peak} mmol/L{delta}'
        parts.append(
            f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="5.5" fill="{fill}" stroke="{C["card"]}" '
            f'stroke-width="1.5" data-tip="{_esc(tip)}" style="cursor:pointer">'
            f'<title>{_esc(tip)}</title></circle>'
        )

    body = "\n".join(parts)
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
            f'style="max-width:960px;display:block">\n{body}\n</svg>')


def build_html(payload):
    svg = build_svg(payload)
    t0 = datetime.strptime(payload["startISO"], FMT)
    end = t0 + timedelta(minutes=max(p["x"] for p in payload["series"]))
    span = f'{t0.strftime("%-d %b")} - {end.strftime("%-d %b %Y")}'
    thr = payload["threshold"]
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Plate to Peak</title></head>
<body style="margin:0;background:{C['bone']};font-family:{MONO};color:{C['ink']}">
<div style="padding:22px 24px">
  <h2 style="font-size:16px;margin:0 0 4px">Plate to Peak</h2>
  <div style="color:{C['muted']};font-size:12px;margin-bottom:14px">
    glucose vs meals, {span}. Red dots crossed {thr} mmol/L, amber rose sharply under it,
    green stayed calm. Dashed circles are spikes with no meal logged. Hover any dot for detail.
  </div>
  {svg}
</div>
<div id="ptp-tip" style="position:fixed;z-index:9;pointer-events:none;display:none;
  background:{C['card']};border:1px solid {C['border']};color:{C['ink']};
  font-family:{MONO};font-size:12px;line-height:1.35;padding:8px 10px;max-width:280px;
  border-radius:4px;box-shadow:0 3px 12px rgba(42,38,34,.16)"></div>
<script>
(function(){{
  var svg=document.querySelector('svg'); var tip=document.getElementById('ptp-tip');
  if(!svg||!tip){{return;}}
  var dots=[].slice.call(svg.querySelectorAll('circle[data-tip]')).map(function(c){{
    return {{x:parseFloat(c.getAttribute('cx')),y:parseFloat(c.getAttribute('cy')),
            t:c.getAttribute('data-tip')}};
  }});
  var R2=22*22; // hover radius in SVG user units, squared
  function toUser(e){{
    var p=svg.createSVGPoint(); p.x=e.clientX; p.y=e.clientY;
    var m=svg.getScreenCTM(); if(!m){{return null;}}
    return p.matrixTransform(m.inverse());
  }}
  function move(e){{
    var u=toUser(e); if(!u){{return;}}
    var best=null, bd=R2;
    for(var i=0;i<dots.length;i++){{
      var dx=dots[i].x-u.x, dy=dots[i].y-u.y, d=dx*dx+dy*dy;
      if(d<bd){{bd=d; best=dots[i];}}
    }}
    if(best){{
      tip.textContent=best.t; tip.style.display='block';
      var vw=window.innerWidth, tw=tip.offsetWidth||220;
      var left=e.clientX+14; if(left+tw>vw-8){{left=e.clientX-tw-14;}}
      tip.style.left=left+'px'; tip.style.top=(e.clientY+16)+'px';
    }} else {{ tip.style.display='none'; }}
  }}
  svg.addEventListener('mousemove',move);
  svg.addEventListener('mouseleave',function(){{tip.style.display='none';}});
}})();
</script>
</body></html>"""


def _layout(payload):
    """Shared geometry: turns the payload into positioned SVG primitives (no colours)."""
    series = payload["series"]
    if not series:
        raise ValueError("no series to chart")
    threshold = payload["threshold"]
    t0 = datetime.strptime(payload["startISO"], FMT)
    xs = [p["x"] for p in series]
    x_min, x_max = min(xs), max(xs)
    y_top = max([p["mmol"] for p in series]
                + [m["peak"] for m in payload["meals"] if m.get("peak")] + [threshold]) + 1
    y_bot = 2.0

    def sx(x):
        return M["left"] + (x - x_min) / (x_max - x_min or 1) * PW

    def sy(mmol):
        return M["top"] + (y_top - mmol) / (y_top - y_bot) * PH

    def nearest_mmol(x):
        best, bd = series[0]["mmol"], abs(series[0]["x"] - x)
        for p in series:
            d = abs(p["x"] - x)
            if d < bd:
                bd, best = d, p["mmol"]
        return best

    gaps = payload.get("gaps", [])
    cuts = [x_min] + [g["x2"] for g in gaps]
    segments = []
    for i, start in enumerate(cuts):
        end = gaps[i]["x1"] if i < len(gaps) else x_max
        seg = [p for p in series if start <= p["x"] <= end]
        if len(seg) > 1:
            segments.append(" ".join(f"{sx(p['x']):.1f},{sy(p['mmol']):.1f}" for p in seg))

    gap_rects = [(sx(g["x1"]), sx(g["x2"]) - sx(g["x1"])) for g in gaps]

    start_min = t0.hour * 60 + t0.minute
    first_mid = (1440 - start_min) % 1440
    gridlines, d = [], first_mid
    while d <= x_max:
        if d >= x_min:
            gridlines.append(sx(d))
        d += 1440
    day_labels, noon = [], first_mid - 720
    while noon <= x_max:
        if noon >= x_min:
            day_labels.append((sx(noon), (t0 + timedelta(minutes=noon)).strftime("%a %-d")))
        noon += 1440

    y_ticks, tick = [], 2
    while tick <= y_top:
        y_ticks.append((tick, sy(tick)))
        tick += 2

    meals = []
    for m in payload["meals"]:
        if m["x"] < 0 or m.get("status") == "insufficient_data":
            continue
        role = "spiked" if m["spiked"] else ("notable" if m.get("notableRise") else "calm")
        clock = (t0 + timedelta(minutes=m["x"])).strftime("%a %-d, %H:%M")
        peak = f'{m["peak"]}' if m.get("peak") is not None else "?"
        delta = f', +{m["delta"]} from baseline' if m.get("delta") is not None else ""
        meals.append({"x": sx(m["x"]), "y": sy(nearest_mmol(m["x"])), "role": role,
                      "tip": f'{clock} - {m["food"]} - peak {peak} mmol/L{delta}'})
    orphans = [{"x": sx(o["x"]), "y": sy(o["mmol"]),
                "tip": f'Unexplained spike - {o["mmol"]} mmol/L, nothing logged before it'}
               for o in payload.get("orphans", []) if o["x"] >= x_min]

    return {"segments": segments, "gaps": gap_rects, "gridlines": gridlines,
            "day_labels": day_labels, "y_ticks": y_ticks,
            "threshold": threshold, "threshold_y": sy(threshold),
            "meals": meals, "orphans": orphans}


def build_widget(payload):
    """Theme-adaptive HTML fragment for the visualize show_widget tool (Cowork inline render).

    No <html>/<body>, no position:fixed, transparent surface, currentColor + mid-ramp colours
    that read in both light and dark mode. Same geometry as the standalone file.
    """
    g = _layout(payload)
    RED, AMBER, GREEN = "#E24B4A", "#EF9F27", "#639922"  # c-red/amber/green 400 - legible both modes
    dot_c = {"spiked": RED, "notable": AMBER, "calm": GREEN}
    p = []
    for gx, gw in g["gaps"]:
        p.append(f'<rect x="{gx:.1f}" y="{M["top"]}" width="{gw:.1f}" height="{PH}" '
                 f'fill="currentColor" opacity="0.06"/>')
    for gx in g["gridlines"]:
        p.append(f'<line x1="{gx:.1f}" y1="{M["top"]}" x2="{gx:.1f}" y2="{M["top"] + PH}" '
                 f'stroke="currentColor" stroke-opacity="0.12"/>')
    for label, gy in [(v, y) for v, y in g["y_ticks"]]:
        p.append(f'<text x="{M["left"] - 8}" y="{gy + 4:.1f}" text-anchor="end" font-size="11" '
                 f'fill="currentColor" fill-opacity="0.5">{label}</text>')
    for gx, label in g["day_labels"]:
        p.append(f'<text x="{gx:.1f}" y="{H - 12}" text-anchor="middle" font-size="12" '
                 f'fill="currentColor" fill-opacity="0.6">{label}</text>')
    ty = g["threshold_y"]
    p.append(f'<line x1="{M["left"]}" y1="{ty:.1f}" x2="{M["left"] + PW}" y2="{ty:.1f}" '
             f'stroke="{RED}" stroke-width="1" stroke-dasharray="4 4"/>')
    p.append(f'<text x="{M["left"] + PW}" y="{ty - 5:.1f}" text-anchor="end" font-size="11" '
             f'fill="{RED}">{g["threshold"]}</text>')
    for seg in g["segments"]:
        p.append(f'<polyline points="{seg}" fill="none" stroke="currentColor" stroke-width="1.4" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
    for o in g["orphans"]:
        p.append(f'<circle cx="{o["x"]:.1f}" cy="{o["y"]:.1f}" r="5.5" fill="none" stroke="{AMBER}" '
                 f'stroke-width="2" stroke-dasharray="2 2" data-tip="{_esc(o["tip"])}"/>')
    for m in g["meals"]:
        p.append(f'<circle cx="{m["x"]:.1f}" cy="{m["y"]:.1f}" r="5.5" fill="{dot_c[m["role"]]}" '
                 f'stroke="var(--surface-0)" stroke-width="1.5" data-tip="{_esc(m["tip"])}"/>')
    svg = (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
           f'style="display:block;overflow:visible">{"".join(p)}</svg>')
    thr = g["threshold"]
    return f"""<h2 class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden">Glucose over time with meal markers; red dots crossed {thr} mmol/L.</h2>
<div style="display:flex;gap:16px;font-size:12px;color:var(--text-secondary);margin:0 0 8px">
<span style="color:{RED}">● over {thr}</span><span style="color:{AMBER}">● sharp rise</span>
<span style="color:{GREEN}">● calm</span><span>◌ unexplained spike</span></div>
<div id="ptp-wrap" style="position:relative;color:var(--text-primary);font-family:var(--font-mono,ui-monospace,monospace)">
{svg}
<div id="ptp-tip" style="position:absolute;display:none;pointer-events:none;z-index:5;
background:var(--surface-3,var(--surface-2));border:0.5px solid var(--border);color:var(--text-primary);
font-size:12px;line-height:1.35;padding:7px 9px;max-width:260px;border-radius:8px"></div></div>
<script>
(function(){{
var wrap=document.getElementById('ptp-wrap');var svg=wrap.querySelector('svg');var tip=document.getElementById('ptp-tip');
var dots=[].slice.call(svg.querySelectorAll('circle[data-tip]')).map(function(c){{
return {{x:parseFloat(c.getAttribute('cx')),y:parseFloat(c.getAttribute('cy')),t:c.getAttribute('data-tip')}};}});
var R2=22*22;
svg.addEventListener('mousemove',function(e){{
var m=svg.getScreenCTM();if(!m)return;var pt=svg.createSVGPoint();pt.x=e.clientX;pt.y=e.clientY;
var u=pt.matrixTransform(m.inverse());var best=null,bd=R2;
for(var i=0;i<dots.length;i++){{var dx=dots[i].x-u.x,dy=dots[i].y-u.y,d=dx*dx+dy*dy;if(d<bd){{bd=d;best=dots[i];}}}}
if(best){{var wr=wrap.getBoundingClientRect();tip.textContent=best.t;tip.style.display='block';
var lx=e.clientX-wr.left+12;if(lx+tip.offsetWidth>wr.width)lx=e.clientX-wr.left-tip.offsetWidth-12;
tip.style.left=lx+'px';tip.style.top=(e.clientY-wr.top+14)+'px';}}else{{tip.style.display='none';}}}});
svg.addEventListener('mouseleave',function(){{tip.style.display='none';}});
}})();
</script>"""


if __name__ == "__main__":
    payload = json.load(open(sys.argv[1]))
    args = sys.argv[2:]
    widget = "--widget" in args
    outs = [a for a in args if not a.startswith("--")]
    content = build_widget(payload) if widget else build_html(payload)
    if outs:
        open(outs[0], "w").write(content)
        print(f"wrote {outs[0]}")
    else:
        sys.stdout.write(content)
