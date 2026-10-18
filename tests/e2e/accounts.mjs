// Throwaway-instance browser test. Setup, run and what it needs: tests/e2e/README.md.
// Env: BASE_URL (default http://localhost:8011/), CHROMIUM (path to chrome), SHOTS (optional screenshot dir).
import { chromium } from 'playwright-core';
const BASE = process.env.BASE_URL ?? 'http://localhost:8011/';
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args:['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox'] });
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
const mk = async (name, vp = { width: 1440, height: 900 }) => { const ctx = await b.newContext({ viewport: vp }); const p = await ctx.newPage(); p.on('pageerror', e => console.log(name, 'pageerror', e.message)); return { ctx, p }; };
const nav = (p, n) => p.getByRole('button', { name: n, exact: true }).first().click();

// ---- A: admin
const A = await mk('A'); const a = A.p;
await a.goto(BASE); await a.waitForTimeout(3500);
await nav(a, 'Settings'); await a.waitForTimeout(800);
ok(await a.getByText('Signing in is optional').isVisible(), 'signed out: Account explains that signing in is optional');
ok(!(await a.getByText('People').count()), 'signed out: no admin sections');
await a.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/acct-signedout.png' : undefined });
await a.getByLabel('Username').fill('boss'); await a.getByLabel('Password', { exact: true }).fill('wrong-password-1');
await a.getByRole('button', { name: /Sign in/ }).click(); await a.waitForTimeout(800);
ok(await a.getByRole('alert').filter({ hasText: /invalid username or password/ }).isVisible(), 'wrong password shows the generic error');
await a.getByLabel('Password', { exact: true }).fill('correct-horse-battery');
await a.getByRole('button', { name: /Sign in/ }).click(); await a.waitForTimeout(1500);
ok(await a.getByText('Your journal, home and favorites sync to this account.').isVisible(), 'signed in as admin');
ok(await a.getByText('People').isVisible() && await a.getByText('Invites').isVisible(), 'admin sees People and Invites');
const cookies = await A.ctx.cookies();
const sess = cookies.find(c => c.name === 'holdover_session');
ok(!!sess && sess.httpOnly && sess.sameSite === 'Lax', 'session cookie is HttpOnly + SameSite=Lax');
ok(!(await a.evaluate(() => document.cookie.includes('holdover_session'))), 'script cannot read the session cookie');
ok(!(await a.evaluate(() => JSON.stringify(localStorage)).then(s => /token/i.test(s))), 'no token in localStorage');
// invite
await a.getByRole('button', { name: 'Create invite link' }).click(); await a.waitForTimeout(800);
const link = await a.getByLabel('Invite link').inputValue();
ok(/\/\?invite=[\w-]{20,}$/.test(link), 'invite link created: ' + link.replace(/invite=.+/, 'invite=…'));
await a.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/acct-admin.png' : undefined });
// favorite via star, then see it in Settings
await nav(a, 'Map'); await a.waitForTimeout(800);
await a.getByRole('button', { name: /Dexter Reservoir/ }).first().click(); await a.waitForTimeout(1500);
await a.getByRole('button', { name: /Add Dexter Reservoir to favorites/ }).click(); await a.waitForTimeout(800);
ok(await a.getByRole('button', { name: /Remove Dexter Reservoir from favorites/ }).isVisible(), 'star toggles to favorite');
await a.getByRole('button', { name: 'Close details' }).click();
await nav(a, 'Settings'); await a.waitForTimeout(800);
ok(await a.getByRole('button', { name: /Remove Dexter Reservoir from favorites/ }).isVisible(), 'favorite listed in Settings');
// home via map
await a.getByRole('button', { name: /Set on map/ }).click(); await a.waitForTimeout(400);
ok(await a.getByText('Tap the map to set your home').isVisible(), 'pick-home banner shows');
await a.mouse.click(900, 450); await a.waitForTimeout(1200);
const homeTxt = await a.locator('.line .mono').first().innerText();
ok(/^4\d\.\d{4}, -12\d\.\d{4}$/.test(homeTxt), 'home saved from map tap: ' + homeTxt);
// log a trip (signed in)
await a.getByRole('button', { name: 'Journal', exact: true }).first().click(); await a.waitForTimeout(600);
await a.getByRole('button', { name: /Log (a|your first) trip/ }).first().click();
await a.getByLabel('Where').selectOption({ label: 'Dexter Reservoir' });
await a.getByLabel('Species 1').fill('rainbow trout'); await a.getByRole('button', { name: /More/ }).first().click();
await a.getByRole('button', { name: 'Save trip' }).click(); await a.waitForTimeout(2500);
const adminTrips = await a.evaluate(() => fetch('/api/sync/pull', { credentials: 'same-origin' }).then(r => r.json()).then(j => j.trips.length));
ok(adminTrips === 1, 'admin trip synced to the account (server has 1)');

