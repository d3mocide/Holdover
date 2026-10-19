// Export the device's current copy, including entries that have never reached the server.
export function journalRows(snapshot) {
  const clean = (rows = []) => rows.filter((r) => !r.deleted).map(({ dirty, photo_blob, ...row }) => row);
  const trips = clean(snapshot.trips), tripIds = new Set(trips.map((t) => t.uuid));
  return { trips, catches: clean(snapshot.catches).filter((c) => tripIds.has(c.trip_uuid)),
    pins: clean(snapshot.pins), gear: clean(snapshot.gear), setups: clean(snapshot.setups) };
}

export async function journalJson(snapshot) {
  const data = journalRows(snapshot);
  for (const key of ['catches', 'gear']) {
    for (const row of data[key]) {
      const photo = snapshot[key].find((r) => r.uuid === row.uuid)?.photo_blob;
      if (photo) {
        const bytes = new Uint8Array(await photo.arrayBuffer());
        let binary = '';
        for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
        row.photo_data_url = `data:${photo.type || 'application/octet-stream'};base64,${btoa(binary)}`;
      }
    }
  }
  return JSON.stringify({ scope: 'this_device', exported_at: new Date().toISOString(), ...data }, null, 2);
}

const csvCell = (value) => {
  let text = value == null ? '' : String(value);
  if (typeof value === 'string' && /^\s*[=+@-]/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};

export function journalCsv(snapshot) {
  const d = journalRows(snapshot);
  const items = new Map(d.gear.map((g) => [g.uuid, g.name])), setups = new Map(d.setups.map((s) => [s.uuid, s.name]));
  const rows = [['trip_uuid', 'started_at', 'ended_at', 'waterbody_id', 'lat', 'lon', 'species', 'count',
    'length_in', 'method', 'kept', 'trip_notes', 'conditions_source', 'setup', 'caught_on']];
  for (const trip of d.trips) {
    const catches = d.catches.filter((c) => c.trip_uuid === trip.uuid);
    for (const c of catches.length ? catches : [null]) rows.push([
      trip.uuid, trip.started_at, trip.ended_at, trip.waterbody_id, trip.lat, trip.lon,
      c?.species, c?.count, c?.length_in, c?.method, c?.kept, trip.notes, trip.conditions_source,
      setups.get(trip.setup_uuid), items.get(c?.gear_uuid)
    ]);
  }
  return rows.map((row) => row.map(csvCell).join(',')).join('\r\n') + '\r\n';
}
