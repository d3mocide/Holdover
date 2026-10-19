// Exercise the real Vite modules in a fresh browser with explicitly mocked day bundles. No server writes.
// DEV_URL defaults to the local Docker dev stack. The built-shell offline flow is tested by offline.mjs.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
const DEV = process.env.DEV_URL ?? 'http://localhost:5173';
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox'] });
let checks = 0;
const ok = (v, label) => { assert.ok(v, label); console.log('PASS ' + label); checks++; };
try {
  const ctx = await b.newContext({ timezoneId: 'America/Los_Angeles', serviceWorkers: 'block' });
  const p = await ctx.newPage();
  await p.route(`${DEV}/cache-test`, (r) => r.fulfill({ contentType: 'text/html', body: '<!doctype html><title>Day-cache test</title>' }));
  await p.goto(`${DEV}/cache-test`);
  // A real v2 IndexedDB with existing personal data, before importing the new v3 module.
  await p.evaluate(() => new Promise((resolve, reject) => {
    const req = indexedDB.open('holdover', 20);
    req.onupgradeneeded = () => {
      const db = req.result;
      for (const [name, key, indexes] of [['trips', 'uuid', ['updated_at', 'dirty', 'waterbody_id']], ['catches', 'uuid', ['trip_uuid', 'dirty']],
        ['pins', 'uuid', ['dirty']], ['meta', 'key', []], ['cond', 'waterbody_id', []], ['tiles', 'key', []],
        ['gear', 'uuid', ['kind', 'dirty', 'updated_at']], ['setups', 'uuid', ['dirty', 'updated_at']]]) {
        const st = db.createObjectStore(name, { keyPath: key }); indexes.forEach((i) => st.createIndex(i, i));
      }
    };
    req.onerror = () => reject(req.error);
    req.onsuccess = () => {
      const db = req.result, tx = db.transaction('trips', 'readwrite');
      tx.objectStore('trips').put({ uuid: 'existing-trip', notes: 'Preserve this journal', dirty: 1 });
      tx.oncomplete = () => { db.close(); resolve(); };
    };
  }));
  await p.clock.install({ time: new Date('2026-10-20T02:00:00Z') }); // still Oct 19 in Oregon
  const dates = [];
  await p.route('**/api/day/*', async (route) => {
    const url = new URL(route.request().url()), date = url.searchParams.get('date'), fishery = url.searchParams.get('fishery');
    dates.push(date);
    await route.fulfill({ json: { conditions: { weather: { day: { fixture: `${date}/${fishery}` } },
      gauges: [], stocking: [], advisories: [], daylight: {}, moon: {} }, pack: { intro: `Fixture ${date}/${fishery}` } } });
  });
  await p.evaluate(async () => {
    window.cacheTest = await import('/src/lib/conditions.js');
    window.cacheDb = (await import('/src/lib/db.js')).db;
    await cacheDb.open();
  });
  ok(await p.evaluate(async () => (await cacheDb.trips.get('existing-trip')).notes === 'Preserve this journal'), 'v2 to v3 upgrade preserves existing unsynced journal');
  await p.evaluate(async () => {
    await cacheTest.loadDay(900001, '2026-10-19', 'trout');
    await cacheTest.loadDay(900001, '2026-10-20', 'trout');
    await cacheTest.loadDay(900001, '2026-10-19', 'steelhead');
  });
  ok(await p.evaluate(async () => (await cacheDb.days.count()) === 3), 'separate cache entries for each date and fishery');
  ok(await p.evaluate(async () => (await cacheDb.cond.get(900001)).date === '2026-10-19'), 'future forecast does not replace current conditions cache');
  await p.evaluate(() => cacheTest.captureConditions(900001));
  ok(dates.at(-1) === '2026-10-19', 'evening capture requests Oregon date instead of UTC tomorrow');
  await p.unroute('**/api/day/*'); await ctx.setOffline(true);
  for (const [day, fishery] of [['2026-10-19', 'trout'], ['2026-10-20', 'trout'], ['2026-10-19', 'steelhead']]) {
    const r = await p.evaluate(async ([d, f]) => cacheTest.loadDay(900001, d, f), [day, fishery]);
    ok(r.source === 'cached' && r.data.pack.intro === `Fixture ${day}/${fishery}`, `offline bundle matches ${day}/${fishery}`);
  }
  const missing = await p.evaluate(async () => {
    try { await cacheTest.loadDay(900001, '2026-10-19', 'warmwater'); return false; }
    catch (e) { return e.message.includes('No saved day view'); }
  });
  ok(missing, 'uncached fishery is refused rather than borrowing another pack list');
  const legacy = await p.evaluate(async () => {
    await cacheDb.cond.put({ waterbody_id: 900002, date: '2026-10-19', payload: { pack: { intro: 'Unknown legacy fishery' } } });
    try { await cacheTest.loadDay(900002, '2026-10-19', 'trout'); return false; }
    catch (e) { return e.message.includes('No saved day view'); }
  });
  ok(legacy, 'legacy cache without fishery metadata is not guessed to be trout');
  const capture = await p.evaluate(() => cacheTest.captureConditions(900001));
  ok(capture.source === 'cached' && capture.json.weather.fixture === '2026-10-19/trout', 'offline trip capture keeps dated cached observations');
  console.log(`${checks} day-cache checks passed`);
} finally { await b.close(); }
