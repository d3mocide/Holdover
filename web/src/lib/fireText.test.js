import test from 'node:test';
import assert from 'node:assert/strict';
import { dangerText, dangerHigh, fireLine, nearbyText } from './fireText.js';

test('danger text names the level and area, and is honest outside ODF land', () => {
  assert.equal(dangerText({ covered: true, level: 2, label: 'Moderate', area: 'JD-2' }), 'Moderate (level 2 of 4), ODF area JD-2');
  assert.match(dangerText({ covered: false }), /outside the lands ODF protects/);
  assert.equal(dangerText(null), null);
});
test('high and extreme are flagged, low and uncovered are not', () => {
  assert.equal(dangerHigh({ covered: true, level: 3 }), true);
  assert.equal(dangerHigh({ covered: true, level: 4 }), true);
  assert.equal(dangerHigh({ covered: true, level: 2 }), false);
  assert.equal(dangerHigh({ covered: false }), false);
  assert.equal(dangerHigh(null), false);
});
test('fire line shows distance, size, containment and the perimeter date', () => {
  const s = fireLine({ name: 'Austin', distance_km: 2.4, acres: 12888, percent_contained: 98, updated: '2026-09-29T12:00+00:00', inside: false });
  assert.match(s, /^Austin fire: 2 km away; 12,888 acres, 98% contained, perimeter updated Sep 2[89]$/);
});
test('missing containment and being inside are stated plainly', () => {
  const s = fireLine({ name: '407 DET', distance_km: 0, acres: null, percent_contained: null, updated: null, inside: true });
  assert.equal(s, '407 DET fire: this waterbody is inside the mapped fire area; containment not reported');
});
test('no fires is worded as not listed, never as no fire; unknown stays silent', () => {
  assert.match(nearbyText({ fires: [], near_km: 50 }), /No active wildfire perimeter within 50 km in the data NIFC publishes/);
  assert.equal(nearbyText({ fires: [{}], near_km: 50 }), null);
  assert.equal(nearbyText(null), null);
});
