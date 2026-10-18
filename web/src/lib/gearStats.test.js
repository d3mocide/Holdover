import test from 'node:test';
import assert from 'node:assert/strict';
import { gearStats, namesFor } from './gearStats.js';
import { CATALOG, suggest, KINDS } from './gearCatalog.js';

const g = (uuid, name, kind = 'lure') => ({ uuid, name, kind });
const trip = (uuid, extra = {}) => ({ uuid, ...extra });
const fish = (uuid, trip_uuid, count, extra = {}) => ({ uuid, trip_uuid, count, ...extra });

const gear = [g('spin', 'Panther Martin'), g('bug', 'Woolly Bugger', 'fly'), g('rod', '6wt', 'rod'), g('new', 'Never used')];
const setups = [{ uuid: 's1', name: 'Light spinning', item_uuids_json: JSON.stringify(['spin']) }];

test('credits fish to a lure that was explicitly recorded, and to trips it was used on', () => {
  const r = gearStats({
    gear, setups,
    trips: [trip('t1', { gear_json: JSON.stringify(['spin']), waterbody_id: 5 }), trip('t2', { gear_json: JSON.stringify(['spin', 'bug']) })],
    catches: [fish('c1', 't1', 3, { gear_uuid: 'spin' }), fish('c2', 't2', 2, { gear_uuid: 'bug' }), fish('c3', 't2', 1)]
  });
  const by = Object.fromEntries(r.items.map((i) => [i.name, i]));
  assert.equal(by['Panther Martin'].trips, 2);
  assert.equal(by['Panther Martin'].caught, 3);          // explicit
  assert.equal(by['Panther Martin'].fishOnTrips, 6);     // 3 on t1 + 3 on t2, shared credit
  assert.equal(by['Woolly Bugger'].caught, 2);
  assert.equal(by['Never used'].trips, 0);
  assert.deepEqual(r.totals, { trips: 2, fish: 6 });
  assert.equal(r.items[0].name, 'Panther Martin');       // most caught first
});

test('items in a trip\'s setup count as used on that trip', () => {
  const r = gearStats({ gear, setups, trips: [trip('t1', { setup_uuid: 's1' })], catches: [fish('c1', 't1', 4)] });
  assert.equal(r.items.find((i) => i.uuid === 'spin').trips, 1);
  assert.equal(r.items.find((i) => i.uuid === 'spin').caught, 0);   // used, but no lure recorded on the catch
  assert.equal(r.items.find((i) => i.uuid === 'spin').fishOnTrips, 4);
});

test('setup stats: fish, per-trip average and best waters', () => {
  const r = gearStats({
    gear, setups,
    trips: [trip('t1', { setup_uuid: 's1', waterbody_id: 1 }), trip('t2', { setup_uuid: 's1', waterbody_id: 2 }), trip('t3', { waterbody_id: 1 })],
    catches: [fish('c1', 't1', 5), fish('c2', 't2', 2), fish('c3', 't3', 9)]
  });
  assert.deepEqual(r.setups[0], { uuid: 's1', name: 'Light spinning', trips: 2, fish: 7, perTrip: 3.5, waters: [{ waterbody_id: 1, fish: 5 }, { waterbody_id: 2, fish: 2 }] });
});

test('deleted rows and orphaned catches never count', () => {
  const r = gearStats({
    gear: [...gear, { ...g('old', 'Deleted lure'), deleted: 1 }], setups,
    trips: [trip('t1', { gear_json: JSON.stringify(['spin']) }), trip('t2', { deleted: 1, gear_json: JSON.stringify(['spin']) })],
    catches: [fish('c1', 't1', 2, { gear_uuid: 'spin' }), fish('c2', 't2', 50, { gear_uuid: 'spin' }), fish('c3', 'gone', 9, { gear_uuid: 'spin' }), { ...fish('c4', 't1', 7, { gear_uuid: 'spin' }), deleted: 1 }]
  });
  assert.equal(r.items.find((i) => i.uuid === 'spin').caught, 2);
  assert.equal(r.items.some((i) => i.uuid === 'old'), false);
  assert.deepEqual(r.totals, { trips: 1, fish: 2 });
});

test('bad JSON and empty data do not throw', () => {
  const r = gearStats({ gear, trips: [trip('t1', { gear_json: 'not json', setup_uuid: 'missing' })], catches: [] });
  assert.equal(r.items.every((i) => i.trips === 0), true);
  assert.deepEqual(gearStats({}), { items: [], setups: [], totals: { trips: 0, fish: 0 } });
});

test('namesFor drops gear that no longer exists', () => {
  assert.deepEqual(namesFor(JSON.stringify(['spin', 'ghost', 'bug']), gear), ['Panther Martin', 'Woolly Bugger']);
  assert.deepEqual(namesFor(null, gear), []);
});

test('catalog: every entry is well-formed and unique', () => {
  const kinds = new Set(KINDS.map(([k]) => k));
  const seen = new Set();
  for (const c of CATALOG) {
    assert.ok(kinds.has(c.kind), `unknown kind for ${c.name}`);
    assert.ok(c.fisheries.length && c.fisheries.every((f) => ['trout', 'steelhead', 'warmwater'].includes(f)), c.name);
    assert.ok(!seen.has(c.name.toLowerCase()), `duplicate ${c.name}`); seen.add(c.name.toLowerCase());
  }
  assert.ok(CATALOG.length >= 60);
});

test('suggest: prefix first, then word match, filtered by kind', () => {
  assert.equal(suggest('wool')[0].name, 'Woolly Bugger');
  assert.ok(suggest('minnow').some((c) => c.name === 'Clouser Minnow'));
  assert.ok(suggest('r', 'rod').every((c) => c.kind === 'rod'));
  assert.deepEqual(suggest('zzzz'), []);
  assert.ok(suggest('').length > 0);
});
