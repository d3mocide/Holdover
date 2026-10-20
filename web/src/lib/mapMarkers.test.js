import test from 'node:test';
import assert from 'node:assert/strict';
import { markerChoices, markerDescription } from './mapMarkers.js';
import { markers } from './icons.js';

test('a report is first in an overlap picker, including an unreviewed AI reading', () => {
  const hit = (id, reviewed = true) => ({ layer: { id }, properties: { id: 1, reviewed } });
  const river = hit('river-pts'), gauge = hit('gauge-pts'), report = hit('report-badge', false);
  assert.equal(markerChoices([gauge, report, river])[0], report);
  assert.equal(markerChoices([river, gauge, report])[0], report);
  assert.equal(markerChoices([gauge, river])[0], river);
  assert.deepEqual(markerChoices([]), []);
});

test('an overlap keeps all layers reachable, removes tile duplicates and puts reports first', () => {
  const hit = (id, layer) => ({ layer: { id: layer }, properties: { id } });
  const river = hit(1, 'river-pts'), gauge = hit(1, 'gauge-pts'), report = hit(1, 'report-badge');
  assert.deepEqual(markerChoices([river, gauge, river, report]), [report, river, gauge]);
  assert.deepEqual(markerChoices([hit(1, 'home-pts')]), []);
});

test('a Santiam-style public stack puts advisory above stocking, river and gauge', () => {
  const feature = (layer) => ({ layer: { id: layer }, properties: { id: 1, name: 'Synthetic Santiam stack' } });
  const layers = ['gauge-pts', 'advisory-ring', 'stocking-pts', 'river-pts'];
  assert.deepEqual(markerChoices(layers.map(feature)).map((f) => f.layer.id), ['advisory-ring', 'stocking-pts', 'river-pts', 'gauge-pts']);
});

test('nearby Fall Creek waters remain separate and show their own schedule weeks', () => {
  const feature = (id, name, kind, next_week) => ({ layer: { id: 'stocking-pts' }, properties: { id, name, kind, freshness: 'upcoming', next_week } });
  const creek = feature(19, 'Fall Creek (Willamette R)', 'creek', '2027-04-19');
  const reservoir = feature(20, 'Fall Creek Reservoir', 'reservoir', '2027-03-15');
  assert.equal(markerChoices([creek, reservoir, creek]).length, 2);
  assert.equal(markerDescription(creek), 'creek · Scheduled stocking · week of Apr 19, 2027 · may change');
  assert.equal(markerDescription(reservoir), 'reservoir · Scheduled stocking · week of Mar 15, 2027 · may change');
});

test('personal markers with the same label at different coordinates remain reachable', () => {
  const pin = (lon) => ({ layer: { id: 'journal-pts' }, properties: { label: 'My pin' }, geometry: { coordinates: [lon, 45] } });
  const a = pin(-123), b = pin(-122);
  assert.deepEqual(markerChoices([a, a, b]), [a, b]);
});

test('stocking states have different geometry without relying on hue', () => {
  const c = { main: 'currentColor', bg: 'transparent' };
  const art = ['stocking', 'stocking_recent', 'stocking_older', 'stocking_scheduled'].map((name) => markers[name](c));
  assert.equal(new Set(art).size, 4);
  assert.ok(art.every((svg) => svg.includes('<path'))); // every state retains the fish
  assert.match(art[2], /stroke-dasharray/);
  assert.match(art[3], /<rect/); // calendar, rather than another empty circle
});

test('an advisory badge has an opaque body so underlying stocking art cannot bleed through', () => {
  const art = markers.advisory({ accent: 'warning', bg: 'ground' });
  assert.match(art, /<circle[^>]+fill="warning"/);
  assert.doesNotMatch(art, /opacity|fill="none"/);
  assert.match(art, /stroke="ground"/);
});
