// Wording for the Willamette Falls fish-passage card. Counts and ten-year averages are ODFW's (via DART); nothing here compares fish to a river.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const num = (n) => Number(n).toLocaleString('en-US');
export const dayText = (iso) => { const [, m, d] = iso.split('-').map(Number); return `${MONTHS[m - 1]} ${d}`; };
export const rangeText = (p) => `${dayText(p.from)} to ${dayText(p.through)}${p.days_reported < 7 ? ` (${p.days_reported} days reported)` : ''}`;
export function speciesLine(s) {
  if (s.avg10 > 0) return `${s.label}: ${num(s.count)} fish · ten-year average for the same days ${num(s.avg10)}`;
  return `${s.label}: ${num(s.count)} fish`;
}
/** The species worth a line, biggest first (so the run that is on shows first). */
export const shownSpecies = (p) => Object.entries(p?.species ?? {}).filter(([k]) => ['coho', 'chinook', 'steelhead'].includes(k)).map(([, v]) => v).sort((a, b) => b.count - a.count);
