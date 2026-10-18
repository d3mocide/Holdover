import test from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { uuid } from './uuid.js';

const V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

test('uses the platform uuid when there is one', () => {
  assert.match(uuid(), V4);
});
test('still works on an insecure origin, where randomUUID does not exist', () => {
  const real = globalThis.crypto;
  Object.defineProperty(globalThis, 'crypto', { configurable: true, value: { getRandomValues: (a) => webcrypto.getRandomValues(a) } });
  try {
    const ids = new Set(Array.from({ length: 200 }, () => uuid()));
    assert.equal(ids.size, 200);
    for (const id of ids) assert.match(id, V4);
  } finally { Object.defineProperty(globalThis, 'crypto', { configurable: true, value: real }); }
});
