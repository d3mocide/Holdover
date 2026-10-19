// Fresh fixture instance: setup.sh gear. No production or personal dev data is used.
import { chromium } from 'playwright-core';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const BASE = process.env.BASE_URL ?? 'http://localhost:8031/';
const shots = process.env.SHOTS ?? '/tmp/holdover-hardening-shots';
await fs.mkdir(shots, { recursive: true });
const b = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
let checks = 0;
const pageErrors = [];
const ok = (value, label) => { assert.ok(value, label); console.log('PASS ' + label); checks++; };
const nav = (p, name) => p.getByRole('button', { name, exact: true }).first().click();
const open = async () => {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, timezoneId: 'America/Los_Angeles', serviceWorkers: 'block' });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => { pageErrors.push(e.message); console.error('PAGE ERROR', e.name, e.message); });
  await p.goto(BASE);
  await nav(p, 'Journal');
  await p.getByText('No trips yet').waitFor();
  return { p, ctx };
};
const login = async (p, user, password) => {
  await nav(p, 'Settings');
  await p.getByLabel('Username').fill(user);
  await p.getByLabel('Password', { exact: true }).fill(password);
  await p.getByRole('button', { name: 'Sign in', exact: true }).click();
  await p.getByText('Your journal, home and favorites sync to this account.').waitFor();
};
const meta = (p, key) => p.evaluate((key) => new Promise((resolve, reject) => {
  const r = indexedDB.open('holdover'); r.onerror = () => reject(r.error);
  r.onsuccess = () => { const db = r.result, q = db.transaction('meta').objectStore('meta').get(key); q.onsuccess = () => { resolve(q.result?.value); db.close(); }; };
}), key);
const downloadText = async (p, format) => {
  const download = p.waitForEvent('download');
  await p.getByRole('button', { name: `Export ${format.toUpperCase()}` }).click();
  const d = await download;
  return fs.readFile(await d.path(), 'utf8');
};

