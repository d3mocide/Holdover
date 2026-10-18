// Wording for the look-ahead stocking schedule.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const num = (n) => Number(n).toLocaleString('en-US');

export const monthLabel = (ym) => { const [y, m] = ym.split('-').map(Number); return `${MONTHS[m - 1]} ${y}`; };
export const monthShort = (ym, now = new Date()) => { const [y, m] = ym.split('-').map(Number); return y === now.getFullYear() ? MONTHS[m - 1] : `${MONTHS[m - 1]} ${y}`; };
export const plural = (n, one, many = `${one}s`) => `${num(n)} ${Number(n) === 1 ? one : many}`;
export const weekSummary = (w) => `${plural(w.waterbodies.length, 'waterbody', 'waterbodies')} · ${plural(w.total_fish, 'fish', 'fish')}`;
/** First and last day of a "YYYY-MM" month as ISO dates. */
export function monthRange(ym) {
  const [y, m] = ym.split('-').map(Number);
  const last = new Date(Date.UTC(y, m, 0)).getUTCDate();
  return [`${ym}-01`, `${ym}-${String(last).padStart(2, '0')}`];
}
