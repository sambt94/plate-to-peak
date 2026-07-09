// ABOUTME: Artifact template for the Plate to Peak chart - meal dots on a glucose trend line.
// ABOUTME: Self-contained: trend/band math inlined (port of phase2-trend.ts); DATA is injected.
// The map-spikes skill replaces DATA with the build_payload JSON, then renders this as an artifact.
import React from 'react';
import {
  ComposedChart, Line, Area, Scatter, XAxis, YAxis, Tooltip,
  ReferenceLine, ReferenceArea, ResponsiveContainer,
} from 'recharts';

const DATA = /*__PAYLOAD__*/ { startISO: '', threshold: 7.8, series: [], gaps: [], meals: [], orphans: [] };

// Warm-bone palette (phase2-theme.ts, sambt.dev)
const C = {
  bone: '#f2eee4', card: '#fbf9f4', border: '#e6e0d0', hair: '#efe9dc',
  ink: '#2a2622', muted: '#6b6355', faint: '#8a8070', key: '#a89f8c',
  amber: '#d8971e', green: '#6e8b5b', red: '#c4553b', blue: '#4a7c8c',
};
const MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace";

// TREND-MATH-START
// Port of phase2-trend.ts (sambt.dev). Scale factors map (minutes, mmol) into a
// common distance space so the Douglas-Peucker tolerance is meaningful across both axes.
const SX = 277 / 1440;
const SY = 34;
const EPS = 26;
const STEP = 30; // band sample spacing, minutes
const HALF = 45; // half-window for the rolling band, minutes

function perpDistance(p, a, b) {
  const ax = a.x * SX, ay = a.mmol * SY;
  const bx = b.x * SX, by = b.mmol * SY;
  const px = p.x * SX, py = p.mmol * SY;
  const dx = bx - ax, dy = by - ay;
  const norm = Math.hypot(dx, dy) || 1e-9;
  return Math.abs(dy * px - dx * py + bx * ay - by * ax) / norm;
}

function simplifyTrend(series, eps = EPS) {
  if (series.length < 3) return series.slice();
  let dmax = 0, idx = 0;
  const last = series[series.length - 1];
  for (let i = 1; i < series.length - 1; i++) {
    const d = perpDistance(series[i], series[0], last);
    if (d > dmax) { dmax = d; idx = i; }
  }
  if (dmax > eps) {
    const left = simplifyTrend(series.slice(0, idx + 1), eps);
    const right = simplifyTrend(series.slice(idx), eps);
    return left.slice(0, -1).concat(right);
  }
  return [series[0], last];
}

function buildBand(series) {
  if (series.length === 0) return [];
  const xs = series.map((p) => p.x);
  const first = Math.floor(xs[0] / STEP) * STEP;
  const last = xs[xs.length - 1];
  const out = [];
  for (let c = first; c <= last; c += STEP) {
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < series.length; i++) {
      if (xs[i] < c - HALF) continue;
      if (xs[i] > c + HALF) break;
      const g = series[i].mmol;
      if (g < lo) lo = g;
      if (g > hi) hi = g;
    }
    if (hi >= lo) out.push({ x: c, band: [Math.round(lo * 10) / 10, Math.round(hi * 10) / 10] });
  }
  return out;
}

function buildChartData(series) {
  const band = buildBand(series);
  if (band.length === 0) return [];
  const trend = simplifyTrend(series);
  const rows = new Map();
  for (const b of band) rows.set(b.x, { x: b.x, band: b.band });
  for (const v of trend) {
    const existing = rows.get(v.x);
    if (existing) existing.mmol = v.mmol;
    else rows.set(v.x, { x: v.x, band: band[0].band, mmol: v.mmol });
  }
  const data = [...rows.values()].sort((a, b) => a.x - b.x);
  const bandXs = new Set(band.map((b) => b.x));
  let lastBand = band[0].band;
  for (const p of data) {
    if (bandXs.has(p.x)) lastBand = p.band;
    else p.band = lastBand;
  }
  return data;
}
// TREND-MATH-END

// --- Time helpers: x is minutes since DATA.startISO ---
const startMs = Date.parse(DATA.startISO);
const fmtClock = (x) => {
  const d = new Date(startMs + x * 60000);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};
const fmtDay = (x) => {
  const d = new Date(startMs + x * 60000);
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric' });
};

// Split the series at gaps so the trend never bridges a data hole. Each segment
// gets its own mmol key (mmol0, mmol1, ...) so its Line can connectNulls through
// the sparse trend vertices without bridging across the gap to the next segment.
function chartRows() {
  const cuts = [0, ...DATA.gaps.map((g) => g.x2)];
  const segments = cuts.map((start, i) => {
    const end = DATA.gaps[i] ? DATA.gaps[i].x1 : Infinity;
    return DATA.series.filter((p) => p.x >= start && p.x <= end);
  }).filter((s) => s.length > 1);
  const rows = [];
  segments.forEach((seg, i) => {
    if (i > 0) rows.push({ x: seg[0].x - 1 }); // bandless row breaks the Area across the gap
    for (const r of buildChartData(seg)) {
      const row = { x: r.x, band: r.band };
      if (r.mmol != null) row[`mmol${i}`] = r.mmol;
      rows.push(row);
    }
  });
  return { rows, segmentCount: segments.length };
}

