import test from 'node:test';
import { qualityReadings, readingStale, gaugeStale } from './gaugeText.js';
import assert from 'node:assert/strict';
import { medianText, unusual, sortGauges, detailParts } from './gaugeText.js';
import { floodShort } from './floodText.js';

test('cached sensor freshness expires offline and a fresh temperature never refreshes old flow', () => {
  const now = Date.parse('2026-10-19T12:00:00Z');
  const old = { observed_at: '2026-10-19T06:00:00Z', stale: false };
  const fresh = { observed_at: '2026-10-19T11:00:00Z', stale: false };
  assert.equal(readingStale(old, now), true); assert.equal(readingStale(fresh, now), false);
  assert.equal(gaugeStale({ as_of: fresh.observed_at, values: { discharge_cfs: old, water_temp_f: fresh } }, now), true);
});

test('water-quality rows retain their own timestamps and stale state', () => {
  const now = Date.parse('2026-10-19T12:00:00Z');
  const gauge = { values: { ph: { value: 7.4, observed_at: '2026-10-19T06:00:00Z', stale: true },
    turbidity_fnu: { value: 2.5, observed_at: '2026-10-19T11:00:00Z', stale: false },
    conductance_uscm: { value: 100, observed_at: '2026-10-10T11:00:00Z', stale: true } } };
  const readings = qualityReadings(gauge, now);
  assert.equal(readings.length, 2);
  assert.equal(readings[0].observed_at, gauge.values.ph.observed_at);
  assert.equal(readings[0].stale, true);
  assert.equal(readings[1].stale, false);
});

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

import { qualityParts } from './gaugeText.js';
test('water quality shows what the gauge reports, in plain units, and drops a stale sensor', () => {
  const now = Date.parse('2026-10-19T03:00:00Z');
  const g = { values: { dissolved_oxygen_mgl: { value: 9.5, observed_at: '2026-10-19T02:30:00+00:00' }, ph: { value: 7.46, observed_at: '2026-10-19T02:30:00+00:00' },
    turbidity_fnu: { value: 2.3, observed_at: '2026-10-19T02:30:00+00:00' }, conductance_uscm: { value: 73, observed_at: '2026-10-17T15:00:00+00:00' } } };
  assert.deepEqual(qualityParts(g, now), ['dissolved oxygen 9.5 mg/L', 'pH 7.5', 'turbidity 2.3 FNU']);  // conductance is two days old
  assert.deepEqual(qualityParts({ values: {} }, now), []);
  assert.equal(qualityParts({ values: { turbidity_fnu: { value: 41.7, observed_at: '2026-10-19T02:30:00+00:00' } } }, now)[0], 'turbidity 42 FNU');
});
