// ABOUTME: Tests the trend-math block inlined in chart-template.jsx (port of phase2-trend.ts).
// ABOUTME: Extracts the marked section and runs it - the artifact itself only renders in a browser.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const templatePath = join(
  dirname(fileURLToPath(import.meta.url)),
  '..', 'plugins', 'plate-to-peak', 'assets', 'chart-template.jsx',
);
const src = readFileSync(templatePath, 'utf8');
const block = src.split('// TREND-MATH-START')[1]?.split('// TREND-MATH-END')[0];
assert.ok(block, 'TREND-MATH markers missing from chart-template.jsx');
const { simplifyTrend, buildBand, buildChartData } = new Function(
  `${block}; return { simplifyTrend, buildBand, buildChartData };`,
)();

const flat = Array.from({ length: 40 }, (_, i) => ({ x: i * 5, mmol: 5.0 }));

test('simplifyTrend collapses a flat line to its endpoints', () => {
  const out = simplifyTrend(flat);
  assert.equal(out.length, 2);
});

test('simplifyTrend keeps a real spike vertex', () => {
  const spike = flat.map((p, i) => (i === 20 ? { x: p.x, mmol: 9.6 } : p));
  const out = simplifyTrend(spike);
  assert.ok(out.some((p) => p.mmol === 9.6), 'spike vertex dropped');
});

test('buildBand returns rolling [min,max] pairs', () => {
  const out = buildBand(flat);
  assert.ok(out.length > 0);
  for (const b of out) assert.deepEqual(b.band, [5, 5]);
});

test('buildChartData rows ascend and carry band everywhere', () => {
  const spike = flat.map((p, i) => (i === 20 ? { x: p.x, mmol: 9.6 } : p));
  const rows = buildChartData(spike);
  for (let i = 1; i < rows.length; i++) assert.ok(rows[i].x > rows[i - 1].x);
  for (const r of rows) assert.ok(Array.isArray(r.band));
});
