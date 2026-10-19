import test from 'node:test';
import assert from 'node:assert/strict';
import { journalRows, journalJson, journalCsv } from './journalExport.js';

const snapshot = () => ({
  trips: [{ uuid: 't', notes: 'not synced, "yet"\nsecond line', dirty: 1, lat: 44, lon: -123, setup_uuid: 's' }, { uuid: 'gone', deleted: 1 }],
  catches: [{ uuid: 'c', trip_uuid: 't', species: 'trout', count: 2, gear_uuid: 'g', dirty: 1 },
    { uuid: 'orphan', trip_uuid: 'gone' }, { uuid: 'deleted', trip_uuid: 't', deleted: 1 }],
  gear: [{ uuid: 'g', name: 'spinner', dirty: 1 }], setups: [{ uuid: 's', name: 'Spinning' }],
  pins: [{ uuid: 'p', label: 'My spot' }, { uuid: 'deleted-pin', deleted: 1 }]
});

test('device export keeps unsynced rows, gear and pins, and omits deleted and orphaned entries', () => {
  const d = journalRows(snapshot());
  assert.equal(d.trips.length, 1); assert.equal(d.catches.length, 1); assert.equal(d.pins.length, 1);
  assert.equal(d.gear[0].name, 'spinner'); assert.equal(d.setups[0].name, 'Spinning');
  assert.ok(!Object.hasOwn(d.trips[0], 'dirty'));
});

test('JSON includes local photo bytes rather than empty Blob objects', async () => {
  const s = snapshot(); s.catches[0].photo_blob = new Blob(['photo-bytes'], { type: 'image/jpeg' });
  const d = JSON.parse(await journalJson(s));
  assert.equal(d.scope, 'this_device'); assert.ok(d.exported_at);
  assert.equal(d.catches[0].photo_data_url, 'data:image/jpeg;base64,cGhvdG8tYnl0ZXM=');
  assert.ok(!Object.hasOwn(d.catches[0], 'photo_blob'));
});

test('CSV quotes notes, preserves numbers and includes setup and lure names', () => {
  const csv = journalCsv(snapshot());
  assert.ok(csv.includes('"not synced, ""yet""\nsecond line"'));
  assert.ok(csv.includes(',44,-123,trout,2,'));
  assert.ok(csv.includes(',Spinning,spinner\r\n'));
});

test('CSV handles skunks and protects spreadsheet cells from formulas', () => {
  const s = snapshot(); s.catches = []; s.trips[0].notes = '=1+1';
  const csv = journalCsv(s);
  assert.ok(csv.includes("'=1+1")); assert.equal(csv.split('\r\n').length, 3);
  assert.equal(journalRows({}).trips.length, 0);
});
