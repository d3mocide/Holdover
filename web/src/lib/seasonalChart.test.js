import test from 'node:test';
import assert from 'node:assert/strict';
import { seasonalChart, baselineStale, flowStale } from './seasonalChart.js';

test('seasonal bands and lines leave gaps and map one actual dated observation', () => {
  const row = date => ({ date, p25: 10, median: 20, p75: 30 });
  const data = { series: [row('2026-10-19'), row('2026-10-20'), { date: '2026-10-21', median: null }, row('2026-10-22')],
    current: { date: '2026-10-20', value: 50 } };
  const c = seasonalChart(data);
  assert.equal(c.bands.length, 1); assert.equal(c.lines.length, 2); assert.equal(c.max, 50);
  assert.equal(c.dot.x, 12 + 376 / 3); assert.equal(c.dot.y, 16);
  assert.equal(seasonalChart({ ...data, current: { date: '2026-10-25', value: 999 } }).dot, null);
  assert.equal(seasonalChart({ series: [{ ...row('a'), p25: 50 }] }).lines.length, 0);
  assert.deepEqual(seasonalChart(null).bands, []);
});
test('empty, zero and constant baselines produce finite chart coordinates', () => {
  const chart = seasonalChart({ series: [{ date: 'a', p25: 0, median: 0, p75: 0 }], current: { date: 'a', value: 0 } });
  assert.equal(chart.max, 1); assert.equal(chart.dot.y, 144); assert.ok(!chart.lines.join('').includes('NaN'));
});
test('cached baselines and current values age independently, including rollover and future dates', () => {
  const now = Date.parse('2026-10-20T18:00Z');
  const d = { as_of: '2026-10-01T18:00Z', end_year: 2025 };
  assert.equal(baselineStale(d, now), false);
  assert.equal(baselineStale(d, now + 50 * 86400000), true);
  assert.equal(baselineStale({ ...d, stale: true }, now), true);
  assert.equal(baselineStale({ ...d, end_year: 2024 }, now), true);
  assert.equal(baselineStale({ ...d, as_of: '2026-10-21T00:00Z' }, now), true);
  assert.equal(flowStale({ observed_at: '2026-10-20T17:00Z' }, now), false);
  assert.equal(flowStale({ observed_at: '2026-10-20T14:00Z' }, now), true);
  assert.equal(flowStale({ observed_at: '2026-10-20T19:00Z' }, now), true);
  assert.equal(flowStale(null, now), true);
});
