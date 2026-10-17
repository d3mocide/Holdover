import { api } from './api.js';
import { db } from './db.js';

/** Day bundle with an IndexedDB copy, so conditions survive going offline. Returns {data, source, as_of}. */
export async function loadDay(id, dayIso) {
  try {
    const data = await api.day(id, dayIso);
    await db.cond.put({ waterbody_id: id, fetched_at: new Date().toISOString(), date: dayIso, payload: data });
    return { data, source: 'live', as_of: new Date().toISOString() };
  } catch (e) {
    const c = await db.cond.get(id);
    if (c) return { data: c.payload, source: 'cached', as_of: c.fetched_at };
    throw e;
  }
}

/** What goes in trip.conditions_json. Live if reachable (6 s cap), else the last cached bundle. */
export async function captureConditions(wbId) {
  if (!wbId) return { json: null, source: null };
  const day = new Date().toISOString().slice(0, 10);
  let res;
  try {
    const data = await Promise.race([api.day(wbId, day), new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 6000))]);
    await db.cond.put({ waterbody_id: wbId, fetched_at: new Date().toISOString(), date: day, payload: data });
    res = { data, source: 'live', as_of: new Date().toISOString() };
  } catch {
    const c = await db.cond.get(wbId);
    if (!c) return { json: null, source: null };
    res = { data: c.payload, source: 'cached', as_of: c.fetched_at };
  }
  const c = res.data.conditions;
  const json = {
    captured_at: new Date().toISOString(), source: res.source, cache_as_of: res.source === 'cached' ? res.as_of : undefined,
    weather: c.weather?.day ?? null, weather_as_of: c.weather?.as_of ?? null,
    water_temp_f: c.water_temp_f ?? null,
    gauges: c.gauges.map((g) => ({ site_no: g.site_no, name: g.name, values: g.values, as_of: g.as_of, trend: g.trend, provisional: true })),
    daylight: c.daylight, moon: c.moon,
    stocking_recent: c.stocking.filter((s) => s.freshness !== 'upcoming'),
    advisories: c.advisories.map((a) => ({ kind: a.kind, issued: a.issued }))
  };
  return { json, source: res.source };
}
