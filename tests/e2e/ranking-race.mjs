// Disposable fixture only. Deliberately deliver obsolete fishery rankings last.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
try {
  for (const view of ['Map', 'Plan']) {
    const ctx = await browser.newContext({ serviceWorkers: 'block' }), p = await ctx.newPage();
    let release, held = 0, completed = 0;
    const gate = new Promise(resolve => { release = resolve; });
    const base = process.env.BASE_URL ?? 'http://localhost:8058';
    await ctx.route('**/api/spots?**', async route => {
      const url = new URL(route.request().url()), old = url.searchParams.get('fishery') === 'trout';
      if (old) { held++; await gate; }
      const name = old ? 'Synthetic obsolete trout ranking' : 'Synthetic selected steelhead ranking';
      await route.fulfill({ json: { date: url.searchParams.get('date'), fishery: url.searchParams.get('fishery'), spots: [{
        rank: 1, waterbody: { id: old ? 900001 : 900002, name, kind: 'lake' }, score: 50, coverage: 0,
        factors: [], explanation: { source: 'template', text: 'Synthetic request-order fixture.' },
      }] } });
      if (old) completed++;
    });
    await p.goto(base);
    if (view === 'Plan') await p.getByRole('button', { name: view, exact: true }).first().click();
    const root = view === 'Map' ? p.getByRole('region', { name: 'Explore waters', exact: true }) : p.locator('.daybody');
    await p.getByRole('button', { name: 'Steelhead & salmon', exact: true }).click();
    await root.getByText('Synthetic selected steelhead ranking', { exact: true }).waitFor();
    assert.ok(held >= (view === 'Plan' ? 8 : 1), 'previous fishery requests are held');
    release();
    while (completed < held) await new Promise(resolve => setTimeout(resolve, 10));
    // Let fetch parsing and Svelte updates consume every obsolete response.
    await p.waitForTimeout(500);
    assert.equal(await root.getByText('Synthetic obsolete trout ranking', { exact: true }).count(), 0);
    assert.equal(await root.getByText('Synthetic selected steelhead ranking', { exact: true }).count(), 1);
    console.log(`PASS ${view}: late previous-fishery responses cannot replace the selected ranking`);
    await ctx.unrouteAll({ behavior: 'wait' }); await ctx.close();
  }
} finally { await browser.close(); }
