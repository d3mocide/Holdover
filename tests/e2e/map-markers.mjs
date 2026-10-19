// Map overlap and gauge card regressions. Only browser responses are changed; all synthetic values are labelled.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8051/';
const shots = process.env.SHOTS ?? '/tmp/holdover-marker-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (value, label) => { assert.ok(value, label); console.log('PASS ' + label); checks++; };
try {
  for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(), errors = []; let reviewed = false, riverId;
    p.on('pageerror', (e) => errors.push(e.message));
    await p.route('**/api/map?**', async (route) => {
      const res = await route.fetch(), data = await res.json();
      const river = data.features.find((f) => f.properties.layer === 'river' && f.properties.name === 'Tualatin River');
      if (river) {
        riverId = river.properties.id;
        const dexter = data.features.find((f) => f.properties.name === 'Dexter Reservoir');
        data.features = [river,
          { ...river, properties: { layer: 'gauge', name: 'Tualatin River at West Linn · test fixture', site_no: '14207500', waterbody_id: riverId, flow_cfs: 221, trend: 'steady', as_of: '2020-01-01T12:00:00Z', stale: false } },
          { ...river, properties: { layer: 'report', name: 'Dexter Reservoir · test fixture', id: dexter.properties.id, rating: 'excellent', reviewed } }
        ];
      }
      await route.fulfill({ response: res, json: data });
    });
    await p.goto(BASE);
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      await p.getByRole('button', { name: 'Settings', exact: true }).first().click();
      await p.getByRole('radio', { name: label, exact: true }).check();
      await p.getByRole('button', { name: 'Map', exact: true }).first().click();
      reviewed = theme === 'redband';
      await p.reload();
      const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
      if (await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'false')
        await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      await explore.getByRole('button', { name: 'Rivers', exact: true }).click();
      await explore.getByRole('button', { name: /Tualatin River/ }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      if (await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'true')
        await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      await p.waitForTimeout(800);
      const canvas = await p.locator('.maplibregl-canvas').boundingBox();
      const x = canvas.x + canvas.width / 2 + (width >= 900 ? 56 : 0), y = canvas.y + canvas.height / 2;
      await p.mouse.click(x + 7, y - 7);
      const picker = p.getByRole('group', { name: 'Map items here', exact: true });
      await picker.waitFor();
      ok((await picker.getByRole('button').first().textContent()).includes('Report · excellent'), `${theme}/${size}: report is first in the overlap picker`);
      await p.evaluate(axe);
      assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => v.id)), []);
      ok(true, `${theme}/${size}: overlap picker axe has zero violations`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-overlap.png` });
      await picker.getByRole('button', { name: /Stream gauge · USGS/ }).click();
      await p.getByRole('group', { name: 'Stream gauge: Tualatin River at West Linn · test fixture', exact: true }).waitFor();
      ok(true, `${theme}/${size}: gauge is reachable underneath the report`);
      await p.getByRole('button', { name: 'Close gauge details', exact: true }).click();
      await p.mouse.click(x + 7, y - 7);
      await picker.getByRole('button', { name: /River · open details/ }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      ok(true, `${theme}/${size}: river is reachable underneath the report`);
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await p.waitForTimeout(800); await p.mouse.click(x + 7, y - 7);
      await picker.getByRole('button', { name: /Report · excellent/ }).click();
      await p.getByRole('heading', { name: 'Dexter Reservoir', exact: true }).waitFor();
      ok(true, `${theme}/${size}: ${reviewed ? 'Reviewed report' : 'AI report'} opens from overlapping river/gauge picker`);
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      // Re-focus Tualatin after the report intentionally selected a different waterbody.
      await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      await explore.getByRole('button', { name: /Tualatin River/ }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      await p.getByRole('button', { name: 'Layers', exact: true }).click();
      await p.getByLabel('Rivers', { exact: true }).uncheck();
      await p.getByLabel('Report ratings', { exact: true }).uncheck();
      await p.getByRole('button', { name: 'Layers', exact: true }).click();
      await p.waitForTimeout(800); await p.mouse.click(x, y);
      const card = p.getByRole('group', { name: 'Stream gauge: Tualatin River at West Linn · test fixture', exact: true });
      await card.waitFor();
      ok((await card.textContent()).includes('Stale'), `${theme}/${size}: old cached observation is marked stale`);
      ok(await card.locator('time[datetime="2020-01-01T12:00:00.000Z"]').count() === 1, `${theme}/${size}: card shows its observation timestamp`);
      const close = p.getByRole('button', { name: 'Close gauge details', exact: true });
      const box = await close.boundingBox(), title = await card.getByRole('heading').boundingBox();
      ok(box.width >= 44 && box.height >= 44 && title.x + title.width <= box.x + 1, `${theme}/${size}: close target does not cover title`);
      ok(await p.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${theme}/${size}: popup fits viewport`);
      await p.evaluate(axe);
      assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => ({ id: v.id, targets: v.nodes.map((n) => n.target) }))), []);
      ok(true, `${theme}/${size}: gauge popup axe has zero violations`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-gauge.png` });
      await card.getByRole('button', { name: 'Open waterbody', exact: true }).click();
      await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
      ok(await close.count() === 0, `${theme}/${size}: waterbody action opens details and dismisses popup`);
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await p.getByRole('button', { name: 'Layers', exact: true }).click();
      await p.getByLabel('Rivers', { exact: true }).check();
      await p.getByLabel('Report ratings', { exact: true }).check();
      await p.getByRole('button', { name: 'Layers', exact: true }).click();
    }
    ok(errors.length === 0, `${size}: no browser errors`);
    await ctx.close();
  }
  console.log(`${checks} marker checks passed`);
} finally { await b.close(); }
