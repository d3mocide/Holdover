import test from 'node:test';
import assert from 'node:assert/strict';
import { medianText, unusual, sortGauges, detailParts } from './gaugeText.js';
import { floodShort } from './floodText.js';

const g = (name, cfs, pct, extra = {}) => ({ name, vs_median_pct: pct, values: cfs == null ? {} : { discharge_cfs: { value: cfs } }, ...extra });

test('median wording has a sign, a real minus and a plain "at median"', () => {
  assert.equal(medianText(-21), '−21% vs median');
  assert.equal(medianText(4), '+4% vs median');
  assert.equal(medianText(0), 'at median');
  assert.equal(medianText(null), null);
});
test('only a big departure from the median is flagged', () => {
  assert.equal(unusual(-21), true); assert.equal(unusual(20), true); assert.equal(unusual(19), false); assert.equal(unusual(null), false);
});
test('sorting: by name, by distance from the median (unknowns last), by flow', () => {
  const list = [g('B river', 500, 3), g('A river', 90, -30), g('C river', 1200, null), g('D river', null, 10)];
  assert.deepEqual(sortGauges(list, 'name').map((x) => x.name), ['A river', 'B river', 'C river', 'D river']);
  assert.deepEqual(sortGauges(list, 'unusual').map((x) => x.name), ['A river', 'D river', 'B river', 'C river']);
  assert.deepEqual(sortGauges(list, 'flow').map((x) => x.name), ['C river', 'B river', 'A river', 'D river']);
  assert.deepEqual(list.map((x) => x.name), ['B river', 'A river', 'C river', 'D river']);  // the input is not reordered
});
test('the line under the number only has what the gauge reports', () => {
  assert.deepEqual(detailParts(g('x', 97, 1, { values: { gage_height_ft: { value: 2.39 }, water_temp_f: { value: 48.6 } } })), ['+1% vs median', '2.39 ft', '49°F']);
  assert.deepEqual(detailParts(g('x', 97, null)), []);
});
test('the NOAA note is short and mentions a forecast only when it is not quiet', () => {
  assert.equal(floodShort({ label: 'No flooding', forecast: { category: 'no_flooding', label: 'No flooding' } }), 'NOAA: no flooding');
  assert.equal(floodShort({ label: 'No flooding', forecast: { category: 'minor', label: 'Minor flooding' } }), 'NOAA: no flooding, forecast minor flooding');
  assert.equal(floodShort(null), null);
});
