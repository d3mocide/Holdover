// Disposable server only. All journal rows, scores and comparison readings below are explicit synthetic fixtures.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8070';
const shots = process.env.SHOTS ?? '/tmp/holdover-advice-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (v, message) => { assert.ok(v, message); console.log('PASS ' + message); checks++; };
const nav = (p, name) => p.getByRole('button', { name, exact: true }).first().click();
const expand = async p => { if (await p.getByRole('button', { name: 'Show Explore waters', exact: true }).count()) await p.getByRole('button', { name: 'Show Explore waters', exact: true }).click(); };
const explore = p => p.getByRole('region', { name: 'Explore waters', exact: true });
const checkbox = p => p.getByRole('checkbox', { name: 'Use my journal in rankings', exact: true });
const detail = p => p.getByRole('complementary', { name: 'Waterbody details', exact: true });
const comparison = root => root.locator('details.advice');
async function installFixtures(p) {
  const waters = await (await p.request.get(BASE + '/api/waterbodies')).json();
  const a = waters.find(w => w.name === 'Tualatin River'), b = waters.find(w => w.name === 'Clackamas River');
  const at = new Date().toISOString();
  const context = { gauges: [{ site_no: 'synthetic-advice-gauge', values: { discharge_cfs: { value: 100, observed_at: at } }, provisional: true }], date: at.slice(0, 10), weather: null, weather_as_of: null };
  const ranked = { spots: [a, b].map((w, i) => ({ rank: i + 1, waterbody: w, score: i ? 49.8 : 50, coverage: .5, factors: [], report_sentence: null,
    explanation: { source: 'template', text: 'Synthetic browser-test ranking.' }, journal_context: context })) };
  await p.context().route('**/api/spots**', route => route.fulfill({ json: ranked }));
  await p.context().route(/\/api\/(waterbodies|day)\/\d+(\?.*)?$/, async route => {
    const url = new URL(route.request().url()); if (url.pathname.startsWith('/api/day/')) url.searchParams.set('refresh', 'false');
    const res = await route.fetch({ url: url.href }), body = await res.json();
    body.conditions.gauges = context.gauges;
    await route.fulfill({ response: res, json: body });
  });
  return { a, b, context };
}
async function seed(p, water) {
  return p.evaluate(async water => {
    const now = Date.now(), lure = crypto.randomUUID(), setup = crypto.randomUUID();
    const trips = [1, 2, 3].map(i => {
      const stamp = new Date(now - i * 86400000).toISOString();
      return { uuid: crypto.randomUUID(), started_at: stamp, ended_at: stamp, waterbody_id: water.id,
        conditions_json: JSON.stringify({ captured_at: stamp, gauges: [{ site_no: 'synthetic-advice-gauge', values: { discharge_cfs: { value: 100, observed_at: stamp } } }] }),
        setup_uuid: setup, gear_json: JSON.stringify([lure]), updated_at: new Date(now).toISOString(), deleted: 0, dirty: 1 };
    });
    const catches = [{ uuid: crypto.randomUUID(), trip_uuid: trips[0].uuid, species: 'Synthetic test trout', count: 2, gear_uuid: lure, updated_at: new Date(now).toISOString(), dirty: 1, deleted: 0 }];
    const gear = [{ uuid: lure, kind: 'lure', name: 'Synthetic comparison lure', status: 'active', quantity: 1, updated_at: new Date(now).toISOString(), dirty: 1, deleted: 0 }];
    const setups = [{ uuid: setup, name: 'Synthetic comparison setup', item_uuids_json: JSON.stringify([lure]), updated_at: new Date(now).toISOString(), dirty: 1, deleted: 0 }];
    await new Promise((resolve, reject) => {
      const req = indexedDB.open('holdover'); req.onerror = () => reject(req.error); req.onsuccess = () => {
        const d = req.result, tx = d.transaction(['trips', 'catches', 'gear', 'setups'], 'readwrite');
        for (const [name, rows] of Object.entries({ trips, catches, gear, setups })) for (const row of rows) tx.objectStore(name).put(row);
        tx.oncomplete = () => { d.close(); resolve(); }; tx.onerror = () => reject(tx.error);
      };
    }); return trips.map(t => t.uuid);
  }, water);
}
async function scan(p, name) {
  await p.evaluate(axe);
  const violations = await p.evaluate(async () => (await axe.run()).violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })));
  assert.deepEqual(violations, []); ok(true, name + ': full axe clean');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), name + ': no horizontal overflow');
  await p.screenshot({ path: `${shots}/${name}.png` });
}
try {
  if (!process.env.FEATURE_ONLY) for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await browser.newContext({ viewport: { width, height }, serviceWorkers: 'block' }), p = await ctx.newPage(), errors = [];
    p.setDefaultTimeout(15000); p.on('pageerror', e => errors.push(e.message)); const { a } = await installFixtures(p); await p.goto(BASE); await expand(p);
    await checkbox(p).waitFor(); ok(!await checkbox(p).isChecked(), size + ': personal adjustment defaults off');
    await seed(p, a); await p.reload(); await expand(p); await checkbox(p).waitFor();
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      await nav(p, 'Settings'); await p.getByRole('radio', { name: label, exact: true }).check(); await nav(p, 'Map'); await expand(p);
      await checkbox(p).check(); await explore(p).getByText(/journal -0.5/).waitFor();
      ok((await explore(p).locator('button.row .name').first().textContent()) === 'Clackamas River', size + '/' + theme + ': journal reorders Best bets');
      await scan(p, `${size}-${theme}-map`);
      await nav(p, 'Plan'); await checkbox(p).waitFor(); ok(await checkbox(p).isChecked(), size + '/' + theme + ': Plan shares opt-in');
      await p.locator('.spotli').first().waitFor();
      const spot = p.locator('.spotli').filter({ hasText: 'Tualatin River' }).first();
      await comparison(spot).locator(':scope > summary').click();
      await comparison(spot).getByText(/^1 of 3 comparable trips have/).waitFor();
      await comparison(spot).getByText(/Synthetic comparison lure: 2 fish/).waitFor();
      await scan(p, `${size}-${theme}-plan`);
      await nav(p, 'Map'); await expand(p); await explore(p).getByRole('button', { name: /Tualatin River/ }).click();
      await detail(p).getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      await comparison(detail(p)).locator(':scope > summary').click();
      await comparison(detail(p)).getByText(/^1 of 3 comparable trips have/).waitFor();
      await comparison(detail(p)).getByText(/Trips behind this comparison/).click();
      ok(await comparison(detail(p)).getByText(/0 fish recorded/).count() === 2, 'zero-catch evidence remains visible');
      await scan(p, `${size}-${theme}-details`);
      await detail(p).getByRole('button', { name: 'Plan the day', exact: true }).click();
      const day = p.getByRole('region', { name: 'Day-of view', exact: true });
      await comparison(day).locator(':scope > summary').click(); await comparison(day).getByText(/Synthetic comparison setup/).waitFor();
      await scan(p, `${size}-${theme}-day`);
      await p.getByRole('button', { name: 'Back', exact: true }).click();
      if (await p.getByRole('button', { name: 'Close details', exact: true }).count()) await p.getByRole('button', { name: 'Close details', exact: true }).click();
    }
    ok(!errors.length, size + ': no browser exceptions');
    await ctx.unrouteAll({ behavior: 'wait' });
    await ctx.close();
  }
  if (!process.env.UI_ONLY) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } }), p = await ctx.newPage();
    p.setDefaultTimeout(15000); const { a } = await installFixtures(p); await p.goto(BASE); await expand(p); await checkbox(p).waitFor();
    const ids = await seed(p, a); await p.reload(); await expand(p); await checkbox(p).check(); await explore(p).getByText(/journal -0.5/).waitFor();
    await p.evaluate(() => navigator.serviceWorker.ready); await p.reload(); await expand(p); await checkbox(p).waitFor();
    ok(!await checkbox(p).isChecked(), 'opt-in resets on reload; personal history persists');
    // Save routed public bundles through the actual app cache before disconnecting.
    await checkbox(p).check(); await explore(p).getByRole('button', { name: /Tualatin River/ }).click();
    await comparison(detail(p)).locator(':scope > summary').click(); await comparison(detail(p)).getByText(/^1 of 3 comparable trips have/).waitFor();
    await p.getByRole('button', { name: 'Close details', exact: true }).click();
    await p.context().unroute('**/api/spots**'); await p.context().unroute(/\/api\/(waterbodies|day)\/\d+(\?.*)?$/);
    await ctx.setOffline(true); await p.evaluate(() => dispatchEvent(new Event('offline'))); await p.reload(); await expand(p);
    await checkbox(p).check(); await explore(p).getByText(/journal -0.5/).waitFor();
    ok(true, 'airplane-mode app reload reuses public comparison cache and local journal');
    await explore(p).getByRole('button', { name: /Tualatin River/ }).click();
    await comparison(detail(p)).locator(':scope > summary').click(); await comparison(detail(p)).getByText(/^1 of 3 comparable trips have/).waitFor();
    ok(!await comparison(detail(p)).getByText(/Waiting to sync/).first().isVisible(), 'trip evidence is initially collapsed');
    await comparison(detail(p)).getByText('Trips behind this comparison', { exact: true }).click();
    ok(await comparison(detail(p)).getByText(/Waiting to sync/).count() === 3, 'unsynced trips support offline advice');
    await p.getByRole('button', { name: 'Close details', exact: true }).click();
    await ctx.setOffline(false); await nav(p, 'Settings');
    await p.getByLabel('Username', { exact: true }).fill('boss'); await p.getByLabel('Password', { exact: true }).fill('correct-horse-battery'); await p.getByRole('button', { name: 'Sign in', exact: true }).click(); await p.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    let synced;
    for (let i = 0; i < 120; i++) { synced = await p.evaluate(() => fetch('/api/sync/pull').then(r => r.json())); if (ids.every(id => synced.trips.some(t => t.uuid === id))) break; await p.waitForTimeout(250); }
    ok(ids.every(id => synced.trips.some(t => t.uuid === id)), 'anonymous evidence adopts and syncs to its owner on reconnect');
    await p.getByRole('button', { name: 'Sign out', exact: true }).click();
    await p.getByLabel('Username', { exact: true }).fill('sam'); await p.getByLabel('Password', { exact: true }).fill('sams-long-password'); await p.getByRole('button', { name: 'Sign in', exact: true }).click(); await p.getByRole('button', { name: 'Sign out', exact: true }).waitFor();
    const other = await p.evaluate(() => fetch('/api/sync/pull').then(r => r.json())); ok(!other.trips.length && !other.gear.length, 'second account cannot read the owner’s comparison data');
    await installFixtures(p); await p.reload(); await nav(p, 'Map'); await expand(p); await checkbox(p).waitFor(); ok(!await checkbox(p).isChecked(), 'account change resets opt-in');
    await checkbox(p).check(); ok(!await explore(p).getByText(/journal -0.5/).count(), 'second account has no previous-owner score adjustment');
    await explore(p).getByRole('button', { name: /Tualatin River/ }).click(); await comparison(detail(p)).locator(':scope > summary').click();
    await comparison(detail(p)).getByText(/No comparable trips yet/).waitFor(); ok(!await comparison(detail(p)).getByText(/Synthetic comparison lure/).count(), 'same-device account switch removes previous-owner gear advice');
    await ctx.unrouteAll({ behavior: 'wait' });
    await ctx.close();
  }
  console.log(`${checks} journal advice checks passed`);
} finally { await browser.close(); }
