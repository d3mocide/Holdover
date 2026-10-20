import { liveQuery } from 'dexie';
import { db } from './db.js';
import { auth } from './auth.svelte.js';

export const adviceState = $state({ enabled: false, now: Date.now(), data: null, error: '' });
const empty = () => ({ trips: [], catches: [], gear: [], setups: [] });

export function adviceData() {
  const d = adviceState.data;
  // Hide a previous owner's in-memory snapshot immediately while device clearing/pulling completes.
  return d && (!auth.user || d.owner === auth.user.id) ? d : empty();
}

export function startAdvice() {
  const sub = liveQuery(() => db.transaction('r', db.trips, db.catches, db.gear, db.setups, db.meta, async () => ({
    trips: await db.trips.toArray(), catches: await db.catches.toArray(), gear: await db.gear.toArray(),
    setups: await db.setups.toArray(), owner: (await db.meta.get('syncOwner'))?.value ?? null
  }))).subscribe({ next: data => { adviceState.data = data; adviceState.error = ''; },
    error: () => { adviceState.data = null; adviceState.error = 'Could not read this device’s journal.'; } });
  const timer = setInterval(() => { adviceState.now = Date.now(); }, 60000);
  return () => { sub.unsubscribe(); clearInterval(timer); adviceState.data = null; };
}
