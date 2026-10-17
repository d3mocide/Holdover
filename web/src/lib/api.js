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
  map: () => req('/api/map?zone=willamette'),
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
