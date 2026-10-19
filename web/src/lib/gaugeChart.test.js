import test from 'node:test';
import assert from 'node:assert/strict';
import { chartLines } from './gaugeChart.js';
const point = (hour, value) => ({ observed_at: `2026-10-19T${String(hour).padStart(2, '0')}:00:00Z`, value });
test('observations are sorted, zero remains data, and gaps break the line', () => {
  const c = chartLines([point(6, 20), point(1, 0), point(2, 10)]);
  assert.equal(c.min, 0); assert.equal(c.max, 20); assert.equal(c.lines.length, 2);
  assert.equal(c.rows[0].value, 0); assert.equal(c.rows.length, 3);
});
test('empty, constant and single-sample charts never invent points or NaN', () => {
  assert.deepEqual(chartLines([]).lines, []);
  for (const rows of [[point(1, 100)], [point(1, 100), point(2, 100)]]) {
    const c = chartLines(rows); assert.equal(c.rows.length, rows.length); assert.ok(!c.lines.join('').includes('NaN'));
  }
});
