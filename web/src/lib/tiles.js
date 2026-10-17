import { PMTiles } from 'pmtiles';
import { db, metaGet, metaSet } from './db.js';

const URL_ = '/tiles/oregon.pmtiles';
const archive = new PMTiles(URL_);
// Willamette zone plus the Cascade lakes and Columbia-side waters the seed covers
export const ZONE_BBOX = [-123.9, 43.3, -121.5, 46.1];

/** MapLibre protocol: serve a tile from IndexedDB if "prepared for offline", else from the PMTiles file. */
export function registerTileProtocol(maplibregl) {
  maplibregl.addProtocol('holdover', async (params, abort) => {
    const m = /holdover:\/\/(\d+)\/(\d+)\/(\d+)/.exec(params.url);
    if (!m) throw new Error(`bad tile url ${params.url}`);
    const [z, x, y] = m.slice(1).map(Number);
    const hit = await db.tiles.get(`${z}/${x}/${y}`);
    if (hit) return { data: new Uint8Array(hit.data) };
    try {
      const r = await archive.getZxy(z, x, y, abort.signal);
      return { data: r ? new Uint8Array(r.data) : new Uint8Array() };
    } catch (e) {
      if (abort.signal.aborted) throw e;
      return { data: new Uint8Array() }; // offline and not cached: draw nothing rather than error the map
    }
  });
}

export async function basemapAvailable() {
  try {
    const ok = (await fetch(URL_, { method: 'HEAD' })).ok;
    await metaSet('hasBasemap', ok);
    return ok;
  } catch {
    return await metaGet('hasBasemap', false); // offline: trust the last answer
  }
}

const lon2x = (lon, z) => Math.floor(((lon + 180) / 360) * 2 ** z);
const lat2y = (lat, z) => Math.floor(((1 - Math.asinh(Math.tan((lat * Math.PI) / 180)) / Math.PI) / 2) * 2 ** z);

export function tileList(bbox = ZONE_BBOX, minZ = 6, maxZ = 11) {
  const out = [];
  for (let z = minZ; z <= maxZ; z++) {
    for (let x = lon2x(bbox[0], z); x <= lon2x(bbox[2], z); x++)
      for (let y = lat2y(bbox[3], z); y <= lat2y(bbox[1], z); y++) out.push([z, x, y]);
  }
  return out;
}

export async function cachedTileCount() { return db.tiles.count(); }
export async function clearTiles() { await db.tiles.clear(); }

/** Download tiles into IndexedDB. Stops cleanly on a storage-quota error and says so. */
export async function prepareTiles({ minZ = 6, maxZ = 11, onProgress, signal } = {}) {
  try { await navigator.storage?.persist?.(); } catch { /* optional */ }
  const list = tileList(ZONE_BBOX, minZ, maxZ);
  let done = 0, stored = 0;
  for (const [z, x, y] of list) {
    if (signal?.aborted) return { done, stored, total: list.length, stopped: 'cancelled' };
    const key = `${z}/${x}/${y}`;
    if (!(await db.tiles.get(key))) {
      try {
        const r = await archive.getZxy(z, x, y, signal);
        if (r) { await db.tiles.put({ key, data: r.data }); stored++; }
      } catch (e) {
        if (e?.name === 'QuotaExceededError') return { done, stored, total: list.length, stopped: 'storage full' };
        if (signal?.aborted) return { done, stored, total: list.length, stopped: 'cancelled' };
        return { done, stored, total: list.length, stopped: 'network error' };
      }
    }
    onProgress?.(++done, list.length);
  }
  return { done, stored, total: list.length, stopped: null };
}
