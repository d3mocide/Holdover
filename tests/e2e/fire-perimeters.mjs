// Explicit synthetic perimeter around an existing waterbody coordinate, browser-only; never stored.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8056/';
const shots = process.env.SHOTS ?? '/tmp/holdover-fire-perimeter-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (value, label) => { assert.ok(value, label); console.log('PASS ' + label); checks++; };
const region = async (p, x, y) => {
  const png = (await p.screenshot({ clip: { x: x - 70, y: y - 70, width: 140, height: 140 } })).toString('base64');
  return p.evaluate(async (png) => {
    const img = new Image(); img.src = `data:image/png;base64,${png}`; await img.decode();
    const canvas = document.createElement('canvas'); canvas.width = img.width; canvas.height = img.height;
    const g = canvas.getContext('2d'); g.drawImage(img, 0, 0); const data = g.getImageData(0, 0, img.width, img.height).data;
    const counts = new Map(); for (let i = 0; i < data.length; i += 4) { const key = `${data[i]},${data[i+1]},${data[i+2]}`; counts.set(key, (counts.get(key) ?? 0) + 1); }
    const [color, count] = [...counts].sort((a, b) => b[1] - a[1])[0];
    return { color, fraction: count / (data.length / 4) };
  }, png);
};
try {
  for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(), errors = []; p.on('pageerror', (e) => errors.push(e.message));
    const waters = await (await ctx.request.get(new URL('/api/waterbodies', BASE).href)).json();
    const { lon, lat } = waters.find((w) => w.name === 'Tualatin River');
    const feature = { type: 'Feature', properties: { name: 'Synthetic Grasshopper', updated: '2026-10-19T12:00:00Z' }, geometry: { type: 'Polygon', coordinates: [[[lon-.3,lat-.3],[lon+.3,lat-.3],[lon+.3,lat+.3],[lon-.3,lat+.3],[lon-.3,lat-.3]]] } };
    await p.route('**/api/map?**', async (route) => { const res = await route.fetch(), json = await res.json(); json.features = []; await route.fulfill({ response: res, json }); });
    await p.route('**/api/fire/map', (route) => route.fulfill({ json: { zones: { type: 'FeatureCollection', features: [] }, fires: { type: 'FeatureCollection', features: [feature, feature, feature] } } }));
    await p.goto(BASE);
    const nav = (name) => p.getByRole('button', { name, exact: true }).first().click();
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      await nav('Settings'); await p.getByRole('radio', { name: label, exact: true }).check(); await nav('Map');
      const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
      if (await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'false') await p.getByRole('button', { name: 'Show Explore waters', exact: true }).click();
      await explore.getByRole('button', { name: 'Rivers', exact: true }).click(); await explore.getByRole('button', { name: /Tualatin River/ }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor(); await p.getByRole('button', { name: 'Close details', exact: true }).click(); await p.getByRole('button', { name: 'Hide Explore waters', exact: true }).click();
      await p.waitForTimeout(900);
      const canvas = await p.locator('.maplibregl-canvas').boundingBox(), x = canvas.x + canvas.width / 2 + (width >= 900 ? 56 : 0), y = canvas.y + canvas.height / 2;
      const before = await region(p, x, y);
      ok(before.fraction > .995, `${theme}/${size}: perimeter interior has no repeated text labels`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-perimeter.png` });
      await p.mouse.click(x, y);
      const popup = p.getByRole('group', { name: 'Wildfire perimeter details', exact: true }); await popup.waitFor();
      ok(await popup.getByRole('heading', { name: 'Synthetic Grasshopper fire', exact: true }).count() === 1, `${theme}/${size}: popup names the incident once despite duplicate polygon hits`);
      ok(/Perimeter updated/.test(await popup.textContent()) && /2026/.test(await popup.textContent()), `${theme}/${size}: popup shows the perimeter update time`);
      ok(/not a closure notice/.test(await popup.textContent()) && await popup.getByRole('link', { name: 'Official Oregon wildfire information' }).getAttribute('href') === 'https://wildfire.oregon.gov', `${theme}/${size}: popup links to the source without a closure claim`);
      const close = p.getByRole('button', { name: 'Close wildfire details', exact: true }), bounds = await close.boundingBox(), title = await popup.getByRole('heading').boundingBox();
      ok(bounds.width >= 44 && bounds.height >= 44 && title.x + title.width <= bounds.x + 1, `${theme}/${size}: close target stays clear of the incident name`);
      await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => v.id)), []); ok(true, `${theme}/${size}: fire popup axe has zero violations`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-popup.png` }); await close.click();
      await p.getByRole('button', { name: 'Layers', exact: true }).click(); await p.getByLabel('Fire danger and fires', { exact: true }).uncheck(); await p.getByRole('button', { name: 'Layers', exact: true }).click(); await p.waitForTimeout(250);
      const after = await region(p, x, y); await p.mouse.click(x, y);
      ok(after.color !== before.color && await popup.count() === 0, `${theme}/${size}: fire toggle hides the perimeter and its interaction`);
      await p.getByRole('button', { name: 'Layers', exact: true }).click(); await p.getByLabel('Fire danger and fires', { exact: true }).check(); await p.getByRole('button', { name: 'Layers', exact: true }).click();
    }
    ok(!errors.length, `${size}: no browser errors`); await ctx.close();
  }
  console.log(`${checks} fire perimeter checks passed`);
} finally { await b.close(); }