// ---- B: invited user, a fresh browser
const B = await mk('B'); const bp = B.p;
await bp.goto(link); await bp.waitForTimeout(3500);
ok(await bp.getByText('You were invited to Holdover').isVisible(), 'invite link opens the registration form');
ok(!(await bp.evaluate(() => location.search)), 'invite code removed from the address bar');
await bp.getByLabel('Username').fill('sam'); await bp.getByLabel('Password (10+ characters)').fill('sams-long-password'); await bp.getByLabel('Repeat password').fill('sams-long-password');
await bp.getByRole('button', { name: 'Create account' }).click(); await bp.waitForTimeout(1800);
ok(await bp.getByText('Your journal, home and favorites sync to this account.').isVisible(), 'sam registered and signed in');
ok(!(await bp.getByText('People').count()), 'sam is not an admin: no admin sections');
await nav(bp, 'Journal'); await bp.waitForTimeout(800);
ok(await bp.getByText('No trips yet').isVisible(), "sam does not see boss's trip");
await nav(bp, 'Settings'); await bp.waitForTimeout(500);
ok(await bp.getByText('None yet. Use the star on a waterbody to add it.').isVisible(), "sam does not inherit boss's favorites");
const reuse = await bp.evaluate((l) => fetch('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Holdover': '1' }, body: JSON.stringify({ invite: new URL(l).searchParams.get('invite'), username: 'eve', password: 'eves-long-password' }) }).then(r => r.status), link);
ok(reuse === 400, 'invite cannot be used twice');
const adminFromSam = await bp.evaluate(() => fetch('/api/admin/users', { credentials: 'same-origin' }).then(r => r.status));
ok(adminFromSam === 403, 'sam is refused the admin API (403)');
await bp.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/acct-sam.png' : undefined });

// ---- C: anonymous device keeps prefs locally, merges on sign-in
const C = await mk('C'); const c = C.p;
await c.goto(BASE); await c.waitForTimeout(3500);
await c.locator('.spot').nth(1).click(); await c.waitForTimeout(1500);   // second ranked spot: not boss's Dexter
await c.getByRole('button', { name: /^Add .* to favorites$/ }).click(); await c.waitForTimeout(500);
ok((await c.evaluate(() => localStorage.getItem('holdover.favorites'))) !== null, 'signed out: favorite kept on this device');
const anonSpots = await c.evaluate(() => fetch('/api/sync/pull', { credentials: 'same-origin' }).then(r => r.status));
ok(anonSpots === 401, 'signed out: journal API refuses (401), journal stays local');
await nav(c, 'Settings'); await c.waitForTimeout(500);
await c.getByLabel('Username').fill('boss'); await c.getByLabel('Password', { exact: true }).fill('correct-horse-battery');
await c.getByRole('button', { name: /Sign in/ }).click(); await c.waitForTimeout(2000);
const favs = await c.evaluate(() => fetch('/api/auth/me', { credentials: 'same-origin' }).then(r => r.json()).then(j => j.user.favorites.length));
ok(favs === 2, "sign-in merged this device's favorite into the account (boss now has 2)");
ok((await c.evaluate(() => localStorage.getItem('holdover.favorites'))) === null, 'local favorites cleared after the merge');
await c.getByRole('button', { name: 'Sign out', exact: true }).click(); await c.waitForTimeout(1000);
ok(await c.getByText('Signing in is optional').isVisible(), 'signed out again');
const after = await c.evaluate(() => fetch('/api/sync/pull', { credentials: 'same-origin' }).then(r => r.status));
ok(after === 401, 'after sign-out the server no longer answers journal calls');


