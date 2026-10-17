const TOKEN_KEY = 'holdover.token';

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}
export function setToken(v) {
  try { v ? localStorage.setItem(TOKEN_KEY, v) : localStorage.removeItem(TOKEN_KEY); } catch { /* storage blocked */ }
}

async function req(path, opts = {}) {
  const headers = { ...(opts.auth ? { Authorization: `Bearer ${getToken()}` } : {}), ...(opts.headers || {}) };
  const r = await fetch(path, { ...opts, headers });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export const api = {
  map: () => req('/api/map?zone=willamette&layers=stocking,gauges,advisories,reports'),
  waterbodyList: () => req('/api/waterbodies'),
  gauges: () => req('/api/gauges'),
  day: (id, date) => req(`/api/day/${id}?date=${date}`),
  report: (zone = 'willamette') => req(`/api/reports?zone=${zone}`),
  reviewItems: () => req('/api/admin/review/items', { auth: true }),
  acceptItem: (id, waterbody_id) =>
    req(`/api/admin/review/items/${id}/accept`, { method: 'POST', auth: true, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ waterbody_id }) }),
  rejectItem: (id) => req(`/api/admin/review/items/${id}/reject`, { method: 'POST', auth: true }),
  runReports: () => req('/api/admin/jobs/reports/run', { method: 'POST', auth: true }),
  waterbody: (id) => req(`/api/waterbodies/${id}`),
  health: () => req('/healthz'),
  aliases: () => req('/api/admin/aliases?status=unconfirmed', { auth: true }),
  waterbodies: () => req('/api/admin/waterbodies', { auth: true }),
  confirm: (id, waterbody_id) =>
    req(`/api/admin/aliases/${id}/confirm`, {
      method: 'POST', auth: true, headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ waterbody_id })
    }),
  runStocking: () => req('/api/admin/jobs/stocking/run', { method: 'POST', auth: true })
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export function weekLabel(iso) {
  if (!iso) return '';
  const [, m, d] = iso.split('-').map(Number);
  return `Week of ${MONTHS[m - 1]} ${d}`;
}
export function hhmm(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}
export const FRESH_LABEL = {
  this_week: 'Stocked this week', recent: 'Stocked in the last 2 weeks',
  older: 'Stocked earlier', upcoming: 'Scheduled'
};

export function longDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

export const asOf = (iso) => (iso ? `as of ${hhmm(iso)}` : 'no data');
export const cToF = (c) => Math.round((c * 9) / 5 + 32);
export const TREND = { rising: '↑ rising', falling: '↓ falling', steady: '→ steady' };
export const isoDay = (offset = 0) => {
  const d = new Date(); d.setDate(d.getDate() + offset);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
