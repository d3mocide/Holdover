import test from 'node:test';
import assert from 'node:assert/strict';
import { describeConditions, waterbodyHistory } from './journalStats.js';

const cond = { weather: { temp_f: 54.4, short: 'Partly Sunny' }, water_temp_f: { value: 49.2 },
  gauges: [{ values: { discharge_cfs: { value: 1240 } }, trend: 'steady' }], moon: { phase: 'First quarter' } };
const trip = (uuid, wb, date, extra = {}) => ({ uuid, waterbody_id: wb, started_at: `${date}T07:00:00Z`, ...extra });
const fish = (uuid, t, count, species = 'rainbow trout', extra = {}) => ({ uuid, trip_uuid: t, count, species, ...extra });

test('conditions are described from what was recorded, and nothing else', () => {
  assert.deepEqual(describeConditions(cond), ['54°F air, partly sunny', 'water 49°F', '1,240 cfs steady', 'first quarter']);
  assert.deepEqual(describeConditions({ source: 'cached', moon: { phase: 'Full moon' } }), ['full moon', 'from cached values']);
  assert.deepEqual(describeConditions(JSON.stringify(cond)).length, 4);   // accepts the stored JSON string
  assert.deepEqual(describeConditions(null), []);
  assert.deepEqual(describeConditions('not json'), []);
  assert.deepEqual(describeConditions({ weather: { temp_f: 'warm' } }), []); // junk values are skipped, not shown
});

test('history: totals, species, last visit, only this waterbody', () => {
  const h = waterbodyHistory({
    waterbodyId: 5,
    trips: [trip('a', 5, '2026-10-01'), trip('b', 5, '2026-10-12'), trip('c', 9, '2026-10-13')],
    catches: [fish('1', 'a', 2), fish('2', 'b', 3), fish('3', 'b', 1, 'brown trout'), fish('4', 'c', 50)]
  });
  assert.equal(h.trips, 2); assert.equal(h.fish, 6); assert.equal(h.last, '2026-10-12');
  assert.deepEqual(h.bySpecies, [{ species: 'rainbow trout', count: 5 }, { species: 'brown trout', count: 1 }]);
});

test('best day is the trip with the most fish, ties go to the newer one, and it carries its conditions', () => {
  const h = waterbodyHistory({
    waterbodyId: 5,
    trips: [trip('a', 5, '2026-09-01', { conditions_json: JSON.stringify({ moon: { phase: 'New moon' } }) }), trip('b', 5, '2026-10-12', { conditions_json: JSON.stringify(cond) }), trip('z', 5, '2026-10-20')],
    catches: [fish('1', 'a', 4), fish('2', 'b', 4), fish('3', 'z', 1)]
  });
  assert.equal(h.best.uuid, 'b'); assert.equal(h.best.date, '2026-10-12'); assert.equal(h.best.fish, 4);
  assert.equal(h.best.conditions.length, 4);
  assert.equal(waterbodyHistory({ waterbodyId: 5, trips: [trip('a', 5, '2026-09-01')], catches: [] }).best, null); // a skunk has no best day
});

test('top lure counts only explicit "caught on" records for existing gear', () => {
  const gear = [{ uuid: 'g1', name: 'Panther Martin' }, { uuid: 'g2', name: 'Woolly Bugger' }, { uuid: 'g3', name: 'Gone', deleted: 1 }];
  const h = waterbodyHistory({
    waterbodyId: 5, gear, trips: [trip('a', 5, '2026-10-01')],
    catches: [fish('1', 'a', 2, 'rainbow trout', { gear_uuid: 'g1' }), fish('2', 'a', 1, 'rainbow trout', { gear_uuid: 'g2' }), fish('3', 'a', 9, 'x', { gear_uuid: 'g3' }), fish('4', 'a', 7)]
  });
  assert.deepEqual(h.topGear, { uuid: 'g1', name: 'Panther Martin', count: 2 });
});

test('deleted trips and catches never count, and empty input is fine', () => {
  const h = waterbodyHistory({ waterbodyId: 5, trips: [trip('a', 5, '2026-10-01', { deleted: 1 }), trip('b', 5, '2026-10-02')], catches: [fish('1', 'a', 9), fish('2', 'b', 2, 'x', { deleted: 1 }), fish('3', 'b', 1)] });
  assert.equal(h.trips, 1); assert.equal(h.fish, 1);
  assert.deepEqual(waterbodyHistory({ waterbodyId: 1 }), { trips: 0, fish: 0, last: null, bySpecies: [], best: null, topGear: null });
});
