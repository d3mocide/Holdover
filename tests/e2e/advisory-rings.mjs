// Synthetic overlap responses on existing coordinates; no stored advisory or measurement is changed.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8054/';
const shots = process.env.SHOTS ?? '/tmp/holdover-ring-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (value, label) => { assert.ok(value, label); console.log('PASS ' + label); checks++; };
const pixels = async (p, points) => {
  const png = (await p.screenshot()).toString('base64');
  return p.evaluate(async ({ png, points }) => {
    const img = new Image(); img.src = `data:image/png;base64,${png}`; await img.decode();
    const canvas = document.createElement('canvas'); canvas.width = img.width; canvas.height = img.height;
    const g = canvas.getContext('2d'); g.drawImage(img, 0, 0);
    return points.map(([x, y]) => [...g.getImageData(Math.round(x), Math.round(y), 1, 1).data].slice(0, 3));
  }, { png, points });
};
const near = (a, b, tolerance = 12) => a.every((v, i) => Math.abs(v - b[i]) <= tolerance);
try {
  for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(), errors = []; p.on('pageerror', (e) => errors.push(e.message));
    await p.route('**/api/map?**', async (route) => {
      const res = await route.fetch(), data = await res.json();
      const river = data.features.find((f) => f.properties.layer === 'river' && f.properties.name === 'Tualatin River');
      data.features = [river,
        { ...river, properties: { layer: 'stocking', id: river.properties.id, name: 'Synthetic river stocking', freshness: 'upcoming', kind: 'river', next_week: '2027-04-19' } },
        { ...river, properties: { layer: 'advisory', id: river.properties.id, name: 'Synthetic river advisory', kind: 'precaution', text: 'Synthetic marker fixture' } },
        { ...river, properties: { layer: 'report', id: river.properties.id, name: 'Synthetic river report', rating: 'excellent', reviewed: true } }
      ];
      await route.fulfill({ response: res, json: data });
    });
    await p.goto(BASE);
    const nav = (name) => p.getByRole('button', { name, exact: true }).first().click();
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      await nav('Settings'); await p.getByRole('radio', { name: label, exact: true }).check(); await nav('Map');
      const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
      if (await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'false') await p.getByRole('button', { name: 'Show Explore waters', exact: true }).click();
      await explore.getByRole('button', { name: 'Rivers', exact: true }).click();
      await explore.getByRole('button', { name: /Tualatin River/ }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await p.getByRole('button', { name: 'Hide Explore waters', exact: true }).click();
      await p.waitForTimeout(800);
      const canvas = await p.locator('.maplibregl-canvas').boundingBox();
      const x = canvas.x + canvas.width / 2 + (width >= 900 ? 56 : 0), y = canvas.y + canvas.height / 2;
      const accent = await p.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--alert').trim());
      const rgb = accent.slice(1).match(/../g).map((v) => parseInt(v, 16));
      const points = [[x, y + 18], [x, y]];
      const before = await pixels(p, points);
      await p.screenshot({ path: `${shots}/${theme}-${size}-stack.png` });
      ok(near(before[0], rgb), `${theme}/${size}: surrounding ring uses the red advisory colour`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-detail.png`, clip: { x: x - 60, y: y - 60, width: 120, height: 120 } });
      await p.mouse.click(x, y + 18);
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      ok(await p.getByRole('group', { name: 'Map items here', exact: true }).count() === 0, `${theme}/${size}: ring click opens its waterbody directly`);
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await p.waitForTimeout(800); await p.mouse.click(x, y);
      const picker = p.getByRole('group', { name: 'Map items here', exact: true }); await picker.waitFor();
      ok(await picker.getByRole('button', { name: /Synthetic river advisory.*Algae advisory/ }).count() === 1, `${theme}/${size}: centre overlap still exposes its advisory`);
      await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => v.id)), []);
      ok(true, `${theme}/${size}: advisory chooser axe has zero violations`);
      await p.getByRole('button', { name: 'Close map items', exact: true }).click();
      await p.getByRole('button', { name: 'Layers', exact: true }).click(); await p.getByLabel('Advisories', { exact: true }).uncheck(); await p.getByRole('button', { name: 'Layers', exact: true }).click();
      await p.waitForTimeout(300);
      const after = await pixels(p, points);
      ok(!near(after[0], rgb, 30), `${theme}/${size}: advisory toggle hides the ring`);
      ok(near(after[1], before[1], 1), `${theme}/${size}: advisory ring leaves the centre marker unchanged`);
      await p.getByRole('button', { name: 'Layers', exact: true }).click(); await p.getByLabel('Advisories', { exact: true }).check(); await p.getByRole('button', { name: 'Layers', exact: true }).click();
      await p.getByRole('button', { name: 'Legend', exact: true }).click();
      const legendRing = p.locator('.legend-body .item').filter({ hasText: 'Algae advisory' });
      ok(await legendRing.locator('circle[fill="none"][stroke-dasharray]').count() === 1, `${theme}/${size}: legend identifies the dashed warning ring`);
      await p.getByRole('button', { name: 'Legend', exact: true }).click();
    }
    ok(!errors.length, `${size}: no browser errors`); await ctx.close();
  }
  console.log(`${checks} advisory ring checks passed`);
} finally { await b.close(); }
