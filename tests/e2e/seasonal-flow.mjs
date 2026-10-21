// Built app on a disposable fixture only. Baselines/readings are synthetic (seed-seasonal.py).
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8080', shots = process.env.SHOTS ?? '/tmp/holdover-seasonal-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (v, label) => { assert.ok(v, label); checks++; console.log('PASS ' + label); };
const nav = (p, name) => p.getByRole('button', { name, exact: true }).first().click();
const explore = p => p.getByRole('region', { name: 'Explore waters', exact: true });
const card = root => root.getByRole('group', { name: 'Seasonal flow context', exact: true });
const summary = root => card(root).locator(':scope > details > summary');
const expand = async p => { if (await p.getByRole('button', { name: 'Show Explore waters', exact: true }).count()) await p.getByRole('button', { name: 'Show Explore waters', exact: true }).click(); };
async function openRiver(p) {
  await nav(p, 'Map'); await expand(p); await explore(p).getByRole('button', { name: 'Rivers', exact: true }).click();
  await explore(p).getByRole('button', { name: /Tualatin River/ }).click();
  const sheet = p.getByRole('complementary', { name: 'Waterbody details', exact: true });
  await sheet.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  return sheet;
}
async function scan(p, label) {
  await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))), []);
  ok(true, label + ': full axe clean');
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), label + ': no horizontal overflow');
  await p.screenshot({ path: `${shots}/${label}.png` });
}
try {
 if (!process.env.OFFLINE_ONLY) for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
  const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' }), p = await ctx.newPage(), errors = [];
  p.setDefaultTimeout(15000); p.on('pageerror', e => errors.push(e.message));
  // No weather source refreshes in fixtures; historical endpoints only read the disposable cache.
  await p.route('**/api/day/**', async route => { const url = new URL(route.request().url()); url.searchParams.set('refresh', 'false'); const r = await route.fetch({ url: url.href }); await route.fulfill({ response: r }); });
  await p.goto(BASE);
  const waters = await (await p.request.get(BASE + '/api/waterbodies')).json(), water = waters.find(w => w.name === 'Tualatin River');
  let variant = 'ready';
  await p.route(`**/api/waterbodies/${water.id}`, async route => {
    const response = await route.fetch(), data = await response.json();
    for (const g of data.conditions.gauges) {
      if (variant === 'stale') { g.seasonal.as_of = new Date(Date.now() - 60 * 86400000).toISOString(); g.seasonal.stale = false; }
      if (variant === 'insufficient') { g.seasonal.status = 'insufficient'; g.seasonal.selected = { samples: 10, expected: 150, years: [2025], median: null }; g.seasonal.series = g.seasonal.series.map(row => ({ ...row, median: null, p25: null, p75: null, samples: 10, years: [2025] })); if (g.seasonal.current) g.seasonal.current.position = null; }
      if (variant === 'disabled') g.seasonal = { ...g.seasonal, status: 'disabled', current: null, series: [] };
      if (variant === 'legacy') delete g.seasonal;
    }
    await route.fulfill({ response, json: data });
  });
  for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
    await nav(p, 'Settings'); await p.getByRole('radio', { name: label, exact: true }).check();
    await p.getByText('Downloads disabled (USGS API key)', { exact: true }).waitFor(); await scan(p, `${size}-${theme}-settings`);
    variant = 'ready'; const sheet = await openRiver(p); await summary(sheet).click();
    await card(sheet).getByRole('img').waitFor();
    ok(await card(sheet).getByText(/150\/150 daily values/).isVisible(), 'baseline exposes exact date-window coverage');
    ok(await summary(sheet).boundingBox().then(r => r.height >= 44), 'seasonal disclosure has a 44px target');
    await card(sheet).getByText('Read historical values and coverage', { exact: true }).click();
    ok(await card(sheet).locator('li').count() === 61, 'all 61 chart days have a textual alternative');
    await scan(p, `${size}-${theme}-river`);
    if (await card(sheet).getByRole('combobox').count()) {
      const picker = card(sheet).getByLabel('Seasonal gauge', { exact: true }); const option = picker.locator('option').nth(1);
      const value = await option.getAttribute('value'), name = await option.textContent();
      await picker.selectOption(value); await card(sheet).getByText(`${name} · USGS`, { exact: false }).waitFor(); await card(sheet).getByRole('img').waitFor(); ok(true, 'alternate river gauge has its own seasonal baseline');
    }
    await sheet.getByRole('button', { name: 'Plan the day', exact: true }).click();
    const day = p.getByRole('region', { name: 'Day-of view', exact: true }); await summary(day).click(); await card(day).getByRole('img').waitFor();
    await scan(p, `${size}-${theme}-day`); await p.getByRole('button', { name: 'Back', exact: true }).click();
    if (await p.getByRole('button', { name: 'Close details', exact: true }).count()) await p.getByRole('button', { name: 'Close details', exact: true }).click();
    await nav(p, 'Plan'); await p.getByRole('button', { name: 'Steelhead & salmon', exact: true }).click();
    const spot = p.locator('.spotli').filter({ hasText: 'Tualatin River' }).first(); await summary(spot).click(); await card(spot).getByRole('img').waitFor();
    await scan(p, `${size}-${theme}-plan`);
    for (const state of ['stale', 'insufficient', 'disabled']) {
      variant = state; const target = await openRiver(p); await summary(target).click();
      if (state === 'stale') { await card(target).getByText(/Stale baseline/).waitFor(); ok(!await card(target).getByText(/Latest flow (above|below|within)/).count(), 'expired cached baseline hides comparative classification'); }
      if (state === 'insufficient') await card(target).getByText(/Not enough coverage/).waitFor();
      if (state === 'disabled') await card(target).getByText(/Historical downloads are disabled/).waitFor();
      await scan(p, `${size}-${theme}-${state}`); await target.getByRole('button', { name: 'Close details', exact: true }).click();
    }
  }
  if (size === 'desktop') {
    variant = 'legacy';
    await p.route('**/api/gauges/*/seasonal?*', route => route.fulfill({ status: 404, json: { detail: 'Synthetic old-server endpoint missing' } }));
    const legacy = await openRiver(p); await summary(legacy).click();
    await card(legacy).getByText(/No saved seasonal chart/).waitFor();
    ok(!await card(legacy).getByText('Loading seasonal context…', { exact: true }).count(), 'older cached bundles show a missing-chart message without a perpetual loading state');
    await scan(p, 'desktop-legacy-missing-chart');
  }
  ok(!errors.length, size + ': no browser errors'); await ctx.close();
 }
 if (!process.env.UI_ONLY) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }), p = await ctx.newPage(); p.setDefaultTimeout(15000);
  await p.goto(BASE); const sheet = await openRiver(p); await summary(sheet).click(); await card(sheet).getByRole('img').waitFor();
  await p.getByRole('button', { name: 'Hide Explore waters', exact: true }).click();
  await p.getByRole('button', { name: 'Prepare for offline', exact: true }).first().click();
  const dialog = p.getByRole('dialog', { name: 'Prepare for offline', exact: true });
  await dialog.getByLabel('Area to save', { exact: true }).selectOption('trip'); await dialog.getByLabel('Trip waterbody', { exact: true }).selectOption({ label: 'Tualatin River' });
  await dialog.getByLabel('Area around the pin', { exact: true }).selectOption('5'); await dialog.getByLabel('Map detail', { exact: true }).selectOption('8');
  await dialog.getByLabel('Trip fishery', { exact: true }).selectOption('steelhead');
  await dialog.getByRole('button', { name: 'Save for offline', exact: true }).click(); await dialog.getByRole('status').filter({ hasText: /^Saved/ }).waitFor({ timeout: 60000 });
  await dialog.getByRole('button', { name: 'Close', exact: true }).click(); await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await nav(p, 'Plan'); await p.getByRole('button', { name: 'Steelhead & salmon', exact: true }).click();
  const spot = p.locator('.spotli').filter({ hasText: 'Tualatin River' }).first(); await summary(spot).click(); await card(spot).getByRole('img').waitFor();
  await p.evaluate(() => navigator.serviceWorker.ready); await p.reload(); await ctx.setOffline(true); await p.reload();
  await expand(p); await explore(p).getByRole('button', { name: 'Steelhead & salmon', exact: true }).click();
  const offlineSheet = await openRiver(p); await summary(offlineSheet).click(); await card(offlineSheet).getByRole('img').waitFor(); ok(true, 'airplane-mode reload retains full river baseline');
  await offlineSheet.getByRole('button', { name: 'Plan the day', exact: true }).click();
  const day = p.getByRole('region', { name: 'Day-of view', exact: true }); await day.getByRole('button', { name: 'Tomorrow', exact: true }).click();
  await summary(day).click(); await card(day).getByRole('img').waitFor(); ok(true, 'prepared exact-date offline day includes full seasonal chart');
  await p.getByRole('button', { name: 'Back', exact: true }).click(); if (await p.getByRole('button', { name: 'Close details', exact: true }).count()) await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await nav(p, 'Plan'); await p.getByRole('button', { name: 'Steelhead & salmon', exact: true }).click();
  const offlineSpot = p.locator('.spotli').filter({ hasText: 'Tualatin River' }).first(); await summary(offlineSpot).click(); await card(offlineSpot).getByRole('img').waitFor(); ok(true, 'previously opened Plan seasonal chart survives offline reload');
  await ctx.close();
 }
 console.log(`${checks} seasonal flow checks passed`);
} finally { await b.close(); }
