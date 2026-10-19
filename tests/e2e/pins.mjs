// Placing a pin from the map as an admin. Throwaway instance: `tests/e2e/setup.sh accounts` (admin "boss"), then `node tests/e2e/pins.mjs`.
import { chromium } from 'playwright-core';
const BASE = process.env.BASE_URL ?? 'http://localhost:8011/';
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox'] });
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const nav = (p, n) => p.getByRole('button', { name: n, exact: true }).first().click();
const p = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
p.on('pageerror', e => console.log('pageerror', e.message));
await p.goto(BASE); await p.waitForTimeout(3500);
await nav(p, 'Settings'); await p.waitForTimeout(500);
ok(!(await p.getByText('Place pins').count()), 'signed out: no pin tool');
await p.getByLabel('Username').fill('boss'); await p.getByLabel('Password', { exact: true }).fill('correct-horse-battery');
await p.getByRole('button', { name: /Sign in/ }).click(); await p.waitForTimeout(2000);
ok(await p.getByText(/Place pins \(\d+\)/).isVisible(), 'admin sees the Place pins card');
const row = p.locator('.pins li', { hasText: 'East Lake' });
ok(await row.isVisible() && /no pin/.test(await row.innerText()), 'East Lake (Central) is listed with no pin');
const before = await p.evaluate(() => fetch('/api/waterbodies').then(r => r.json()).then(l => l.find(w => w.name === 'East Lake')));
ok(before && before.lat == null, 'East Lake has no coordinates yet');
await row.getByRole('button', { name: 'Place on map' }).click(); await p.waitForTimeout(1500);
ok(await p.getByText('Tap the map to place East Lake').isVisible(), 'the map asks for a tap');
ok((await p.evaluate(() => localStorage.getItem('holdover.zone'))) === 'central', 'the map switched to the Central zone');
await p.mouse.click(900, 450); await p.waitForTimeout(1500);
const after = await p.evaluate(() => fetch('/api/waterbodies').then(r => r.json()).then(l => l.find(w => w.name === 'East Lake')));
ok(after && after.lat != null && after.lat > 41.9 && after.lon < -116, `the tap was saved as a pin (${after?.lat}, ${after?.lon})`);
ok(!(await p.getByText('Tap the map to place East Lake').count()), 'the prompt is gone');
await nav(p, 'Settings'); await p.waitForTimeout(800);
ok(!(await p.locator('.pins li', { hasText: 'East Lake' }).count()), 'East Lake left the list once placed');
// cancel path
const row2 = p.locator('.pins li', { hasText: 'Baker Pond' });
await row2.getByRole('button', { name: 'Place on map' }).click(); await p.waitForTimeout(800);
await p.getByRole('button', { name: 'Cancel' }).click(); await p.waitForTimeout(400);
const unchanged = await p.evaluate(() => fetch('/api/waterbodies').then(r => r.json()).then(l => l.find(w => w.name === 'Baker Pond')));
ok(unchanged.lat == null && !(await p.getByText('Tap the map to place Baker Pond').count()), 'cancelling leaves the pin unset');
await b.close();
if (fails) { console.log(fails + ' failed'); process.exit(1); }
