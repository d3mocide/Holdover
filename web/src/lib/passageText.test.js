import test from 'node:test';
import assert from 'node:assert/strict';
import { dayText, rangeText, speciesLine, shownSpecies } from './passageText.js';

const p = { from: '2026-10-09', through: '2026-10-15', days_reported: 7, species: {
  coho: { label: 'Coho', count: 589, avg10: 1405 }, chinook: { label: 'Chinook', count: 15, avg10: 76 }, steelhead: { label: 'Steelhead (hatchery and wild)', count: 17, avg10: 35 }, shad: { label: 'x', count: 1, avg10: 1 } } };
test('range and day wording', () => {
  assert.equal(dayText('2026-10-09'), 'Oct 9');
  assert.equal(rangeText(p), 'Oct 9 to Oct 15');
  assert.equal(rangeText({ ...p, days_reported: 4 }), 'Oct 9 to Oct 15 (4 days reported)');
});
test('a species line gives the count and the ten-year average for the same days, never a verdict', () => {
  assert.equal(speciesLine(p.species.coho), 'Coho: 589 fish · ten-year average for the same days 1,405');
  assert.equal(speciesLine({ label: 'Chum', count: 3, avg10: 0 }), 'Chum: 3 fish');
  assert.doesNotMatch(speciesLine(p.species.coho), /good|poor|strong|weak|run is/i);
});
test('only coho, Chinook and steelhead lead, biggest first', () => {
  assert.deepEqual(shownSpecies(p).map((s) => s.label), ['Coho', 'Steelhead (hatchery and wild)', 'Chinook']);
  assert.deepEqual(shownSpecies(null), []);
});
