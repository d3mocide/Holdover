// Browser storage health. Journal, gear and offline map tiles live in IndexedDB, which the browser may clear on its own
// when space runs low unless the page has asked for (and been granted) persistent storage. Phones are the risk.

export const fmtBytes = (n) => {
  if (n == null || Number.isNaN(n)) return 'unknown';
  if (n < 1024) return `${n} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  let v = n / 1024, i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v >= 100 ? Math.round(v) : v >= 10 ? v.toFixed(0) : v.toFixed(1)} ${units[i]}`;
};

/** { supported, persisted, usage, quota } from whatever the browser offers; never throws. */
export async function storageInfo() {
  const out = { supported: typeof navigator !== 'undefined' && !!navigator.storage, persisted: false, usage: null, quota: null };
  try {
    if (navigator.storage?.persisted) out.persisted = await navigator.storage.persisted();
    if (navigator.storage?.estimate) { const e = await navigator.storage.estimate(); out.usage = e.usage ?? null; out.quota = e.quota ?? null; }
  } catch { /* leave what we have */ }
  return out;
}

/** Ask the browser to keep our data. Safe to call often: resolves true if already granted. Browsers may decline
 * silently (Safari decides on its own heuristics), so the caller should show the result, not assume it. */
export async function requestPersistence() {
  try {
    if (!navigator.storage?.persist) return false;
    if (await navigator.storage.persisted()) return true;
    return await navigator.storage.persist();
  } catch { return false; }
}

/** One-line status for the UI. */
export function storageSummary(info) {
  if (!info.supported) return { tone: 'quiet', text: 'This browser does not report storage.' };
  const used = info.usage != null && info.quota != null ? `${fmtBytes(info.usage)} of ${fmtBytes(info.quota)} used. ` : '';
  return info.persisted
    ? { tone: 'ok', text: `${used}Protected: the browser will not clear your journal and gear to free space.` }
    : { tone: 'warn', text: `${used}Not protected: if the device runs low on space the browser may clear this data. Anything not yet synced would be lost.` };
}
