import test from 'node:test';
import assert from 'node:assert/strict';
import { findWaters, evidenceText } from './waterSearch.js';

const waters = [{ id: 1, name: 'Tualatin River', kind: 'river', zone: 'willamette' },
  { id: 2, name: 'Deschutes River', kind: 'river', zone: 'central' },
  { id: 3, name: 'East Lake', kind: 'lake', zone: 'central', lat: null }];
test('river browsing is zone-scoped without relying on stocking or gauges', () => {
  assert.deepEqual(findWaters(waters, { zone: 'willamette' }).map((w) => w.id), [1]);
});
test('search spans zones and includes unpinned waters', () => {
  assert.deepEqual(findWaters(waters, { query: 'east central', zone: 'willamette' }).map((w) => w.id), [3]);
  assert.equal(findWaters(waters, { query: 'nonexistent' }).length, 0);
});
test('favorites span zones and never invent an entry', () => {
  assert.deepEqual(findWaters(waters, { mode: 'favorites', favorites: [3, 1, 99] }).map((w) => w.id), [3, 1]);
});
test('evidence is bounded and distinct from the score', () => {
  assert.equal(evidenceText(.43), 'Evidence: 43%'); assert.equal(evidenceText(null), 'Evidence: 0%');
  assert.equal(evidenceText(1.5), 'Evidence: 100%');
});
