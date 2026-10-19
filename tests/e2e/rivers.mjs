// River discovery on a disposable fixture instance. Populated chart data, if present, is explicitly test data.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const BASE = process.env.BASE_URL ?? 'http://localhost:8041';
const shots = process.env.SHOTS ?? '/tmp/holdover-river-shots';
await fs.mkdir(shots, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0; const errors = [];
const ok = (value, label) => { assert.ok(value, label); console.log('PASS ' + label); checks++; };
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const p = await ctx.newPage(); p.on('pageerror', (e) => errors.push(e.message));
  await p.goto(BASE); await p.evaluate(async () => { await navigator.serviceWorker.ready; }); await p.reload();
  const explore = p.getByRole('region', { name: 'Explore waters', exact: true });
  await explore.getByRole('button', { name: 'Rivers', exact: true }).click();
  await explore.getByRole('button', { name: /Tualatin River/ }).click();
  await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  ok(true, 'river opens directly from river browsing without a gauge popup');
  await p.getByRole('heading', { name: 'River history', exact: true }).waitFor();
  await p.locator('.history svg[role="img"]').waitFor();
  ok(await p.locator('.history polyline').count() > 0, 'stored observations render a real chart');
  await p.getByRole('button', { name: '24 hours', exact: true }).click();
  await p.locator('.history svg[role="img"]').waitFor();
  await p.getByLabel('Measurement', { exact: true }).selectOption('water_temp_c');
  await p.locator('.history svg[role="img"]').waitFor();
  ok(/Water temperature/.test(await p.locator('.history svg').getAttribute('aria-label')), 'temperature chart switches measurement');
  ok(await p.getByText(/not a seasonal normal/).isVisible(), 'recent baseline is not presented as seasonal normal');
  await p.getByRole('button', { name: 'Add Tualatin River to favorites', exact: true }).click();
  await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await explore.getByRole('button', { name: 'Favorites', exact: true }).click();
  ok(await explore.getByRole('button', { name: /Tualatin River/ }).isVisible(), 'favorite river is surfaced without a ranking');

  await explore.getByRole('searchbox', { name: 'Search all waters' }).fill('Deschutes River');
  await explore.getByRole('button', { name: /Deschutes River/ }).click();
  await p.getByRole('heading', { name: 'Deschutes River', exact: true }).waitFor();
  ok(await p.evaluate(() => localStorage.getItem('holdover.zone')) === 'central', 'cross-zone search opens the river and changes zone');
  await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await explore.getByRole('searchbox', { name: 'Search all waters' }).fill('East Lake');
  ok(await explore.getByRole('button', { name: /East Lake.*No map pin/ }).isVisible(), 'search includes waters without pins');
  await explore.getByRole('button', { name: /East Lake.*No map pin/ }).click();
  await p.getByRole('heading', { name: 'East Lake', exact: true }).waitFor();
  ok(true, 'unpinned water details remain usable');
  await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await explore.getByRole('searchbox', { name: 'Search all waters' }).fill('Tualatin');
  await explore.getByRole('button', { name: /Tualatin River/ }).click();
  await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  await p.locator('.history svg[role="img"]').waitFor();
  await p.screenshot({ path: `${shots}/river-desktop.png` });
  await p.getByRole('button', { name: 'Close details', exact: true }).click();
  await explore.getByRole('button', { name: 'Explore waters', exact: true }).click();
  // The previous selection centers the river at MapLibre's padded center (112 px left inset).
  await p.waitForTimeout(700);
  const canvas = await p.locator('.maplibregl-canvas').boundingBox();
  await p.mouse.click(canvas.x + canvas.width / 2 + 56, canvas.y + canvas.height / 2);
  const picker = p.getByRole('group', { name: 'Map items here', exact: true });
  if (await picker.isVisible()) await picker.getByRole('button', { name: /Tualatin River.*River · open details/ }).click();
  await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  ok(await p.getByRole('button', { name: 'Open waterbody', exact: true }).count() === 0, 'river marker or overlap choice opens details without a gauge-popup detour');

  await ctx.setOffline(true); await p.reload();
  await p.getByRole('button', { name: 'Rivers', exact: true }).click();
  await p.getByRole('button', { name: /Tualatin River.*river/ }).click();
  await p.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  await p.locator('.history svg[role="img"]').waitFor();
  ok(true, 'river list, details and loaded history survive offline reload');

  const phone = await browser.newContext({ viewport: { width: 393, height: 852 } });
  const m = await phone.newPage(); m.on('pageerror', (e) => errors.push(e.message));
  await m.goto(BASE);
  await m.getByRole('button', { name: 'Rivers', exact: true }).click();
  await m.getByRole('button', { name: /Tualatin River.*river/ }).click();
  await m.getByRole('heading', { name: 'Tualatin River', exact: true }).waitFor();
  ok(await m.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'phone river details fit without horizontal overflow');
  await m.screenshot({ path: `${shots}/river-phone.png` });
  ok(errors.length === 0, 'river browsing has no browser errors');
  console.log(`${checks} river checks passed`);
} finally { await browser.close(); }
