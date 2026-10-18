import { db, metaGet, metaSet } from './db.js';
import { auth, loadAuth } from './auth.svelte.js';

export const syncState = $state({ status: 'idle', pending: 0, lastSync: null, error: '' });

const LOCAL_ONLY = new Set(['dirty', 'photo_blob']);
const strip = (row) => Object.fromEntries(Object.entries(row).filter(([k]) => !LOCAL_ONLY.has(k)));

async function authed(path, opts = {}) {
  const r = await fetch(path, { ...opts, credentials: 'same-origin', headers: { 'X-Holdover': '1', ...(opts.headers || {}) } });
  if (r.status === 401) { const e = new Error('401'); e.signedOut = true; throw e; }
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

export async function countPending() {
  const counts = await Promise.all([db.trips, db.catches, db.pins, db.gear, db.setups].map((t) => t.where('dirty').equals(1).count()));
  syncState.pending = counts.reduce((a, b) => a + b, 0);
  return syncState.pending;
}

// Sync pushes gear and setups before trips (a trip can point at them), and every table works the same way.
const tables = () => [['gear', db.gear], ['setups', db.setups], ['trips', db.trips], ['pins', db.pins], ['catches', db.catches]];

async function uploadPhotos() {
  for (const table of [db.catches, db.gear]) {
    for (const c of await table.where('dirty').equals(1).toArray()) {
      if (c.photo_blob && !c.photo_path) {
        const fd = new FormData();
        fd.append('file', c.photo_blob, 'photo');
        const r = await authed('/api/journal/photo', { method: 'POST', body: fd });
        await table.update(c.uuid, { photo_path: r.photo_path, updated_at: new Date().toISOString() });
      }
    }
  }
}

export async function push() {
  await uploadPhotos();
  const dirty = {};
  for (const [key, table] of tables()) dirty[key] = await table.where('dirty').equals(1).toArray();
  if (!Object.values(dirty).some((rows) => rows.length)) return;
  const res = await authed('/api/sync/push', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(Object.fromEntries(Object.entries(dirty).map(([k, rows]) => [k, rows.map(strip)])))
  });
  const rejected = new Set(res.rejected.map((r) => r.uuid));
  // Clear dirty only if the row wasn't edited while the request was in flight.
  for (const [key, table] of tables()) {
    for (const r of dirty[key]) {
      if (rejected.has(r.uuid)) continue;
      await table.where('uuid').equals(r.uuid).modify((cur) => { if (cur.updated_at === r.updated_at) cur.dirty = 0; });
    }
  }
}

export async function pull() {
  const since = await metaGet('lastPull');
  const res = await authed(`/api/sync/pull${since ? `?since=${encodeURIComponent(since)}` : ''}`);
  for (const [key, table] of tables()) {
    for (const row of res[key] ?? []) {
      const local = await table.get(row.uuid);
      if (!local || (!local.dirty && local.updated_at < row.updated_at)) await table.put({ ...local, ...row, dirty: 0 });
    }
  }
  const t = new Date(new Date(res.server_time).getTime() - 2000).toISOString(); // overlap: never miss a same-ms write
  await metaSet('lastPull', t);
}

let timer = null, failures = 0, running = false;

export async function syncNow() {
  if (running) return;
  if (!auth.user) { syncState.status = 'signed-out'; await countPending(); return; }
  if (!navigator.onLine) { syncState.status = 'offline'; await countPending(); return; }
  running = true; syncState.status = 'syncing';
  try {
    await push(); await pull();
    failures = 0; syncState.error = ''; syncState.status = 'idle'; syncState.lastSync = new Date().toISOString();
  } catch (e) {
    if (e.signedOut) { auth.user = null; auth.notice = 'You were signed out. Your journal is still on this device.'; syncState.status = 'signed-out'; return; }
    failures++; syncState.status = 'error'; syncState.error = e.message;
    clearTimeout(timer);
    timer = setTimeout(syncNow, Math.min(5000 * 2 ** (failures - 1), 300000)); // 5 s .. 5 min backoff
  } finally { running = false; await countPending(); }
}

export function startSync() {
  // Back online: first confirm who we are (an offline start only assumed it), then sync.
  addEventListener('online', () => loadAuth().then(syncNow));
  addEventListener('offline', () => { syncState.status = 'offline'; });
  setInterval(syncNow, 60000);
  syncNow();
}
