import { PMTiles } from 'pmtiles';
import { db, metaGet, metaSet } from './db.js';

import { ZONE_BBOX, tileList, intersectBounds, ESTIMATED_TILE_BYTES } from './offlineArea.js';
export { ZONE_BBOX, tileList } from './offlineArea.js';

const URL_ = '/tiles/oregon.pmtiles';
const archive = new PMTiles(URL_);

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

/** Header coverage is read from the installed archive, with a cached copy for offline previews. */
export async function basemapInfo() {
  if (!(await basemapAvailable())) return null;
  try {
    const h = await archive.getHeader();
    const info = { bbox: [h.minLon,h.minLat,h.maxLon,h.maxLat], minZ: h.minZoom, maxZ: h.maxZoom };
    await metaSet('basemapInfo',info); return info;
  } catch { return metaGet('basemapInfo', null); }
}
export async function tilePreview(bbox, minZ, maxZ) {
  const list = tileList(bbox,minZ,maxZ), keys = new Set(await db.tiles.toCollection().primaryKeys());
  const cached = list.filter(t => keys.has(t.join('/'))).length;
  return { total:list.length, cached, remaining:list.length-cached, estimatedBytes:(list.length-cached)*ESTIMATED_TILE_BYTES };
}

export async function cachedTileCount() { return db.tiles.count(); }
export async function clearTiles() { await db.tiles.clear(); }

/** Download tiles into IndexedDB. Stops cleanly on a storage-quota error and says so. */
export async function prepareTiles({ bbox = ZONE_BBOX, minZ = 6, maxZ = 11, onProgress, signal } = {}) {
  try { await navigator.storage?.persist?.(); } catch { /* optional */ }
  const info = await basemapInfo();
  const area = info ? intersectBounds(bbox, info.bbox) : null;
  if (!area) return { done:0, stored:0, total:0, stopped:'area is outside the installed basemap' };
  const list = tileList(area, Math.max(minZ,info.minZ), Math.min(maxZ,info.maxZ));
  let done = 0, stored = 0, empty = 0;
  for (const [z, x, y] of list) {
    if (signal?.aborted) return { done, stored, total: list.length, stopped: 'cancelled' };
    const key = `${z}/${x}/${y}`;
    if (!(await db.tiles.get(key))) {
      try {
        const r = await archive.getZxy(z, x, y, signal);
        if (r) { await db.tiles.put({ key, data: r.data }); stored++; } else empty++;
      } catch (e) {
        if (e?.name === 'QuotaExceededError') return { done, stored, total: list.length, stopped: 'storage full' };
        if (signal?.aborted) return { done, stored, total: list.length, stopped: 'cancelled' };
        return { done, stored, total: list.length, stopped: 'network error' };
      }
    }
    onProgress?.(++done, list.length);
  }
  return { done, stored, empty, total: list.length, stopped: null };
}
