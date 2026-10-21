const finite = v => typeof v === 'number' && Number.isFinite(v) && v >= 0;
export const baselineStale = (d, now = Date.now()) => !d?.as_of || !!d.stale || !Number.isFinite(Date.parse(d.as_of)) ||
  Date.parse(d.as_of) > now || now - Date.parse(d.as_of) > 45 * 86400000 || d.end_year !== new Date(now).getFullYear() - 1;
export const flowStale = (c, now = Date.now()) => !c || !!c.stale || !Number.isFinite(Date.parse(c.observed_at)) ||
  Date.parse(c.observed_at) > now || now - Date.parse(c.observed_at) > 3 * 3600000;

/** Leave missing/insufficient days blank; the dot is one observation, never a forecast line. */
export function seasonalChart(data) {
  const rows = data?.series ?? [], current = data?.current;
  const valid = r => finite(r.p25) && finite(r.median) && finite(r.p75) && r.p25 <= r.median && r.median <= r.p75;
  const values = rows.filter(valid).flatMap(r => [r.p25, r.p75]);
  const dotIndex = current ? rows.findIndex(r => r.date === current.date) : -1;
  if (dotIndex >= 0 && finite(current.value)) values.push(current.value);
  const max = Math.max(1, ...values), x = i => 12 + i / Math.max(1, rows.length - 1) * 376, y = v => 144 - v / max * 128;
  const groups = []; let group = [];
  for (let i = 0; i < rows.length; i++) {
    if (valid(rows[i])) group.push({ ...rows[i], i });
    else if (group.length) { groups.push(group); group = []; }
  }
  if (group.length) groups.push(group);
  const point = (r, key) => `${x(r.i).toFixed(1)},${y(r[key]).toFixed(1)}`;
  return { max, bands: groups.filter(g => g.length > 1).map(g => [...g.map(r => point(r, 'p75')), ...[...g].reverse().map(r => point(r, 'p25'))].join(' ')),
    lines: groups.map(g => g.map(r => point(r, 'median')).join(' ')),
    dot: dotIndex >= 0 && finite(current.value) ? { x: x(dotIndex), y: y(current.value) } : null };
}
