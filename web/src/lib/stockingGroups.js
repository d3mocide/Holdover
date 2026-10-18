// Stocking weeks for display: what is coming (soonest first) and what already happened (newest first).
// ODFW publishes about a year ahead, so a list can hold the same month in two different years: a week's label carries
// its year whenever that year is not the current one, so nothing is ambiguous and no year headings are needed.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function weekLabelYear(iso, today = new Date()) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return `Week of ${MONTHS[m - 1]} ${d}${y !== today.getFullYear() ? `, ${y}` : ''}`;
}

export function stockingSections(stocking) {
  const upcoming = stocking.filter((s) => s.freshness === 'upcoming').sort((a, b) => a.week_of.localeCompare(b.week_of));
  const past = stocking.filter((s) => s.freshness !== 'upcoming').sort((a, b) => b.week_of.localeCompare(a.week_of));
  return [
    { key: 'upcoming', title: 'Coming up', items: upcoming },
    { key: 'past', title: 'Already stocked', items: past }
  ].filter((s) => s.items.length);
}

/** The first `n` rows to show and how many are tucked behind "show more". */
export const split = (items, n = 4) => ({ shown: items.slice(0, n), rest: items.slice(n) });
