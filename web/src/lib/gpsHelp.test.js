import test from 'node:test';
import assert from 'node:assert/strict';
import { gpsMessage } from './gpsHelp.js';

test('an insecure origin gets a plain explanation, not the browser error', () => {
  assert.match(gpsMessage({ message: 'Only secure origins are allowed' }, false), /secure \(HTTPS\) address/);
});
test('permission denied and other failures are worded for people', () => {
  assert.match(gpsMessage({ code: 1, message: 'User denied' }, true), /blocked/);
  assert.equal(gpsMessage({ message: 'timeout' }, true), 'No GPS fix (timeout). Pick a waterbody instead.');
});
