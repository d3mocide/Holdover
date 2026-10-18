// Your own history at one waterbody, computed from the local journal (so it works offline). Pure functions.

const live = (rows) => (rows || []).filter((r) => !r.deleted);
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/** Short, honest phrases from a trip's captured conditions: only what was actually recorded, never a guess. */
export function describeConditions(conditionsJson) {
  let c = conditionsJson;
  if (typeof c === 'string') { try { c = JSON.parse(c); } catch { return []; } }
  if (!c || typeof c !== 'object') return [];
  const out = [];
  const air = num(c.weather?.temp_f);
  if (air != null) out.push(`${Math.round(air)}°F air${c.weather?.short ? `, ${String(c.weather.short).toLowerCase()}` : ''}`);
  const water = num(c.water_temp_f?.value);
  if (water != null) out.push(`water ${Math.round(water)}°F`);
  const g = (c.gauges || []).find((x) => num(x?.values?.discharge_cfs?.value) != null);
  if (g) out.push(`${Math.round(g.values.discharge_cfs.value).toLocaleString('en-US')} cfs${g.trend ? ` ${g.trend}` : ''}`);
  if (c.moon?.phase) out.push(String(c.moon.phase).toLowerCase());
  if (c.source === 'cached') out.push('from cached values');
  return out;
}

/**
 * @returns {{trips, fish, last, bySpecies: {species, count}[], best: {uuid, date, fish, conditions: string[]} | null,
 *            topGear: {uuid, name, count} | null}}
 * best: the trip with the most fish (ties go to the most recent); null if nothing was caught.
 * topGear: the lure or fly most often recorded as "caught on" here.
 */
export function waterbodyHistory({ trips = [], catches = [], gear = [], waterbodyId }) {
  const mine = live(trips).filter((t) => t.waterbody_id === waterbodyId);
  const ids = new Set(mine.map((t) => t.uuid));
  const fishes = live(catches).filter((c) => ids.has(c.trip_uuid));
  const byTrip = new Map();
  const bySpecies = new Map();
  const byGear = new Map();
  for (const c of fishes) {
    const n = c.count || 0;
    byTrip.set(c.trip_uuid, (byTrip.get(c.trip_uuid) ?? 0) + n);
    if (n) bySpecies.set(c.species || 'unspecified', (bySpecies.get(c.species || 'unspecified') ?? 0) + n);
    if (n && c.gear_uuid) byGear.set(c.gear_uuid, (byGear.get(c.gear_uuid) ?? 0) + n);
  }
  const day = (t) => (t.started_at || '').slice(0, 10);
  const sorted = [...mine].sort((a, b) => (b.started_at || '').localeCompare(a.started_at || ''));
  let best = null;
  for (const t of sorted) { // most recent first, so a tie keeps the newer trip
    const f = byTrip.get(t.uuid) ?? 0;
    if (f > 0 && (!best || f > best.fish)) best = { uuid: t.uuid, date: day(t), fish: f, conditions: describeConditions(t.conditions_json) };
  }
  const names = new Map(live(gear).map((g) => [g.uuid, g.name]));
  const top = [...byGear].filter(([u]) => names.has(u)).sort((a, b) => b[1] - a[1])[0];
  let total = 0;
  for (const v of byTrip.values()) total += v;
  return {
    trips: mine.length, fish: total, last: sorted[0] ? day(sorted[0]) || null : null,
    bySpecies: [...bySpecies].map(([species, count]) => ({ species, count })).sort((a, b) => b.count - a.count || a.species.localeCompare(b.species)),
    best, topGear: top ? { uuid: top[0], name: names.get(top[0]), count: top[1] } : null
  };
}
