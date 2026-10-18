// Optional accounts. Signed out is a first-class state: everything public works, and the journal, home and
// favorites live on this device. Signing in moves them to the account and syncs across devices.
import { api, setUnauthorizedHandler } from './api.js';
import { db, metaGet, metaSet } from './db.js';

export const auth = $state({ ready: false, user: null, serverHome: null, notice: '', assumed: false });
// What the UI shows for home/favorites: the account's when signed in, this device's otherwise.
export const prefs = $state({ favorites: [], home: null });

const USER_KEY = 'holdover.user'; // last known profile, so an offline start still knows who is signed in
const FAV_KEY = 'holdover.favorites';
const HOME_KEY = 'holdover.home';
const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const write = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage blocked */ } };

function applyPrefs() {
  if (auth.user) { prefs.favorites = auth.user.favorites; prefs.home = auth.user.home; }
  else { prefs.favorites = read(FAV_KEY, []); prefs.home = read(HOME_KEY, null); }
}

async function freshApiCache() {
  // Cached API reads (spots, map) can differ per user (distance, favorites): never show one person's to the next.
  try { await caches.delete('api-reads'); } catch { /* no Cache API */ }
}

setUnauthorizedHandler(() => {
  if (auth.user) { auth.user = null; write(USER_KEY, null); auth.notice = 'You were signed out. Your journal is still on this device.'; applyPrefs(); }
});

/** Ask the server who is signed in. With no connection we cannot ask, so we trust the last known answer: the
 * session cookie is still sent when we reconnect, and loadAuth runs again then to confirm (or sign us out). */
export async function loadAuth() {
  try {
    const r = await api.me();
    auth.user = r.user; auth.serverHome = r.server_home; auth.assumed = false;
    write(USER_KEY, r.user);
  } catch (e) {
    if (e.status) { auth.user = null; write(USER_KEY, null); }  // the server answered, and the answer was no
    else { auth.user = read(USER_KEY, null); auth.assumed = !!auth.user; } // no network: assume the last known user
  }
  auth.ready = true;
  applyPrefs();
}

async function localJournalCounts() {
  const tables = [db.trips, db.catches, db.pins, db.gear, db.setups];
  const dirty = (await Promise.all(tables.map((t) => t.where('dirty').equals(1).count()))).reduce((a, b) => a + b, 0);
  return { dirty, total: await db.trips.count() };
}

export async function clearDeviceJournal() {
  await Promise.all([db.trips.clear(), db.catches.clear(), db.pins.clear(), db.gear.clear(), db.setups.clear(), db.meta.delete('lastPull'), db.meta.delete('syncOwner')]);
}

async function onSignedIn(user) {
  // The journal on a device belongs to whoever last signed in here (or to nobody, if it was only ever used signed
  // out). Never let one person's unsynced trips flow into another person's account.
  const owner = await metaGet('syncOwner', null);
  if (owner !== null && owner !== user.id) {
    const { dirty } = await localJournalCounts();
    if (dirty > 0 && !confirm(`This device has ${dirty} unsynced journal entr${dirty === 1 ? 'y' : 'ies'} from a different account. Signing in as ${user.username} will discard them. Continue?`)) {
      await api.logout().catch(() => {});
      throw new Error('Sign-in cancelled: nothing was changed.');
    }
    await clearDeviceJournal();
  }
  await metaSet('syncOwner', user.id);
  // Hand over what this device had saved while signed out; the account wins if both have a home.
  let merged = user;
  try { merged = await api.mergeLocal(read(FAV_KEY, []), read(HOME_KEY, null)); write(FAV_KEY, null); write(HOME_KEY, null); } catch { /* keep going: prefs stay local */ }
  auth.user = merged; auth.notice = ''; auth.assumed = false; write(USER_KEY, merged);
  applyPrefs();
  await freshApiCache();
  const { syncNow } = await import('./sync.svelte.js');
  syncNow();
}

export async function signIn(username, password) {
  const r = await api.login(username, password);
  await onSignedIn(r.user);
}

export async function register(invite, username, password) {
  const r = await api.register(invite, username, password);
  await onSignedIn(r.user);
}

/** clearDevice: also remove the journal copy from this browser (for shared devices). It stays on the server. */
export async function signOut({ clearDevice = false } = {}) {
  if (clearDevice) {
    const { dirty } = await localJournalCounts();
    if (dirty > 0 && !confirm(`${dirty} journal entr${dirty === 1 ? 'y has' : 'ies have'} not synced yet and would be lost. Remove them from this device anyway?`)) return false;
  }
  await api.logout().catch(() => {});
  auth.user = null; auth.notice = ''; auth.assumed = false; write(USER_KEY, null);
  if (clearDevice) await clearDeviceJournal();
  applyPrefs();
  await freshApiCache();
  return true;
}

export const isFavorite = (id) => prefs.favorites.includes(id);

const OFFLINE_MSG = 'You are offline, so this could not be saved to your account. Try again when you have signal.';
async function account(fn) {
  try { return await fn(); } catch (e) { throw e.status ? e : new Error(OFFLINE_MSG); }
}

export async function toggleFavorite(id) {
  const on = isFavorite(id);
  if (auth.user) {
    const u = await account(() => (on ? api.removeFavorite(id) : api.addFavorite(id)));
    auth.user = u; write(USER_KEY, u);
  } else {
    write(FAV_KEY, on ? prefs.favorites.filter((x) => x !== id) : [...prefs.favorites, id]);
  }
  applyPrefs();
}

export async function setHome(home) {
  if (auth.user) { auth.user = await account(() => api.setHome(home?.lat ?? null, home?.lon ?? null)); write(USER_KEY, auth.user); }
  else write(HOME_KEY, home ? { lat: home.lat, lon: home.lon } : null);
  applyPrefs();
}

/** The home the planner should use right now. Signed in, the server already knows it; signed out, send ours. */
export const homeForRequests = () => (auth.user ? null : prefs.home);
