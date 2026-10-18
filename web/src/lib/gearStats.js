// What works for me: pure functions over the local journal, so stats work offline and are easy to test.
// Inputs are the rows as stored in IndexedDB (deleted rows are ignored here).

const parse = (json) => { try { const v = JSON.parse(json); return Array.isArray(v) ? v : []; } catch { return []; } };
const live = (rows) => rows.filter((r) => !r.deleted);

/**
 * @returns {{
 *   items: {uuid, name, kind, trips, caught, fishOnTrips}[],
 *   setups: {uuid, name, trips, fish, perTrip, waters: {waterbody_id, fish}[]}[],
 *   totals: {trips, fish}
 * }}
 * trips: trips the item was used on (named on the trip, in the trip's setup, or the lure of a catch).
 * caught: fish explicitly recorded as caught on it. fishOnTrips: all fish on the trips it was used on, which
 * is shared credit (a trip with three lures counts its fish for each), so it is labelled that way in the UI.
 */
export function gearStats({ trips = [], catches = [], gear = [], setups = [] }) {
  const T = live(trips), C = live(catches), G = live(gear), S = live(setups);
  const tripIds = new Set(T.map((t) => t.uuid));
  const fishByTrip = new Map();
  for (const c of C) if (tripIds.has(c.trip_uuid)) fishByTrip.set(c.trip_uuid, (fishByTrip.get(c.trip_uuid) ?? 0) + (c.count || 0));
  const setupItems = new Map(S.map((s) => [s.uuid, parse(s.item_uuids_json)]));

  const usedOn = new Map(G.map((g) => [g.uuid, new Set()]));
  const caught = new Map(G.map((g) => [g.uuid, 0]));
  const mark = (itemUuid, tripUuid) => usedOn.get(itemUuid)?.add(tripUuid);
  for (const t of T) {
    for (const u of parse(t.gear_json)) mark(u, t.uuid);
    for (const u of setupItems.get(t.setup_uuid) ?? []) mark(u, t.uuid);
  }
  for (const c of C) {
    if (!c.gear_uuid || !tripIds.has(c.trip_uuid)) continue;
    mark(c.gear_uuid, c.trip_uuid);
    if (caught.has(c.gear_uuid)) caught.set(c.gear_uuid, caught.get(c.gear_uuid) + (c.count || 0));
  }
  const items = G.map((g) => {
    const on = usedOn.get(g.uuid);
    let fishOnTrips = 0;
    for (const id of on) fishOnTrips += fishByTrip.get(id) ?? 0;
    return { uuid: g.uuid, name: g.name, kind: g.kind, trips: on.size, caught: caught.get(g.uuid), fishOnTrips };
  }).sort((a, b) => b.caught - a.caught || b.fishOnTrips - a.fishOnTrips || b.trips - a.trips || a.name.localeCompare(b.name));

  const setupRows = S.map((s) => {
    const mine = T.filter((t) => t.setup_uuid === s.uuid);
    const fish = mine.reduce((n, t) => n + (fishByTrip.get(t.uuid) ?? 0), 0);
    const byWater = new Map();
    for (const t of mine) if (t.waterbody_id != null) byWater.set(t.waterbody_id, (byWater.get(t.waterbody_id) ?? 0) + (fishByTrip.get(t.uuid) ?? 0));
    const waters = [...byWater].map(([waterbody_id, f]) => ({ waterbody_id, fish: f })).sort((a, b) => b.fish - a.fish).slice(0, 3);
    return { uuid: s.uuid, name: s.name, trips: mine.length, fish, perTrip: mine.length ? Math.round((fish / mine.length) * 10) / 10 : 0, waters };
  }).sort((a, b) => b.fish - a.fish || b.trips - a.trips || a.name.localeCompare(b.name));

  let fish = 0;
  for (const v of fishByTrip.values()) fish += v;
  return { items, setups: setupRows, totals: { trips: T.length, fish } };
}

/** Gear that resolves to nothing (deleted, or never synced here) is dropped rather than shown as a blank. */
export function namesFor(json, gear) {
  const byId = new Map(live(gear).map((g) => [g.uuid, g.name]));
  return parse(json).map((u) => byId.get(u)).filter(Boolean);
}
