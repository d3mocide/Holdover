import test from 'node:test';
import assert from 'node:assert/strict';
import { hasDraftContent } from './tripDraft.js';

test('only meaningful draft edits count as unsynced work', () => {
  assert.equal(hasDraftContent(null), false);
  assert.equal(hasDraftContent({ startedAt: '2026-10-19', species: [{ name: '', count: 0 }], notes: '  ' }), false);
  for (const d of [{ notes: 'private' }, { gps: { lat: 44, lon: -123 } }, { wbId: '1' }, { method: 'fly' },
    { species: [{ name: 'trout', count: 0 }] }, { species: [{ name: '', count: 2 }] }, { gearSel: ['lure'] }]) {
    assert.equal(hasDraftContent(d), true);
  }
});