// ---- D: one browser shared by two people: no leakage of unsynced trips
const D = await mk('D'); const d = D.p;
const logTrip = async (pg) => {
  await nav(pg, 'Journal'); await pg.waitForTimeout(500);
  await pg.getByRole('button', { name: /Log (a|your first) trip/ }).first().click();
  await pg.getByLabel('Where').selectOption({ label: 'Dexter Reservoir' });
  await pg.getByLabel('Species 1').fill('brown trout'); await pg.getByRole('button', { name: /More/ }).first().click();
  await pg.getByRole('button', { name: 'Save trip' }).click(); await pg.waitForTimeout(1500);
};
const signInAs = async (pg, u, pw) => {
  await nav(pg, 'Settings'); await pg.waitForTimeout(500);
  await pg.getByLabel('Username').fill(u); await pg.getByLabel('Password', { exact: true }).fill(pw);
  await pg.getByRole('button', { name: /^Sign in$/ }).click(); await pg.waitForTimeout(2000);
};
const serverTrips = (pg) => pg.evaluate(() => fetch('/api/sync/pull', { credentials: 'same-origin' }).then(r => r.status === 200 ? r.json().then(j => j.trips.length) : r.status));
await d.goto(BASE); await d.waitForTimeout(3500);
await logTrip(d);                                              // logged while signed out: local only
ok(await d.locator('li.card').filter({ hasText: 'Waiting to sync' }).first().isVisible(), 'signed out: trip saved on this device, waiting to sync');
await signInAs(d, 'boss', 'correct-horse-battery');
await d.waitForTimeout(1500);
ok((await serverTrips(d)) === 2, "signing in adopted the device's local trip into boss's account (server now has 2)");
await nav(d, 'Settings'); await d.getByRole('button', { name: 'Sign out', exact: true }).click(); await d.waitForTimeout(800);
await signInAs(d, 'sam', 'sams-long-password');
await nav(d, 'Journal'); await d.waitForTimeout(800);
ok(await d.getByText('No trips yet').isVisible(), "switching to sam on the same browser: boss's trips are gone from the device");
ok((await serverTrips(d)) === 0, "...and nothing of boss's was pushed into sam's account");
// sam logs a trip that cannot sync (push blocked), signs out, then boss tries to sign in on this browser
await d.route('**/api/sync/push', (r) => r.abort());
await logTrip(d);
ok(await d.locator('li.card').filter({ hasText: 'Waiting to sync' }).first().isVisible(), "sam's trip is waiting to sync");
await nav(d, 'Settings'); await d.getByRole('button', { name: 'Sign out', exact: true }).click(); await d.waitForTimeout(800);
let dialogMsg = '';
d.once('dialog', async (dlg) => { dialogMsg = dlg.message(); await dlg.dismiss(); });
await signInAs(d, 'boss', 'correct-horse-battery');
ok(/unsynced journal entr.*different account/.test(dialogMsg), 'warned that boss signing in would discard sam\'s unsynced trip');
ok(await d.getByText('Signing in is optional').isVisible(), 'declined: boss was NOT signed in (sam\'s trip stays on the device)');
await d.unroute('**/api/sync/push');
d.once('dialog', (dlg) => dlg.accept());
await signInAs(d, 'boss', 'correct-horse-battery');
await nav(d, 'Journal'); await d.waitForTimeout(800);
ok(!(await d.locator('li.card').filter({ hasText: 'Waiting to sync' }).count()), "accepted: sam's unsynced trip was discarded, not pushed to boss");
await d.waitForTimeout(1500);
ok((await serverTrips(d)) === 2, 'boss still has exactly his 2 trips on the server');

// ---- phone layout of Settings (signed in as admin)
const P = await mk('P', { width: 393, height: 852 }); const pp = P.p;
await pp.goto(BASE); await pp.waitForTimeout(3000); await nav(pp, 'Settings'); await pp.waitForTimeout(600);
await pp.getByLabel('Username').fill('boss'); await pp.getByLabel('Password', { exact: true }).fill('correct-horse-battery');
await pp.getByRole('button', { name: /Sign in/ }).click(); await pp.waitForTimeout(1500);
await pp.screenshot({ path: process.env.SHOTS ? process.env.SHOTS + '/acct-phone.png' : undefined });
console.log(fails ? `\n${fails} FAILED` : '\nall passed'); await b.close(); process.exit(fails ? 1 : 0);
