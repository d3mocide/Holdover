// Throwaway-instance browser test. Setup, run and what it needs: tests/e2e/README.md.
// Env: BASE_URL (default http://localhost:8011/), CHROMIUM (path to chrome), SHOTS (optional screenshot dir).
import { chromium } from 'playwright-core'; import fs from 'fs';
const BASE = process.env.BASE_URL ?? 'http://localhost:8011/';
const axeSrc = fs.readFileSync('node_modules/axe-core/axe.min.js', 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox'] });
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const nav = (p, n) => p.getByRole('button', { name: n, exact: true }).first().click();
const login = (p, u, pw) => p.evaluate(({u, pw}) => fetch('/api/auth/login', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Holdover': '1' }, body: JSON.stringify({ username: u, password: pw }) }).then(r => { if (!r.ok) throw new Error('login ' + r.status); }), { u, pw });
const pull = (p) => p.evaluate(() => fetch('/api/sync/pull', { credentials: 'same-origin' }).then(r => r.json()));
const axe = async (p, label) => { await p.evaluate(axeSrc); const r = await p.evaluate(() => axe.run(document, { runOnly: ['wcag2a','wcag2aa','wcag21aa','best-practice'], rules: { region: { enabled: false } } })); ok(r.violations.length === 0, `axe: ${label} has no violations` + (r.violations.length ? ' -> ' + r.violations.map(v => v.id + ':' + v.nodes[0].target.join(' ')).join('; ') : '')); };

const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
const p = await ctx.newPage(); p.on('pageerror', e => console.log('pageerror', e.message));
await p.goto(BASE); await p.waitForTimeout(3000);
await login(p, 'boss', 'correct-horse-battery'); await p.reload(); await p.waitForTimeout(3500);

// ---- empty state and the starter list
await nav(p, 'Gear'); await p.waitForTimeout(700);
ok(await p.getByText('No gear yet').isVisible(), 'empty state invites the first item');
await axe(p, 'Gear (empty)');
await p.getByRole('button', { name: 'Add from the starter list' }).click(); await p.waitForTimeout(500);
ok(await p.getByRole('button', { name: /Panther Martin spinner/ }).isVisible(), 'starter list is shown');
await p.getByRole('button', { name: /Panther Martin spinner/ }).click();
ok((await p.getByLabel('Brand').inputValue()) === 'Panther Martin', 'picking a catalog item fills brand');
ok(await p.getByRole('button', { name: 'Trout', exact: true }).getAttribute('aria-pressed') === 'true', 'picking a catalog item fills fisheries');
await p.getByLabel('Size').fill('1/8 oz'); await p.getByLabel('Color').fill('gold');
await p.getByRole('button', { name: 'More' }).click(); await p.getByRole('button', { name: 'More' }).click();
await axe(p, 'Add gear form');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/gear-form.png' : undefined });
await p.getByRole('button', { name: 'Add to my gear' }).click(); await p.waitForTimeout(800);
ok(await p.getByRole('button', { name: /Panther Martin spinner/ }).filter({ hasText: '×3' }).isVisible(), 'item saved with quantity 3');

// typing searches every kind: "wool" finds the fly although the form defaulted to Lure
await p.getByRole('button', { name: 'Add gear' }).click(); await p.waitForTimeout(400);
await p.getByLabel('Name', { exact: true }).fill('wool'); await p.waitForTimeout(300);
await p.getByRole('button', { name: /Woolly Bugger/ }).click();
ok((await p.getByLabel('Type', { exact: true }).inputValue()) === 'fly', 'a typed search finds a fly and switches the type');
await p.getByRole('button', { name: 'Add to my gear' }).click(); await p.waitForTimeout(600);
// a fully custom rod, then edit it
await p.getByRole('button', { name: 'Add gear' }).click(); await p.waitForTimeout(300);
await p.getByLabel('Type', { exact: true }).selectOption('rod'); await p.getByLabel('Name', { exact: true }).fill('My 6wt'); await p.getByLabel('Size').fill('6wt 9 ft');
await p.getByRole('button', { name: 'Add to my gear' }).click(); await p.waitForTimeout(600);
await p.getByRole('button', { name: /My 6wt/ }).click(); await p.waitForTimeout(300);
await p.getByLabel('Color').fill('olive'); await p.getByRole('button', { name: 'Save changes' }).click(); await p.waitForTimeout(600);
ok(await p.getByText('6wt 9 ft · olive').isVisible(), 'editing an item updates it');
ok((await p.getByText(/^Lures & bait · 1$/).count()) + (await p.getByText(/^Flies · 1$/).count()) + (await p.getByText(/^Rods · 1$/).count()) === 3, 'items are grouped by type');
await p.getByLabel('Search gear').fill('bugger'); await p.waitForTimeout(300);
ok((await p.getByRole('button', { name: /Panther Martin/ }).count()) === 0 && await p.getByRole('button', { name: /Woolly/ }).isVisible(), 'search filters the list');
await p.getByLabel('Search gear').fill('');
await axe(p, 'Gear items');

// ---- setups
await p.getByRole('button', { name: 'Setups', exact: true }).click(); await p.waitForTimeout(300);
await p.getByRole('button', { name: 'Create a setup' }).click(); await p.waitForTimeout(400);
await p.getByLabel('Name', { exact: true }).fill('Light spinning');
await p.getByRole('checkbox', { name: /Panther Martin spinner/ }).check();
await p.getByRole('button', { name: 'Create setup' }).click(); await p.waitForTimeout(600);
ok(await p.getByText('Panther Martin spinner').isVisible() && await p.getByText('Light spinning').isVisible(), 'setup listed with its items');

// ---- log a trip with gear
await nav(p, 'Journal'); await p.waitForTimeout(400);
await p.getByRole('button', { name: /Log (a|your first) trip/ }).first().click(); await p.waitForTimeout(500);
await p.getByLabel('Where').selectOption({ label: 'Dexter Reservoir' });
await p.getByLabel('Setup').selectOption({ label: 'Light spinning' });
await p.getByRole('button', { name: 'Panther Martin spinner', exact: true }).click();
await p.getByLabel('Species 1').fill('rainbow trout'); await p.getByRole('button', { name: /More rainbow trout|More fish/ }).first().click();
await p.getByLabel('Caught on (optional)').selectOption({ label: 'Panther Martin spinner' });
await axe(p, 'Log trip with gear');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/gear-logtrip.png' : undefined });
await p.getByRole('button', { name: 'Save trip' }).click(); await p.waitForTimeout(2500);
ok(await p.getByText('Light spinning · Panther Martin spinner').isVisible(), 'journal card shows the setup and lure');
ok(await p.getByText('1 rainbow trout on Panther Martin spinner').isVisible(), 'journal card shows what the fish was caught on');

// ---- stats
await nav(p, 'Gear'); await p.getByRole('button', { name: 'What works', exact: true }).click(); await p.waitForTimeout(500);
ok(await p.getByText(/1 caught on it · 1 on trips · 1 trip/).isVisible(), 'stats: fish credited to the lure');
ok(await p.getByText(/1 fish · 1 trip · 1\/trip/).isVisible(), 'stats: the setup shows fish, trips and per-trip');
await axe(p, 'Gear stats');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/gear-stats.png' : undefined });

// ---- it all synced to the account
await p.waitForTimeout(1500);
const srv = await pull(p);
ok(srv.gear.length === 3 && srv.setups.length === 1, `server has the gear (3) and setup (1): got ${srv.gear.length}/${srv.setups.length}`);
ok(srv.trips[0].setup_uuid === srv.setups[0].uuid && srv.catches[0].gear_uuid === srv.gear.find(g => g.name === 'Panther Martin spinner').uuid, 'trip and catch carry their gear references on the server');

// ---- another account sees none of it and cannot reference it
const ctx2 = await b.newContext({ viewport: { width: 1440, height: 900 } }); const q = await ctx2.newPage();
await q.goto(BASE); await q.waitForTimeout(2500); await login(q, 'sam', 'sams-long-password'); await q.reload(); await q.waitForTimeout(3000);
await nav(q, 'Gear'); await q.waitForTimeout(600);
ok(await q.getByText('No gear yet').isVisible(), "a second account sees none of boss's gear");
const bossLure = srv.gear.find(g => g.name === 'Panther Martin spinner').uuid;
const steal = await q.evaluate((u) => fetch('/api/sync/push', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Holdover': '1' }, body: JSON.stringify({ trips: [{ uuid: '99999999-9999-4999-8999-999999999999', gear_json: JSON.stringify([u]), updated_at: new Date().toISOString() }] }) }).then(r => r.json()), bossLure);
ok(steal.applied === 0 && steal.rejected[0]?.reason === 'gear belongs to another account', 'and cannot attach a trip to boss\'s gear');
await ctx2.close();

// ---- created offline, synced after reconnect
await nav(p, 'Gear'); await p.getByRole('button', { name: 'Items', exact: true }).click();
await ctx.setOffline(true); await p.waitForTimeout(500);
await p.getByRole('button', { name: 'Add gear' }).click(); await p.waitForTimeout(300);
await p.getByLabel('Name', { exact: true }).fill('Offline spoon'); await p.getByRole('button', { name: 'Add to my gear' }).click(); await p.waitForTimeout(800);
ok(await p.getByRole('button', { name: /Offline spoon/ }).isVisible(), 'offline: gear is saved on the device immediately');
await ctx.setOffline(false); await p.waitForTimeout(5000);
const after = await pull(p);
ok(after.gear.some(g => g.name === 'Offline spoon'), 'after reconnecting the offline item synced to the account');

// ---- phone
const pc = await b.newContext({ viewport: { width: 393, height: 852 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true }); const ph = await pc.newPage();
await ph.goto(BASE); await ph.waitForTimeout(2500); await login(ph, 'boss', 'correct-horse-battery'); await ph.reload(); await ph.waitForTimeout(3500);
await nav(ph, 'Gear'); await ph.waitForTimeout(1500);
await ph.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/gear-phone.png' : undefined });
const navW = await ph.evaluate(() => [...document.querySelectorAll('.navbtn')].map(e => Math.round(e.getBoundingClientRect().width)));
ok(navW.length === 6 && navW.every(w => w >= 44), `phone nav fits six tabs with 44px+ targets (${navW.join(',')})`);
await axe(ph, 'Gear on phone');
await p.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/gear-desk.png' : undefined });
console.log(fails ? `\n${fails} FAILED` : '\nall passed'); await b.close(); process.exit(fails ? 1 : 0);
