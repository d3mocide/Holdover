// Wording and ordering for the Gauges page.
export const medianText = (pct) => (pct == null ? null : pct === 0 ? 'at median' : `${pct > 0 ? '+' : '−'}${Math.abs(pct)}% vs median`);
/** A flow this far from the gauge's own median is worth a second look. */
export const unusual = (pct) => pct != null && Math.abs(pct) >= 20;
export const SORTS = [['name', 'Name'], ['unusual', 'Most unusual'], ['flow', 'Highest flow']];

export function sortGauges(list, mode) {
  const byName = (a, b) => a.name.localeCompare(b.name);
  const cfs = (g) => g.values?.discharge_cfs?.value ?? -1;
  const dev = (g) => (g.vs_median_pct == null ? -1 : Math.abs(g.vs_median_pct));
  const out = [...list];
  if (mode === 'unusual') out.sort((a, b) => dev(b) - dev(a) || byName(a, b));
  else if (mode === 'flow') out.sort((a, b) => cfs(b) - cfs(a) || byName(a, b));
  else out.sort(byName);
  return out;
}

/** The few facts under the number: how it compares, then height and temperature when the gauge has them. */
export function detailParts(g) {
  const v = g.values ?? {};
  return [medianText(g.vs_median_pct), v.gage_height_ft ? `${v.gage_height_ft.value} ft` : null, v.water_temp_f ? `${Math.round(v.water_temp_f.value)}°F` : null].filter(Boolean);
}

const QUALITY = [['dissolved_oxygen_mgl', (v) => `dissolved oxygen ${v.toFixed(1)} mg/L`], ['ph', (v) => `pH ${v.toFixed(1)}`],
  ['turbidity_fnu', (v) => `turbidity ${v < 10 ? v.toFixed(1) : Math.round(v)} FNU`], ['conductance_uscm', (v) => `conductance ${Math.round(v)} µS/cm`]];
/** The water-quality readings a gauge has, newest day only (a sensor that stopped reporting a day ago is not shown as current). */
export function qualityParts(g, now = Date.now()) {
  const v = g.values ?? {};
  return QUALITY.filter(([k]) => v[k] && now - new Date(v[k].observed_at).getTime() < 36 * 3600 * 1000).map(([k, f]) => f(v[k].value));
}
