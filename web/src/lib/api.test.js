// Pure-logic unit tests: run with `npm test` (node's built-in runner, no extra dependencies).
import test from 'node:test';
import assert from 'node:assert/strict';
import { weekLabel, longDate, isoDay, dayLabel, TREND, FRESH_LABEL } from './api.js';

test('stocking is always shown as a week, never a day', () => {
  assert.equal(weekLabel('2026-10-12'), 'Week of Oct 12');
  assert.equal(weekLabel(''), '');
  assert.equal(FRESH_LABEL.upcoming, 'Scheduled');
});

test('longDate formats an ISO date without time-zone drift', () => {
  assert.equal(longDate('2026-01-05'), 'Jan 5, 2026');
  assert.equal(longDate(null), '');
});

test('isoDay is local, zero-padded and offsets by whole days', () => {
  assert.match(isoDay(0), /^\d{4}-\d{2}-\d{2}$/);
  const a = new Date(isoDay(0) + 'T12:00:00'), b = new Date(isoDay(3) + 'T12:00:00');
  assert.equal(Math.round((b - a) / 86400000), 3);
});

test('day labels', () => {
  assert.equal(dayLabel(0), 'Today');
  assert.equal(dayLabel(1), 'Tomorrow');
  assert.ok(dayLabel(4).length > 3);
});

test('trend labels carry an arrow, not just colour', () => {
  for (const t of Object.values(TREND)) assert.match(t, /[↑↓→]/);
});
