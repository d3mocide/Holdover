// Wording for the fire card. The app reports what ODF and NIFC publish and links to them. It never says what is
// allowed or closed, and "no fire listed" is never worded as "no fire".
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const shortDate = (iso) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : `${MONTHS[d.getMonth()]} ${d.getDate()}`; };

export function dangerText(d) {
  if (!d) return null;
  if (!d.covered) return 'This waterbody is outside the lands ODF protects, so ODF publishes no danger level here.';
  return `${d.label} (level ${d.level} of 4), ODF area ${d.area}`;
}
export const dangerHigh = (d) => !!d?.covered && d.level >= 3;

export function fireLine(f) {
  const where = f.inside ? 'this waterbody is inside the mapped fire area' : `${Math.round(f.distance_km)} km away`;
  const contained = f.percent_contained == null ? 'containment not reported' : `${f.percent_contained}% contained`;
  const size = f.acres ? `${f.acres.toLocaleString('en-US')} acres, ` : '';
  const upd = f.updated ? `, perimeter updated ${shortDate(f.updated)}` : '';
  return `${f.name} fire: ${where}; ${size}${contained}${upd}`;
}
export const nearbyText = (n) => (n == null ? null
  : n.fires.length ? null : `No active wildfire perimeter within ${n.near_km} km in the data NIFC publishes. Perimeters can lag a new fire.`);

// Rendered polygon fragments can repeat at tile boundaries. A popup names each incident once.
export function firePerimeters(features) {
  const byName = new Map();
  for (const { properties: p } of features) {
    if (!p.name) continue;
    const previous = byName.get(p.name);
    if (!previous || (p.updated ?? '') > (previous.updated ?? '')) byName.set(p.name, p);
  }
  return [...byName.values()];
}
