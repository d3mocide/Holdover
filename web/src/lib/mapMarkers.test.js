import test from 'node:test';
import assert from 'node:assert/strict';
import { markerHit } from './mapMarkers.js';
import { markers } from './icons.js';

test('a report wins an overlap click, including an unreviewed AI reading', () => {
  const hit = (id, reviewed = true) => ({ layer: { id }, properties: { reviewed } });
  const river = hit('river-pts'), gauge = hit('gauge-pts'), report = hit('report-badge', false);
  assert.equal(markerHit([gauge, report, river]), report);
  assert.equal(markerHit([river, gauge, report]), report);
  assert.equal(markerHit([gauge, river]), river);
  assert.equal(markerHit([]), null);
});

test('stocking states have different geometry without relying on hue', () => {
  const c = { main: 'currentColor', bg: 'transparent' };
  const art = ['stocking', 'stocking_recent', 'stocking_older', 'stocking_scheduled'].map((name) => markers[name](c));
  assert.equal(new Set(art).size, 4);
  assert.ok(art.every((svg) => svg.includes('<path'))); // every state retains the fish
  assert.match(art[2], /stroke-dasharray/);
  assert.match(art[3], /<rect/); // calendar, rather than another empty circle
});
