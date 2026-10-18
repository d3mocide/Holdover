// Time-of-day wording. The server sends daylight as 24-hour "HH:MM" text (also inside planner sentences), and timestamps
// as ISO strings; both go through here so the 12/24-hour setting applies everywhere.
export function to12(h, m) {
  const suffix = h >= 12 ? 'PM' : 'AM';
  return `${h % 12 === 0 ? 12 : h % 12}:${String(m).padStart(2, '0')} ${suffix}`;
}
const pad = (n) => String(n).padStart(2, '0');

/** An ISO timestamp as a local time of day. */
export function formatTime(iso, mode = '12') {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return mode === '24' ? `${pad(d.getHours())}:${pad(d.getMinutes())}` : to12(d.getHours(), d.getMinutes());
}

/** Rewrites every 24-hour "HH:MM" in a piece of text (a daylight range, a planner sentence). Leaves other text alone. */
export function formatClockText(text, mode = '12') {
  if (!text || mode === '24') return text;
  return text.replace(/\b([01]\d|2[0-3]):([0-5]\d)\b/g, (_, h, m) => to12(Number(h), Number(m)));
}
