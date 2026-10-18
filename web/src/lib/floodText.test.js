import test from 'node:test';
import assert from 'node:assert/strict';
import { floodText, floodElevated } from './floodText.js';

const ok = { category: 'no_flooding', label: 'No flooding', stage_ft: 3.05, elevated: false, forecast: { category: 'no_flooding', label: 'No flooding', stage_ft: 3.2 } };
test('quiet river reports NOAA category and stage, never "safe"', () => {
  assert.equal(floodText(ok), 'NOAA flood category: No flooding, stage 3.05 ft');
  assert.equal(floodElevated(ok), false);
  assert.doesNotMatch(floodText(ok), /safe/i);
});
test('a forecast above no flooding is stated and flagged even if it is quiet now', () => {
  const f = { ...ok, forecast: { category: 'minor', label: 'Minor flooding', stage_ft: 21.4 } };
  assert.equal(floodText(f), 'NOAA flood category: No flooding, stage 3.05 ft. NOAA forecast: minor flooding (21.4 ft)');
  assert.equal(floodElevated(f), true);
});
test('observed flooding is flagged; no data is silent', () => {
  assert.equal(floodElevated({ ...ok, category: 'moderate', label: 'Moderate flooding', elevated: true }), true);
  assert.equal(floodText(null), null);
  assert.equal(floodElevated(null), false);
  assert.equal(floodText({ ...ok, stage_ft: null, forecast: null }), 'NOAA flood category: No flooding');
});
