import test from 'node:test';
import assert from 'node:assert/strict';
import { ownedFor, ownedText, RULES } from './gearPack.js';

const g = (name, kind, extra = {}) => ({ uuid: name, name, kind, status: 'active', ...extra });
const fisheries = (...f) => ({ fisheries_json: JSON.stringify(f) });

test('matches by gear type, name hints and fishery tag', () => {
  const gear = [g('Spinning rod', 'rod'), g('Fly rod', 'rod'), g('Panther Martin spinner', 'lure', fisheries('trout')),
    g('Woolly Bugger', 'fly', fisheries('trout', 'warmwater')), g('Waders', 'wearable'), g('Rain jacket', 'wearable'), g('Landing net', 'net')];
  assert.deepEqual(ownedFor('rod-light', gear).names, ['Spinning rod']);               // a fly rod is not a light spinning rod
  assert.deepEqual(ownedFor('trout-lures', gear).names, ['Panther Martin spinner', 'Woolly Bugger']);
  assert.deepEqual(ownedFor('ww-lures', gear).names, ['Woolly Bugger']);               // tagged warmwater
  assert.deepEqual(ownedFor('waders', gear).names, ['Waders']);
  assert.deepEqual(ownedFor('rain', gear).names, ['Rain jacket']);
  assert.deepEqual(ownedFor('net-gaff', gear).names, ['Landing net']);
});

test('retired, lost and deleted gear never counts', () => {
  const gear = [g('Waders', 'wearable', { status: 'retired' }), g('Wading boots', 'wearable', { status: 'lost' }), g('Old waders', 'wearable', { deleted: 1 })];
  assert.deepEqual(ownedFor('waders', gear), { names: [], more: 0 });
});

test('long lists are trimmed and counted, and unknown items or empty gear are safe', () => {
  const lures = ['a', 'b', 'c', 'd', 'e'].map((n) => g(`Lure ${n}`, 'lure', fisheries('trout')));
  const r = ownedFor('trout-lures', lures);
  assert.equal(r.names.length, 3); assert.equal(r.more, 2);
  assert.equal(ownedText(r), 'You have: Lure a, Lure b, Lure c and 2 more');
  assert.equal(ownedText(ownedFor('license', lures)), '');        // nothing to match: says nothing
  assert.equal(ownedText(ownedFor('waders', [])), '');
  assert.equal(ownedText(ownedFor('waders', null)), '');
});

test('it never reports what is missing: no match is an empty string, not a warning', () => {
  assert.equal(ownedText(ownedFor('rod-light', [g('Fly rod', 'rod')])), '');
});

test('every rule is a function, so a typo in an id cannot throw at render time', () => {
  for (const [id, rule] of Object.entries(RULES)) assert.equal(typeof rule, 'function', id);
});