try {
  // Anonymous, offline export includes the entries that have never reached a server.
  const { p, ctx } = await open();
  await p.getByRole('button', { name: 'Log your first trip' }).click();
  await p.getByLabel('Where').selectOption({ label: 'Dexter Reservoir' });
  await p.getByLabel('Notes').fill('Private unsynced note');
  await p.getByLabel('Species 1').fill('rainbow trout');
  await p.getByRole('button', { name: 'More rainbow trout' }).click();
  await ctx.setOffline(true);
  await p.getByRole('button', { name: 'Save trip', exact: true }).click();
  await p.locator('li.card').getByText('Private unsynced note').waitFor();
  const json = JSON.parse(await downloadText(p, 'json'));
  ok(json.trips.length === 1 && json.trips[0].notes === 'Private unsynced note', 'anonymous offline JSON exports unsynced trip');
  ok(json.catches[0].count === 1, 'offline JSON includes catch');
  ok((await downloadText(p, 'csv')).includes('Private unsynced note'), 'anonymous CSV downloads offline');
  await ctx.setOffline(false);
  await login(p, 'boss', 'correct-horse-battery');
  await nav(p, 'Journal');
  await p.locator('li.card', { hasText: 'Private unsynced note' }).first().getByText(/^\s*Synced/).waitFor();

  // Draft alone must trigger the shared-device warning; cancelling must preserve it.
  await p.getByRole('button', { name: 'Log a trip', exact: true }).click();
  await p.getByLabel('Notes').fill('Draft for boss only');
  await p.waitForFunction(() => new Promise((resolve) => {
    const r = indexedDB.open('holdover'); r.onsuccess = () => {
      const db = r.result, q = db.transaction('meta').objectStore('meta').get('tripDraft');
      q.onsuccess = () => { resolve(q.result?.value?.value?.notes === 'Draft for boss only'); db.close(); };
    };
  }));
  await p.getByRole('button', { name: 'Close', exact: true }).click();
  await nav(p, 'Settings');
  await p.getByText('On a shared device?', { exact: true }).click();
  const rejected = p.waitForEvent('dialog').then(async (d) => { ok(/not synced/.test(d.message()), 'unsaved draft warns before clearing device'); await d.dismiss(); });
  await p.getByRole('button', { name: 'Sign out and clear this device', exact: true }).click(); await rejected;
  ok((await meta(p, 'tripDraft')).value.notes === 'Draft for boss only', 'cancel preserves private draft');
  const accepted = p.waitForEvent('dialog').then((d) => d.accept());
  await p.getByRole('button', { name: 'Sign out and clear this device', exact: true }).click(); await accepted;
  await p.getByLabel('Username').waitFor();
  ok(await meta(p, 'tripDraft') === undefined, 'clear-device signout removes the draft');
  await login(p, 'sam', 'sams-long-password');
  await nav(p, 'Journal');
  await p.getByRole('button', { name: 'Log your first trip' }).click();
  ok(await p.getByLabel('Notes').inputValue() === '', 'next account cannot restore previous draft');
  await p.getByLabel('Notes').fill('Sam unfinished trip');
  await p.getByRole('button', { name: 'Close', exact: true }).click();
  await nav(p, 'Settings');
  await p.getByRole('button', { name: 'Sign out', exact: true }).click();
  const switchDialog = p.waitForEvent('dialog').then(async (d) => { ok(/unsynced/.test(d.message()), 'account switching counts a draft as unsynced work'); await d.accept(); });
  await login(p, 'boss', 'correct-horse-battery'); await switchDialog;
  ok(await meta(p, 'tripDraft') === undefined, 'account switch clears previous owner draft');

  // A second device already synced before the offline write was uploaded.
  const second = await open();
  await login(second.p, 'boss', 'correct-horse-battery');
  await nav(second.p, 'Journal');
  await second.p.getByRole('status').filter({ hasText: /^Synced/ }).waitFor();
  const lateId = 'ab'.repeat(16);
  const pushed = await p.evaluate(async (uuid) => {
    const r = await fetch('/api/sync/push', { method: 'POST', headers: { 'X-Holdover': '1', 'Content-Type': 'application/json' },
      body: JSON.stringify({ trips: [{ uuid, notes: 'Late offline arrival', updated_at: '2020-01-01T00:00:00Z' }] }) });
    return r.json();
  }, lateId);
  ok(pushed.applied === 1, 'late offline write accepted');
  await second.p.evaluate(() => dispatchEvent(new Event('online')));
  await nav(second.p, 'Journal');
  await second.p.getByText('Late offline arrival', { exact: true }).waitFor();
  ok(true, 'normal sync on second device receives late offline write');

  // Exact day cache: tomorrow must not replace today's bundle or silently fill an uncached day.
  const dayPage = await open();
  const dp = dayPage.p;
  await dp.route('**/api/day/*', async (route) => {
    const url = new URL(route.request().url()); url.searchParams.set('refresh', 'false');
    const response = await route.fetch({ url: url.href }); const data = await response.json();
    data.pack.intro = `Test fixture: ${url.searchParams.get('date')} ${url.searchParams.get('fishery')}`;
    await route.fulfill({ json: data });
  });
  await nav(dp, 'Plan');
  await dp.locator('.spot', { hasText: 'Dexter Reservoir' }).click();
  await dp.getByRole('button', { name: 'Plan the day', exact: true }).click();
  await dp.getByText(/^Test fixture:/).waitFor();
  const today = await dp.getByText(/^Test fixture:/).innerText();
  await dp.getByRole('button', { name: 'Tomorrow', exact: true }).click();
  await dp.getByText(/^Test fixture:/).filter({ hasNotText: today }).waitFor();
  await dp.unroute('**/api/day/*');
  await dayPage.ctx.setOffline(true);
  await dp.getByRole('button', { name: 'Today', exact: true }).click();
  await dp.getByText(today, { exact: true }).waitFor();
  ok(true, 'today remains correct after caching tomorrow and disconnecting');
  await dp.getByRole('button', { name: 'In 2 days', exact: true }).click();
  await dp.getByRole('alert').filter({ hasText: 'No saved day view for this date and fishery' }).waitFor();
  ok(!(await dp.getByText(/^Test fixture:/).count()), 'uncached day shows missing-cache message instead of another date');

  ok(pageErrors.length === 0, 'no unhandled browser errors');
  console.log(`${checks} hardening checks passed`);
} finally { await b.close(); }
