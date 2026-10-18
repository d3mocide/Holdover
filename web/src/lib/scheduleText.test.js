import test from 'node:test';
import assert from 'node:assert/strict';
import { monthLabel, monthShort, plural, weekSummary, monthRange } from './scheduleText.js';

test('month labels and ranges, including leap years and year ends', () => {
  assert.equal(monthLabel('2026-11'), 'Nov 2026');
  assert.deepEqual(monthRange('2026-11'), ['2026-11-01', '2026-11-30']);
  assert.deepEqual(monthRange('2028-02'), ['2028-02-01', '2028-02-29']);
  assert.deepEqual(monthRange('2026-12'), ['2026-12-01', '2026-12-31']);
});
test('the short chip label carries the year only when it is not the current one', () => {
  const now = new Date(2026, 9, 18);
  assert.equal(monthShort('2026-11', now), 'Nov');
  assert.equal(monthShort('2027-01', now), 'Jan 2027');
});
test('counts are worded with the right plural', () => {
  assert.equal(plural(1, 'waterbody', 'waterbodies'), '1 waterbody');
  assert.equal(plural(5, 'waterbody', 'waterbodies'), '5 waterbodies');
  assert.equal(weekSummary({ waterbodies: [1, 2, 3], total_fish: 4620 }), '3 waterbodies · 4,620 fish');
  assert.equal(weekSummary({ waterbodies: [1], total_fish: 1 }), '1 waterbody · 1 fish');
});
