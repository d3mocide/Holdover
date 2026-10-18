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
  const [a, b, c] = await Promise.all([db.trips.where('dirty').equals(1).count(), db.catches.where('dirty').equals(1).count(), db.pins.where('dirty').equals(1).count()]);
  syncState.pending = a + b + c;
  return syncState.pending;
}

async function uploadPhotos() {
  for (const c of await db.catches.where('dirty').equals(1).toArray()) {
    if (c.photo_blob && !c.photo_path) {
      const fd = new FormData();
      fd.append('file', c.photo_blob, 'photo');
      const r = await authed('/api/journal/photo', { method: 'POST', body: fd });
      await db.catches.update(c.uuid, { photo_path: r.photo_path, updated_at: new Date().toISOString() });
    }
  }
}

export async function push() {
  await uploadPhotos();
  const trips = await db.trips.where('dirty').equals(1).toArray();
  const catches = await db.catches.where('dirty').equals(1).toArray();
  const pins = await db.pins.where('dirty').equals(1).toArray();
  if (!trips.length && !catches.length && !pins.length) return;
  const res = await authed('/api/sync/push', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trips: trips.map(strip), catches: catches.map(strip), pins: pins.map(strip) })
  });
  const rejected = new Set(res.rejected.map((r) => r.uuid));
  // Clear dirty only if the row wasn't edited while the request was in flight.
  for (const [table, rows] of [[db.trips, trips], [db.catches, catches], [db.pins, pins]]) {
    for (const r of rows) {
      if (rejected.has(r.uuid)) continue;
      await table.where('uuid').equals(r.uuid).modify((cur) => { if (cur.updated_at === r.updated_at) cur.dirty = 0; });
    }
  }
}

export async function pull() {
  const since = await metaGet('lastPull');
  const res = await authed(`/api/sync/pull${since ? `?since=${encodeURIComponent(since)}` : ''}`);
  for (const [table, rows] of [[db.trips, res.trips], [db.catches, res.catches], [db.pins, res.pins]]) {
    for (const row of rows) {
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
