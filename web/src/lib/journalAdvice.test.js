import test from 'node:test';
import assert from 'node:assert/strict';
import { journalAdvice, personalSpots, dayContext } from './journalAdvice.js';

const now = Date.parse('2026-10-20T18:00:00Z'), water = { id: 1, kind: 'river' };
const iso = n => new Date(n).toISOString();
const context = (at, value = 100, site = 'test-gauge') => ({ captured_at: iso(at), gauges: [{ site_no: site,
  values: { discharge_cfs: { value, observed_at: iso(at - 60000) } } }], weather: { temp_f: 55 }, weather_as_of: iso(at - 60000) });
const data = () => ({ trips: [1, 2, 3].map(i => ({ uuid: `t${i}`, waterbody_id: 1, started_at: iso(now - i * 86400000),
  conditions_json: JSON.stringify(context(now - i * 86400000)), gear_json: '["lure"]', setup_uuid: 'setup', dirty: 1 })),
  catches: [{ uuid: 'c1', trip_uuid: 't1', count: 2, gear_uuid: 'lure' }, { uuid: 'c2', trip_uuid: 't2', count: 0 }],
  gear: [{ uuid: 'lure', name: 'Test lure', kind: 'lure', status: 'active' }], setups: [{ uuid: 'setup', name: 'Test setup' }] });
const advice = d => journalAdvice(water, context(now), d, now);

test('same-water comparison includes trips with zero or no recorded catches, with shrunken adjustment', () => {
  const a = advice(data());
  assert.equal(a.matched.length, 3); assert.equal(a.successes, 1); assert.equal(a.adjustment, -.5);
  assert.equal(a.eligible, true); assert.equal(a.matched[0].dirty, 1);
  assert.deepEqual(a.gear, [{ uuid: 'lure', name: 'Test lure', trips: 3, successes: 1, fish: 2 }]);
  assert.deepEqual(a.setups, [{ uuid: 'setup', name: 'Test setup', trips: 3, successes: 1 }]);
});
test('threshold, cap, missing data, ties, public-score preservation and no mutation', () => {
  const d = data(); d.trips.pop(); assert.equal(advice(d).adjustment, 0);
  const spots = [{ rank: 1, waterbody: water, score: 50, coverage: .5, journal_context: context(now) },
    { rank: 2, waterbody: { id: 2, kind: 'river' }, score: 49.8, journal_context: context(now) }];
  assert.equal(personalSpots(spots, data(), false, now)[0].score, 50);
  assert.equal(personalSpots([{ ...spots[0], journal_context: null, score: 23.456 }], data(), true, now)[0].score, 23.456);
  const ranked = personalSpots(spots, data(), true, now);
  assert.equal(ranked[0].waterbody.id, 2); assert.equal(ranked[1].score, 49.5);
  assert.equal(ranked[1].public_score, 50); assert.equal(ranked[1].coverage, .5); assert.equal(spots[0].score, 50);
  assert.equal(personalSpots([{ ...spots[0], score: .1 }], data(), true, now)[0].score, 0);
  d.trips = Array.from({ length: 30 }, (_, i) => ({ ...data().trips[0], uuid: `x${i}` }));
  d.catches = d.trips.map(t => ({ trip_uuid: t.uuid, count: 100 }));
  assert.equal(advice(d).adjustment, 5); d.catches = []; assert.equal(advice(d).adjustment, -5);
});
test('no cross-water, cross-gauge, out-of-range, deleted or future trips; stale current data is neutral', () => {
  for (const patch of [{ waterbody_id: 2 }, { deleted: 1 }, { started_at: iso(now + 60000) },
    { conditions_json: JSON.stringify(context(now - 86400000, 100, 'other')) },
    { conditions_json: JSON.stringify(context(now - 86400000, 121)) }]) {
    const d = data(); d.trips = [{ ...d.trips[0], ...patch }]; assert.equal(advice(d).matched.length, 0);
  }
  for (const c of [null, context(now - 4 * 3600000), context(now + 120000), context(now, 0)]) {
    assert.equal(journalAdvice(water, c, data(), now).ready, false);
    assert.equal(journalAdvice(water, c, data(), now).adjustment, 0);
  }
});
test('invalid/backdated/expired snapshots and invalid outcome counts never contribute', () => {
  for (const json of ['broken', 'null', '{}', '{"gauges":[null]}', '{"gauges":{}}',
    JSON.stringify(context(now - 10 * 86400000))]) {
    const d = data(); d.trips.forEach(t => { t.conditions_json = json; }); assert.equal(advice(d).matched.length, 0);
  }
  const d = data(); d.catches[0].count = -1; assert.equal(advice(d).matched.length, 2);
  d.catches[0].count = '2'; assert.equal(advice(d).matched.length, 2);
  const old = context(now - 86400000); old.gauges[0].values.discharge_cfs.observed_at = iso(now - 2 * 86400000);
  d.trips = [{ ...data().trips[0], conditions_json: JSON.stringify(old) }]; assert.equal(advice(d).matched.length, 0);
});
test('gear needs explicit catch attribution, failed usage counts, and removed gear/setups are excluded', () => {
  const d = data(); d.catches[0].gear_uuid = null; assert.equal(advice(d).gear.length, 0);
  d.catches[0].gear_uuid = 'lure'; d.gear[0].status = 'lost'; assert.equal(advice(d).gear.length, 0);
  d.gear[0].status = 'active'; d.gear[0].deleted = 1; d.setups[0].deleted = 1;
  assert.equal(advice(d).gear.length, 0); assert.equal(advice(d).setups.length, 0);
  d.catches[0].deleted = 1; assert.equal(advice(d).successes, 0);
});
test('lake comparison uses timely air forecasts within 10 F, not a river gauge or water temperature', () => {
  const lake = { id: 1, kind: 'lake' }, c = context(now); c.weather.temp_f = 65;
  assert.equal(journalAdvice(lake, c, data(), now).matched.length, 3);
  c.weather.temp_f = 66; assert.equal(journalAdvice(lake, c, data(), now).matched.length, 0);
  c.weather_as_of = iso(now - 7 * 3600000); assert.equal(journalAdvice(lake, c, data(), now).ready, false);
  const day = dayContext({ weather: { day: { temp_f: 55 }, as_of: iso(now - 60000) }, gauges: [] });
  assert.equal(journalAdvice(lake, day, data(), now).matched.length, 3);
});
test('comparison evidence retains actual values and uses the same deterministic gauge on every view', () => {
  const c = context(now); c.gauges.unshift({ site_no: 'zzz-other', values: { discharge_cfs: { value: 999, observed_at: iso(now - 60000) } } });
  const a = journalAdvice(water, c, data(), now);
  assert.equal(a.current.site_no, 'test-gauge'); assert.equal(a.current.value, 100);
  assert.equal(a.matched[0].comparison_value, 100);
  assert.equal(a.matched[0].comparison_as_of, iso(now - 86400000 - 60000));
});
