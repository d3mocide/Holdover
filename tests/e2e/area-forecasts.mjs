// Explicit synthetic forecast responses on existing waters; never written to a database.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8058';
const shots = process.env.SHOTS ?? '/tmp/holdover-area-forecast-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (v, label) => { assert.ok(v, label); console.log('PASS ' + label); checks++; };
try {
  for (const [size, width, height] of [['phone',393,852], ['tablet',768,1024], ['desktop',1440,900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(), errors = []; p.on('pageerror', e => errors.push(e.message));
    let weather;
    await p.route('**/api/waterbodies/*', async route => {
      const res = await route.fetch(), json = await res.json();
      if (json.conditions) json.conditions.weather = weather;
      await route.fulfill({ response: res, json });
    });
    await p.route('**/api/day/**', async route => {
      const url = new URL(route.request().url()); url.searchParams.set('refresh', 'false');
      const res = await route.fetch({ url: url.href }), json = await res.json();
      json.conditions.weather = weather;
      await route.fulfill({ response: res, json });
    });
    await p.goto(BASE);
    const nav = name => p.getByRole('button', { name, exact: true }).first().click();
    for (const [theme,label] of [['fir','Fir & Steelhead'], ['redband','Redband'], ['nightbite','Night Bite']]) {
      await nav('Settings'); await p.getByRole('radio', { name: label, exact: true }).check(); await nav('Map');
      const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
      await explore.getByRole('button', { name: 'Rivers', exact: true }).click();
      for (const state of ['area','stale','date','missing']) {
        weather = state === 'missing' ? null : { as_of: '2026-10-19T12:00:00Z', stale: state === 'stale', distance_km: 12.3, source: 'NWS forecast', day: state === 'date' ? null : { temp_f: 55, short: 'Cloudy', precip_pct: 20, wind: '5 mph', wind_dir: 'W' } };
        await explore.getByRole('button', { name: /Tualatin River/ }).click();
        await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
        const tile = p.locator('.tile').filter({ has: p.getByText('Forecast', { exact: true }) });
        await tile.waitFor();
        const text = await tile.textContent();
        if (state === 'area' || state === 'stale') ok(text.includes('55°F') && text.includes('NWS point 12 km away') && text.includes('NWS as of'), `${theme}/${size}/${state}: area forecast has value, distance and source time`);
        if (state === 'stale') ok(text.includes('Stale'), `${theme}/${size}: stale area forecast remains labelled`);
        if (state === 'date') ok(text.includes('No forecast available for this date') && !text.includes('No forecast cached'), `${theme}/${size}: unavailable date is distinct from missing area cache`);
        if (state === 'missing') ok(text.includes('No forecast cached for this area yet'), `${theme}/${size}: missing area cache explained`);
        ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${theme}/${size}/${state}: no horizontal overflow`);
        await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map(v => v.id)), []);
        ok(true, `${theme}/${size}/${state}: axe clean`);
        await tile.scrollIntoViewIfNeeded(); await p.screenshot({ path: `${shots}/${theme}-${size}-${state}.png` });
        if (state === 'area') {
          await p.getByRole('button', { name: 'Plan the day', exact: true }).click();
          await p.getByRole('button', { name: 'Back', exact: true }).waitFor();
          const dayTile = p.locator('.tile').filter({ has: p.getByText('Forecast', { exact: true }) });
          await dayTile.waitFor();
          ok((await dayTile.textContent()).includes('NWS point 12 km away'), `${theme}/${size}: day view retains area provenance`);
          await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map(v => v.id)), []);
          ok(true, `${theme}/${size}: day view axe clean`);
          await dayTile.scrollIntoViewIfNeeded(); await p.screenshot({ path: `${shots}/${theme}-${size}-day.png` });
          await p.getByRole('button', { name: 'Back', exact: true }).click();
        }
        await p.getByRole('button', { name: 'Close details', exact: true }).click();
      }
    }
    ok(errors.length === 0, `${size}: no browser errors`); await ctx.close();
  }
  console.log(`${checks} area forecast checks passed`);
} finally { await b.close(); }