// Day ticks at each midnight-noon within the x range.
function dayTicks() {
  const lastX = DATA.series.length ? DATA.series[DATA.series.length - 1].x : 0;
  const ticks = [];
  const start = new Date(startMs);
  const firstNoon = new Date(start); firstNoon.setHours(12, 0, 0, 0);
  let t = (firstNoon - startMs) / 60000;
  if (t < 0) t += 1440;
  for (; t <= lastX; t += 1440) ticks.push(Math.round(t));
  return ticks;
}

function MealDot(props) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null) return null;
  const fill = payload.spiked ? C.red : payload.notableRise ? C.amber : C.key;
  return <circle cx={cx} cy={cy} r={6} fill={fill} stroke={C.card} strokeWidth={2} />;
}

function OrphanDot(props) {
  const { cx, cy } = props;
  if (cx == null || cy == null) return null;
  return <circle cx={cx} cy={cy} r={5} fill="none" stroke={C.amber} strokeWidth={2} strokeDasharray="2 2" />;
}

function MealTip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const m = payload.find((p) => p.payload?.food)?.payload;
  const o = payload.find((p) => p.payload?.orphan)?.payload;
  if (!m && o) {
    return (
      <div style={{ background: C.card, border: `1px solid ${C.border}`, padding: 10,
                    fontFamily: MONO, fontSize: 12, color: C.ink, maxWidth: 220 }}>
        <div style={{ color: C.muted }}>{fmtDay(o.x)} {fmtClock(o.x)}</div>
        <div style={{ fontWeight: 600, margin: '4px 0' }}>unexplained spike</div>
        <div>peak {o.mmol} mmol/L - nothing logged before it</div>
      </div>
    );
  }
  if (!m) return null;
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, padding: 10,
                  fontFamily: MONO, fontSize: 12, color: C.ink, maxWidth: 220 }}>
      <div style={{ color: C.muted }}>{fmtDay(m.x)} {fmtClock(m.x)}</div>
      <div style={{ fontWeight: 600, margin: '4px 0' }}>{m.food}</div>
      {m.status === 'insufficient_data'
        ? <div style={{ color: C.faint }}>sensor gap - no verdict</div>
        : <>
            <div>peak {m.peak} mmol/L{m.spiked ? ' - over threshold' : ''}</div>
            {m.delta != null && <div style={{ color: C.muted }}>+{m.delta} from baseline</div>}
            {m.status === 'ambiguous' && <div style={{ color: C.faint }}>shared window - see notes</div>}
          </>}
    </div>
  );
}

export default function PlateToPeakChart() {
  const { rows, segmentCount } = chartRows();
  const yFor = (x) => {
    let best = null, bd = Infinity;
    for (const p of DATA.series) {
      const d = Math.abs(p.x - x);
      if (d < bd) { bd = d; best = p; }
    }
    return best ? best.mmol : null;
  };
  // Meals timestamped before the sensor window (negative x) are reported in the
  // text readout but not drawn - a Scatter point would stretch the axis, not clip.
  const mealPoints = DATA.meals.filter((m) => m.x >= 0).map((m) => ({ ...m, mmol: yFor(m.x) }));
  const orphanPoints = DATA.orphans.map((o) => ({ ...o, orphan: true }));
  return (
    <div style={{ background: C.bone, padding: 24, fontFamily: MONO }}>
      <h2 style={{ color: C.ink, fontSize: 16, margin: '0 0 4px' }}>Plate to Peak</h2>
      <div style={{ color: C.muted, fontSize: 12, marginBottom: 16 }}>
        glucose vs meals - red dots crossed {DATA.threshold} mmol/L, amber rose sharply under it, dashed circles are unexplained spikes
      </div>
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <XAxis dataKey="x" type="number" domain={['dataMin', 'dataMax']} ticks={dayTicks()}
                 tickFormatter={fmtDay} stroke={C.key} fontSize={11} />
          <YAxis domain={[2, 'auto']} stroke={C.key} fontSize={11}
                 label={{ value: 'mmol/L', angle: -90, position: 'insideLeft', fill: C.muted, fontSize: 11 }} />
          {DATA.gaps.map((g, i) => (
            <ReferenceArea key={i} x1={g.x1} x2={g.x2} fill={C.hair} fillOpacity={0.6}
                           label={{ value: 'no data', fill: C.faint, fontSize: 10 }} />
          ))}
          <ReferenceLine y={DATA.threshold} stroke={C.red} strokeDasharray="4 4"
                         label={{ value: `${DATA.threshold}`, fill: C.red, fontSize: 11, position: 'right' }} />
          <Area dataKey="band" fill={C.border} stroke="none" connectNulls={false} isAnimationActive={false} />
          {Array.from({ length: segmentCount }, (_, i) => (
            <Line key={i} dataKey={`mmol${i}`} type="monotone" stroke={C.ink} strokeWidth={1.5}
                  dot={false} connectNulls isAnimationActive={false} />
          ))}
          <Scatter data={mealPoints} dataKey="mmol" shape={<MealDot />} isAnimationActive={false} />
          <Scatter data={orphanPoints} dataKey="mmol" shape={<OrphanDot />} isAnimationActive={false} />
          <Tooltip content={<MealTip />} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
