// Keep real sample times and break the line across missing observations rather than inventing values.
export function chartLines(points, maxGapMs = 2 * 3600000) {
  const rows = points.filter((p) => Number.isFinite(p.value) && Number.isFinite(Date.parse(p.observed_at)))
    .map((p) => ({ ...p, time: Date.parse(p.observed_at) })).sort((a, b) => a.time - b.time);
  if (!rows.length) return { lines: [], min: null, max: null, rows };
  const values = rows.map((p) => p.value), min = Math.min(...values), max = Math.max(...values);
  const span = rows.at(-1).time - rows[0].time || 1, range = max - min || Math.max(1, Math.abs(max) * 0.1);
  const lines = []; let line = [];
  for (const [i, p] of rows.entries()) {
    if (i && p.time - rows[i - 1].time > maxGapMs) { lines.push(line.join(' ')); line = []; }
    line.push(`${(12 + 376 * (p.time - rows[0].time) / span).toFixed(1)},${(128 - 110 * (p.value - min) / range).toFixed(1)}`);
  }
  lines.push(line.join(' '));
  return { lines, min, max, rows };
}
