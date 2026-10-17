import Dexie from 'dexie';

// Local journal store. `dirty: 1` means changed since the last successful push.
export const db = new Dexie('holdover');
db.version(1).stores({
  trips: 'uuid, updated_at, dirty, waterbody_id',
  catches: 'uuid, trip_uuid, dirty',
  pins: 'uuid, dirty',
  meta: 'key',
  cond: 'waterbody_id',
  tiles: 'key'
});

export const uuid = () => crypto.randomUUID();
export const nowIso = () => new Date().toISOString();

export async function metaGet(key, fallback = null) {
  try { return (await db.meta.get(key))?.value ?? fallback; } catch { return fallback; }
}
export const metaSet = (key, value) => db.meta.put({ key, value });
