import test from 'node:test';
import assert from 'node:assert/strict';
import { to12, formatTime, formatClockText } from './clockFormat.js';

test('12-hour edge cases: midnight, noon, single digit hours', () => {
  assert.equal(to12(0, 5), '12:05 AM');
  assert.equal(to12(12, 0), '12:00 PM');
  assert.equal(to12(7, 29), '7:29 AM');
  assert.equal(to12(18, 18), '6:18 PM');
  assert.equal(to12(23, 59), '11:59 PM');
});
test('timestamps follow the mode, and bad input is empty', () => {
  const iso = new Date(2026, 9, 18, 17, 46).toISOString();
  assert.equal(formatTime(iso, '12'), '5:46 PM');
  assert.equal(formatTime(iso, '24'), '17:46');
  assert.equal(formatTime('', '12'), '');
  assert.equal(formatTime('nonsense', '12'), '');
});
test('24-hour times inside text are rewritten, other text and numbers are not', () => {
  assert.equal(formatClockText('07:29–18:18', '12'), '7:29 AM–6:18 PM');
  assert.equal(formatClockText('Stocked: 5,060 fish. Light 07:29-18:21. Flow 1,240 cfs (+0%).', '12'), 'Stocked: 5,060 fish. Light 7:29 AM-6:21 PM. Flow 1,240 cfs (+0%).');
  assert.equal(formatClockText('ratio 99:99 and 25:00', '12'), 'ratio 99:99 and 25:00');
  assert.equal(formatClockText('Light 07:29-18:21.', '24'), 'Light 07:29-18:21.');
  assert.equal(formatClockText(null, '12'), null);
});
