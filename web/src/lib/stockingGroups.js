// Stocking weeks for display: what is coming (soonest first) and what already happened (newest first), each under a
// year heading. ODFW publishes about a year ahead, so one list can hold the same month in two different years.
const byYear = (items) => {
  const years = [];
  for (const s of items) {
    const year = s.week_of.slice(0, 4);
    const last = years[years.length - 1];
    if (last && last.year === year) last.items.push(s); else years.push({ year, items: [s] });
  }
  return years;
};

export function stockingSections(stocking) {
  const upcoming = stocking.filter((s) => s.freshness === 'upcoming').sort((a, b) => a.week_of.localeCompare(b.week_of));
  const past = stocking.filter((s) => s.freshness !== 'upcoming').sort((a, b) => b.week_of.localeCompare(a.week_of));
  return [
    { key: 'upcoming', title: 'Coming up', years: byYear(upcoming) },
    { key: 'past', title: 'Already stocked', years: byYear(past) }
  ].filter((s) => s.years.length);
}
