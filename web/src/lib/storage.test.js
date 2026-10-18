import test from 'node:test';
import assert from 'node:assert/strict';
import { fmtBytes, storageSummary } from './storage.js';

test('byte formatting is human and never throws', () => {
  assert.equal(fmtBytes(0), '0 B');
  assert.equal(fmtBytes(1536), '1.5 KB');
  assert.equal(fmtBytes(5 * 1024 * 1024), '5.0 MB');
  assert.equal(fmtBytes(250 * 1024 * 1024), '250 MB');
  assert.equal(fmtBytes(3.2 * 1024 ** 3), '3.2 GB');
  assert.equal(fmtBytes(null), 'unknown');
  assert.equal(fmtBytes(NaN), 'unknown');
});

test('the summary says plainly whether data is protected, and what is at stake if not', () => {
  const ok = storageSummary({ supported: true, persisted: true, usage: 1024 * 1024, quota: 1024 ** 3 });
  assert.equal(ok.tone, 'ok');
  assert.match(ok.text, /1\.0 MB of 1\.0 GB used\. Protected/);
  const bad = storageSummary({ supported: true, persisted: false, usage: null, quota: null });
  assert.equal(bad.tone, 'warn');
  assert.match(bad.text, /Not protected.*not yet synced would be lost/);
  assert.equal(storageSummary({ supported: false }).tone, 'quiet');
});
