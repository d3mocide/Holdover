// Airplane-mode journal flow. See tests/e2e/README.md. Needs: playwright-core, a running server with a
// seeded DB, the toy tiles (scripts/make_test_pmtiles.py), and HOLDOVER_TOKEN=testtoken.
import { chromium } from 'playwright-core';
import { execSync } from 'child_process';
const sql = (q) => execSync(`python3 -c "import sqlite3;print(sqlite3.connect('${process.env.E2E_DB}').execute(\\"${q}\\").fetchall())"`).toString().trim();
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
const p = await ctx.newPage();
const errs = []; p.on('pageerror', e => errs.push('pageerror ' + e.message));
const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) process.exitCode = 1; };

await p.goto(process.env.BASE_URL ?? 'http://localhost:8000/');
await p.evaluate(() => localStorage.setItem('holdover.token', 'testtoken'));
await p.evaluate(async () => { await navigator.serviceWorker.ready; });
await p.reload(); await p.waitForTimeout(3000);
ok(await p.evaluate(() => !!navigator.serviceWorker.controller), 'service worker controls the page');

// select a stocked waterbody with a gauge, then prepare for offline
await p.getByRole('button', { name: /Dexter Reservoir/ }).click(); await p.waitForTimeout(1000);
await p.getByRole('button', { name: 'Prepare for offline' }).first().click();
await p.getByLabel('Map detail').selectOption('8');
await p.getByRole('button', { name: 'Save for offline' }).click();
await p.getByRole('status').filter({ hasText: /Saved/ }).waitFor({ timeout: 30000 });
console.log('prepare:', await p.getByRole('status').filter({ hasText: /Saved/ }).innerText());
const tilesSaved = await p.evaluate(() => new Promise((res) => { const r = indexedDB.open('holdover'); r.onsuccess = () => { const t = r.result.transaction('tiles').objectStore('tiles').count(); t.onsuccess = () => res(t.result); }; }));
ok(tilesSaved > 0, `map tiles stored in IndexedDB (${tilesSaved})`);
await p.getByRole('button', { name: 'Close', exact: true }).click();

// ---- airplane mode ----
await ctx.setOffline(true);
await p.reload(); await p.waitForTimeout(3500);
ok((await p.title()) === 'Holdover', 'app shell loads offline');
ok(await p.getByRole('button', { name: /Dexter Reservoir/ }).isVisible(), 'cached stocking list renders offline');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/offline-map.png' : undefined });

await p.getByRole('button', { name: 'Journal' }).click();
await p.getByRole('button', { name: /Log (a|your first) trip/ }).first().click();
await p.getByLabel('Where').selectOption({ label: 'Dexter Reservoir' });
ok(await p.getByText('Saved on this phone, syncs when you have signal').isVisible(), 'offline banner shown');
await p.getByLabel('Species 1').fill('rainbow trout');
await p.getByRole('button', { name: /More/ }).first().click();
await p.getByRole('button', { name: /More/ }).first().click();
await p.getByLabel('Lure or method').fill('1/8 oz spinner');
await p.getByRole('button', { name: 'Save trip' }).click();
await p.locator('li.card').getByText('Waiting to sync').waitFor({ timeout: 10000 });
ok(true, 'trip saved locally while offline');
console.log('card:', (await p.locator('li.card').first().innerText()).replace(/\n/g,' | '));
ok(await p.getByText(/conditions cached/).first().isVisible(), 'conditions captured from cache and marked cached');
ok(sql('select count(*) from trip') === '[(0,)]', 'nothing on server yet');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/journal-offline.png' : undefined });

// ---- back online ----
await ctx.setOffline(false);
await p.locator('li.card').getByText(/^\s*Synced/).waitFor({ timeout: 20000 });
ok(sql('select count(*) from trip') === '[(1,)]', 'trip synced to server after reconnect');
ok(sql('select count(*), sum(count) from catch') === '[(1, 2)]', 'catch synced (1 row, count 2)');
console.log(sql("select conditions_source, species from trip join catch on catch.trip_uuid=trip.uuid"));
await p.waitForTimeout(500);
// duplicate push of the same rows: mark dirty again and sync
await p.evaluate(async () => { const r = indexedDB.open('holdover'); await new Promise(res => r.onsuccess = res);
  const db = r.result; const tx = db.transaction(['trips','catches'], 'readwrite');
  for (const n of ['trips','catches']) { const st = tx.objectStore(n); const all = st.getAll(); all.onsuccess = () => all.result.forEach(x => { x.dirty = 1; st.put(x); }); }
  await new Promise(res => tx.oncomplete = res); });
await p.evaluate(() => dispatchEvent(new Event('online')));
await p.waitForTimeout(2500);
ok(sql('select count(*) from trip') === '[(1,)]' && sql('select count(*) from catch') === '[(1,)]', 'duplicate push created no duplicates');
console.log(errs.join('\n') || 'no page errors');
await b.close();
