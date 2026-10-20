// Personal advice is computed on-device from the current journal, never sent to the model or public API.
const HOUR = 3600000;
const number = v => typeof v === 'number' && Number.isFinite(v);
const parsed = v => { try { return typeof v === 'string' ? JSON.parse(v) : v; } catch { return null; } };
const timely = (stamp, at, hours) => Number.isFinite(Date.parse(stamp)) && Date.parse(stamp) <= at && at - Date.parse(stamp) <= hours * HOUR;
const flows = (c, at) => (Array.isArray(c?.gauges) ? c.gauges : []).filter(g => typeof g?.site_no === 'string' && g.site_no && number(g.values?.discharge_cfs?.value) &&
  g.values.discharge_cfs.value > 0 && !g.values.discharge_cfs.stale && timely(g.values.discharge_cfs.observed_at, at, 3))
  .sort((a, b) => a.site_no.localeCompare(b.site_no));
const temperature = (c, at) => number(c?.weather?.temp_f) && timely(c.weather_as_of, at, 6) ? c.weather.temp_f : null;

export function dayContext(c) {
  return { gauges: c?.gauges ?? [], weather: c?.weather?.day, weather_as_of: c?.weather?.as_of };
}

/** Conservative comparison rule, not a validated fishing range. Rivers need the same gauge within 20% of
 * the latest flow; other waters need air temperature within 10 F. Old snapshots must be close to trip start. */
export function journalAdvice(water, context, data, now = Date.now()) {
  const trips = data.trips.filter(t => !t.deleted && t.waterbody_id === water.id &&
    Number.isFinite(Date.parse(t.started_at)) && Date.parse(t.started_at) <= now);
  const currentFlow = flows(context, now)[0], temp = temperature(context, now);
  const ready = water.kind === 'river' ? !!currentFlow : temp !== null;
  const rule = water.kind === 'river' ? 'Same water and USGS gauge, flow within 20% of the latest observation.' : 'Same water, forecast air temperature within 10°F.';
  const catches = new Map();
  for (const c of data.catches) if (!c.deleted) {
    if (!catches.has(c.trip_uuid)) catches.set(c.trip_uuid, []);
    catches.get(c.trip_uuid).push(c);
  }
  const matched = [];
  if (ready) for (const trip of trips) {
    const past = parsed(trip.conditions_json), at = Date.parse(trip.started_at);
    // Backdated logs and expired cached snapshots cannot stand in for conditions during the trip.
    if (!past || !Number.isFinite(Date.parse(past.captured_at)) || Math.abs(Date.parse(past.captured_at) - at) > 3 * HOUR) continue;
    const sameFlow = flows(past, at).find(g => currentFlow?.site_no === g.site_no &&
      Math.abs(g.values.discharge_cfs.value - currentFlow.values.discharge_cfs.value) / currentFlow.values.discharge_cfs.value <= .2);
    const oldTemp = temperature(past, at);
    if (water.kind === 'river' ? !sameFlow : oldTemp === null || Math.abs(oldTemp - temp) > 10) continue;
    const rows = catches.get(trip.uuid) ?? [];
    if (rows.some(c => !Number.isInteger(c.count) || c.count < 0)) continue;
    matched.push({ ...trip, fish: rows.reduce((n, c) => n + c.count, 0), catches: rows,
      comparison_value: water.kind === 'river' ? sameFlow.values.discharge_cfs.value : oldTemp,
      comparison_as_of: water.kind === 'river' ? sameFlow.values.discharge_cfs.observed_at : past.weather_as_of });
  }
  matched.sort((a, b) => b.started_at.localeCompare(a.started_at) || a.uuid.localeCompare(b.uuid));
  const successes = matched.filter(t => t.fish > 0).length;
  const eligible = matched.length >= 3;
  // At most five points; small samples shrink toward no adjustment. No data never penalises a water.
  const adjustment = eligible ? Math.round(5 * (2 * successes / matched.length - 1) * Math.min(matched.length / 10, 1) * 10) / 10 : 0;
  const gear = [];
  for (const g of data.gear.filter(g => !g.deleted && g.status === 'active' && ['lure', 'fly'].includes(g.kind))) {
    const used = matched.filter(t => {
      const ids = parsed(t.gear_json);
      return (Array.isArray(ids) && ids.includes(g.uuid)) || t.catches.some(c => c.gear_uuid === g.uuid);
    });
    const fish = used.reduce((n, t) => n + t.catches.filter(c => c.gear_uuid === g.uuid).reduce((n, c) => n + c.count, 0), 0);
    const successful = used.filter(t => t.catches.some(c => c.gear_uuid === g.uuid && c.count > 0)).length;
    if (successful) gear.push({ uuid: g.uuid, name: g.name, trips: used.length, successes: successful, fish });
  }
  const setups = data.setups.filter(s => !s.deleted).map(s => {
    const used = matched.filter(t => t.setup_uuid === s.uuid);
    return { uuid: s.uuid, name: s.name, trips: used.length, successes: used.filter(t => t.fish > 0).length };
  }).filter(s => s.successes);
  const byResults = (a, b) => b.successes - a.successes || b.trips - a.trips || a.name.localeCompare(b.name);
  const current = water.kind === 'river' ? (currentFlow ? { value: currentFlow.values.discharge_cfs.value,
    as_of: currentFlow.values.discharge_cfs.observed_at, site_no: currentFlow.site_no } : null) :
    (temp !== null ? { value: temp, as_of: context.weather_as_of } : null);
  return { total: trips.length, ready, rule, current, flow: water.kind === 'river', matched, successes, eligible, adjustment,
    gear: gear.sort(byResults).slice(0, 3), setups: setups.sort(byResults).slice(0, 3) };
}

export function personalSpots(spots, data, enabled, now = Date.now()) {
  const out = spots.map(s => {
    const advice = journalAdvice(s.waterbody, s.journal_context, data, now);
    const score = enabled && advice.eligible ? Math.max(0, Math.min(100, Math.round((s.score + advice.adjustment) * 10) / 10)) : s.score;
    return { ...s, public_score: s.score, score, advice, personal: enabled && advice.eligible };
  });
  if (enabled) out.sort((a, b) => b.score - a.score || a.rank - b.rank);
  return out.map((s, i) => ({ ...s, rank: i + 1 }));
}
