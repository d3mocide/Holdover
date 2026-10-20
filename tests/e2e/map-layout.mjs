// Shared title alignment, Explore selectors and two nearby waters. Synthetic schedules exist only in browser responses.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8052/';
const shots = process.env.SHOTS ?? '/tmp/holdover-map-layout-shots';
await fs.mkdir(shots, { recursive: true });
const axe = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const ok = (condition, label) => { assert.ok(condition, label); console.log('PASS ' + label); checks++; };
try {
  for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(), errors = [];
    p.on('pageerror', (e) => errors.push(e.message));
    const waters = await (await ctx.request.get(new URL('/api/waterbodies', BASE).href)).json();
    const creek = waters.find((w) => w.name === 'Fall Creek (Willamette R)'), reservoir = waters.find((w) => w.name === 'Fall Creek Reservoir');
    await p.route('**/api/map?**', async (route) => {
      const res = await route.fetch(), data = await res.json();
      data.features = [creek, reservoir].map((w, i) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [w.lon, w.lat] }, properties: { layer: 'stocking', id: w.id, name: `${w.name} · test fixture`, kind: w.kind, freshness: 'upcoming', next_week: i ? '2027-03-15' : '2027-04-19' } }));
      await route.fulfill({ response: res, json: data });
    });
    await p.goto(BASE);
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      const nav = (name) => p.getByRole('button', { name, exact: true }).first().click();
      await nav('Settings'); await p.getByRole('radio', { name: label, exact: true }).check();
      let planSize;
      for (const view of ['Settings', 'Plan', 'Reports', 'Journal', 'Gear', 'Gauges']) {
        await nav(view); await p.locator('.page-header').waitFor();
        const aligned = await p.locator('.page-header').evaluate((el) => {
          const title = el.querySelector('h1').getBoundingClientRect(), badge = el.querySelector('.title > span').getBoundingClientRect();
          return Math.abs(title.y + title.height / 2 - badge.y - badge.height / 2) < 1 && badge.width === 48 && badge.height === 48 && Math.abs(title.x - badge.right - 14) < 1;
        });
        if (view === 'Plan') { await p.waitForTimeout(350); planSize = await p.locator('.planner').boundingBox(); }
        ok(aligned, `${theme}/${size}/${view}: title and 48px icon share the same centre and gap`);
      }
      await nav('Map');
      const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
      if (await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'false') await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      const exploreSize = await explore.boundingBox();
      ok(Math.abs(exploreSize.width - planSize.width) < 1 && Math.abs(exploreSize.height - planSize.height) < 1, `${theme}/${size}: Explore matches Plan width and height`);
      const titleSize = await explore.locator('.t strong').evaluate((el) => getComputedStyle(el).fontSize);
      ok(titleSize === '24px', `${theme}/${size}: Explore uses the Plan title size`);
      const hide = p.getByRole('button', { name: 'Hide Explore waters', exact: true });
      await hide.click();
      ok(await explore.getByRole('button', { name: 'Explore waters', exact: true }).getAttribute('aria-expanded') === 'false', `${theme}/${size}: edge control collapses Explore`);
      await p.getByRole('button', { name: 'Show Explore waters', exact: true }).click();
      ok(await explore.getByRole('searchbox', { name: 'Search all waters' }).isVisible(), `${theme}/${size}: edge control restores Explore`);
      const tabs = explore.getByRole('group', { name: 'Browse waters', exact: true });
      for (const label of ['Rivers', 'Favorites', 'Best bets']) {
        await tabs.getByRole('button', { name: label, exact: true }).click();
        ok(await tabs.getByRole('button', { name: label, exact: true }).getAttribute('aria-pressed') === 'true', `${theme}/${size}: ${label} selector is active`);
      }
      const geometry = await explore.evaluate((el) => {
        const title = el.querySelector('.t strong').getBoundingClientRect(), badge = el.querySelector('.t > span').getBoundingClientRect();
        const tabs = [...el.querySelectorAll('.selector-tab')].map((el) => el.getBoundingClientRect());
        return Math.abs(title.y + title.height / 2 - badge.y - badge.height / 2) < 1 && tabs.every((r) => r.height >= 44 && Math.abs(r.y - tabs[0].y) < 1) && el.getBoundingClientRect().right <= innerWidth;
      });
      ok(geometry, `${theme}/${size}: Explore badge aligns and three selectors fit one 44px row`);
      if (width >= 900) {
        await p.setViewportSize({ width: 900, height: 900 }); await p.waitForTimeout(350);
        const legend = await p.getByRole('button', { name: 'Legend', exact: true }).boundingBox(), layers = await p.getByRole('button', { name: 'Layers', exact: true }).boundingBox();
        ok(legend.x + legend.width <= layers.x, `${theme}/900px: Legend and Layers do not overlap`);
        await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => v.id)), []);
        ok(true, `${theme}/900px: matched card and compact controls pass axe`);
        await p.screenshot({ path: `${shots}/${theme}-900px-explore.png` });
        await p.setViewportSize({ width, height }); await p.waitForTimeout(350);
      }
      await p.screenshot({ path: `${shots}/${theme}-${size}-explore.png` });
      await explore.getByRole('searchbox', { name: 'Search all waters' }).fill('Fall Creek');
      await explore.getByRole('button', { name: /Fall Creek \(Willamette R\)/ }).click();
      await p.getByRole('heading', { name: 'Fall Creek (Willamette R)', exact: true }).waitFor();
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
      await p.waitForTimeout(800);
      const canvas = await p.locator('.maplibregl-canvas').boundingBox();
      await p.mouse.click(canvas.x + canvas.width / 2 + (width >= 900 ? 56 : 0), canvas.y + canvas.height / 2);
      const picker = p.getByRole('group', { name: 'Map items here', exact: true }); await picker.waitFor();
      ok(await picker.getByRole('button').count() === 2, `${theme}/${size}: nearby creek and reservoir are separate choices`);
      const creekChoice = picker.getByRole('button', { name: /Fall Creek \(Willamette R\).*creek.*Apr 19, 2027/ });
      const reservoirChoice = picker.getByRole('button', { name: /Fall Creek Reservoir.*reservoir.*Mar 15, 2027/ });
      ok(await creekChoice.count() === 1 && await reservoirChoice.count() === 1, `${theme}/${size}: each water shows its own kind and schedule week`);
      await p.evaluate(axe); assert.deepEqual(await p.evaluate(async () => (await axe.run()).violations.map((v) => v.id)), []);
      ok(true, `${theme}/${size}: nearby-water picker axe has zero violations`);
      await p.screenshot({ path: `${shots}/${theme}-${size}-nearby-waters.png` });
      await reservoirChoice.click(); await p.getByRole('heading', { name: 'Fall Creek Reservoir', exact: true }).waitFor();
      ok(true, `${theme}/${size}: reservoir choice opens the reservoir, not the creek`);
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
    }
    ok(!errors.length, `${size}: no browser errors`); await ctx.close();
  }
  console.log(`${checks} map layout checks passed`);
} finally { await b.close(); }
