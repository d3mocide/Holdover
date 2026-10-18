import test from 'node:test';
import assert from 'node:assert/strict';
import { stockingSections, weekLabelYear, split } from './stockingGroups.js';

const w = (week_of, freshness) => ({ week_of, freshness });
test('coming up is soonest first and past is newest first', () => {
  const s = stockingSections([w('2027-05-24', 'upcoming'), w('2026-11-02', 'upcoming'), w('2027-01-25', 'upcoming'),
    w('2026-09-14', 'older'), w('2026-10-12', 'this_week'), w('2025-12-01', 'older')]);
  assert.deepEqual(s.map((x) => x.title), ['Coming up', 'Already stocked']);
  assert.deepEqual(s[0].items.map((i) => i.week_of), ['2026-11-02', '2027-01-25', '2027-05-24']);
  assert.deepEqual(s[1].items.map((i) => i.week_of), ['2026-10-12', '2026-09-14', '2025-12-01']);
});
test('empty sections are left out and an empty list gives nothing', () => {
  assert.deepEqual(stockingSections([]), []);
  assert.deepEqual(stockingSections([w('2026-10-12', 'this_week')]).map((x) => x.key), ['past']);
});
test('a week names its year only when it is not the current year', () => {
  const now = new Date(2026, 9, 18);
  assert.equal(weekLabelYear('2026-10-12', now), 'Week of Oct 12');
  assert.equal(weekLabelYear('2027-04-05', now), 'Week of Apr 5, 2027');
  assert.equal(weekLabelYear('2025-12-01', now), 'Week of Dec 1, 2025');
  assert.equal(weekLabelYear('', now), '');
});
test('long lists show the first rows and tuck the rest away', () => {
  const items = Array.from({ length: 10 }, (_, i) => i);
  assert.deepEqual(split(items), { shown: [0, 1, 2, 3], rest: [4, 5, 6, 7, 8, 9] });
  assert.deepEqual(split([1, 2]), { shown: [1, 2], rest: [] });
});
