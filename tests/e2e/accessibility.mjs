// Full axe checks (including landmarks), screenshots and phone header bounds on a fixture instance.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const BASE = process.env.BASE_URL ?? 'http://localhost:8031/';
const shots = process.env.SHOTS ?? '/tmp/holdover-accessibility-shots';
await fs.mkdir(shots, { recursive: true });
const axeSrc = await fs.readFile('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const nav = (p, name) => p.getByRole('button', { name, exact: true }).first().click();
let checks = 0;
try {
  for (const [size, width, height] of [['phone', 393, 852], ['tablet', 768, 1024], ['desktop', 1440, 900]]) {
    const ctx = await b.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const p = await ctx.newPage(); const errors = [];
    p.on('pageerror', (e) => errors.push(e.message));
    await p.goto(BASE);
    for (const [theme, label] of [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']]) {
      await nav(p, 'Settings');
      await p.getByRole('radio', { name: label, exact: true }).check();
      const scan = async (view) => {
        await p.evaluate(axeSrc);
        const violations = await p.evaluate(async () => (await axe.run()).violations.map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) })));
        assert.deepEqual(violations, [], `${theme}/${size}/${view}: ${JSON.stringify(violations)}`);
        await p.screenshot({ path: `${shots}/${theme}-${size}-${view}.png` });
        console.log(`PASS axe ${theme}/${size}/${view}`); checks++;
      };
      await scan('settings');
      await nav(p, 'Map'); await p.getByRole('button', { name: 'Legend', exact: true }).waitFor(); await scan('map');
      await nav(p, 'Plan'); await p.locator('.spot').first().waitFor(); await scan('plan');
      if (width < 900) {
        const overlap = await p.evaluate(() => {
          const b = document.querySelector('.ptoggle').getBoundingClientRect(), h = document.querySelector('h1').getBoundingClientRect();
          return b.left < h.right && b.right > h.left && b.top < h.bottom && b.bottom > h.top;
        });
        assert.equal(overlap, false, `${theme}/${size}: collapse control overlaps heading`);
      }
      await p.locator('.spot', { hasText: 'Dexter Reservoir' }).click();
      await p.getByRole('button', { name: 'Plan the day', exact: true }).click();
      await p.getByRole('heading', { name: 'Dexter Reservoir', exact: true }).waitFor(); await scan('day');
      await p.getByRole('button', { name: 'Back', exact: true }).click();
      await p.getByRole('button', { name: 'Close details', exact: true }).click();
      await nav(p, 'Journal'); await scan('journal');
      await p.getByRole('button', { name: 'Log your first trip', exact: true }).click();
      await p.getByLabel('Where').waitFor(); await scan('log-trip');
      await p.getByRole('button', { name: 'Close', exact: true }).click();
    }
    assert.deepEqual(errors, [], `${size} browser errors`);
    await ctx.close();
  }
  console.log(`${checks} full axe scans passed`);
} finally { await b.close(); }
