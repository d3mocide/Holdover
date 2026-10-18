import test from 'node:test';
import assert from 'node:assert/strict';
import { stockingSections } from './stockingGroups.js';

const w = (week_of, freshness) => ({ week_of, freshness });
test('coming up is soonest first and past is newest first, each grouped by year', () => {
  const s = stockingSections([w('2027-05-24', 'upcoming'), w('2026-11-02', 'upcoming'), w('2027-01-25', 'upcoming'),
    w('2026-09-14', 'older'), w('2026-10-12', 'this_week'), w('2025-12-01', 'older')]);
  assert.deepEqual(s.map((x) => x.title), ['Coming up', 'Already stocked']);
  assert.deepEqual(s[0].years.map((y) => [y.year, y.items.map((i) => i.week_of)]),
    [['2026', ['2026-11-02']], ['2027', ['2027-01-25', '2027-05-24']]]);
  assert.deepEqual(s[1].years.map((y) => [y.year, y.items.map((i) => i.week_of)]),
    [['2026', ['2026-10-12', '2026-09-14']], ['2025', ['2025-12-01']]]);
});
test('empty sections are left out and an empty list gives nothing', () => {
  assert.deepEqual(stockingSections([]), []);
  assert.deepEqual(stockingSections([w('2026-10-12', 'this_week')]).map((x) => x.key), ['past']);
});
