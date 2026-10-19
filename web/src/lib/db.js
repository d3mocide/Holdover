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

// v2: gear and setups (the person's tackle). New tables need a version bump; added fields on existing
// tables (trip.setup_uuid, trip.gear_json, catch.gear_uuid) do not, since only indexed fields are declared.
db.version(2).stores({
  trips: 'uuid, updated_at, dirty, waterbody_id',
  catches: 'uuid, trip_uuid, dirty',
  pins: 'uuid, dirty',
  meta: 'key',
  cond: 'waterbody_id',
  tiles: 'key',
  gear: 'uuid, kind, dirty, updated_at',
  setups: 'uuid, dirty, updated_at'
});

// Keep each planned day and fishery separately; `cond` remains the latest observed conditions for logging.
db.version(3).stores({ days: '[waterbody_id+date+fishery]' });

export { uuid } from './uuid.js';
export const nowIso = () => new Date().toISOString();

export async function metaGet(key, fallback = null) {
  try { return (await db.meta.get(key))?.value ?? fallback; } catch { return fallback; }
}
export const metaSet = (key, value) => db.meta.put({ key, value });
