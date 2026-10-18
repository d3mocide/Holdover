let onUnauthorized = () => {};
/** The auth store registers here so any signed-in call that comes back 401 flips the app to signed-out. */
export function setUnauthorizedHandler(fn) { onUnauthorized = fn; }

// The session is an HttpOnly cookie, so scripts never see it. X-Holdover is the CSRF marker the server requires
// on every state-changing call (a cross-site page cannot add a custom header without a CORS preflight).
async function req(path, opts = {}) {
  const { auth, json, ...rest } = opts;
  const headers = { 'X-Holdover': '1', ...(json !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(rest.headers || {}) };
  const r = await fetch(path, { ...rest, headers, body: json !== undefined ? JSON.stringify(json) : rest.body, credentials: 'same-origin' });
  if (r.status === 401 && auth) onUnauthorized();
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try { const j = await r.json(); if (typeof j.detail === 'string') msg = j.detail; else if (Array.isArray(j.detail)) msg = j.detail.map((d) => d.msg).join('; '); } catch { /* not JSON */ }
    throw Object.assign(new Error(msg), { status: r.status });
  }
  return r.json();
}

export const api = {
  map: () => req('/api/map?zone=willamette&layers=stocking,gauges,advisories,reports'),
  waterbodyList: () => req('/api/waterbodies'),
  gauges: () => req('/api/gauges'),
  day: (id, date, fishery = 'trout') => req(`/api/day/${id}?date=${date}&fishery=${fishery}`),
  spots: (date, fishery, home = null) =>
    req(`/api/spots?date=${date}&fishery=${fishery}${home ? `&home_lat=${home.lat}&home_lon=${home.lon}` : ''}`),
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
  runStocking: () => req('/api/admin/jobs/stocking/run', { method: 'POST', auth: true }),

  // accounts
  me: () => req('/api/auth/me'),
  login: (username, password) => req('/api/auth/login', { method: 'POST', json: { username, password } }),
  logout: () => req('/api/auth/logout', { method: 'POST' }),
  inviteValid: (code) => req(`/api/auth/invite/${encodeURIComponent(code)}`),
  register: (invite, username, password) => req('/api/auth/register', { method: 'POST', json: { invite, username, password } }),
  changePassword: (current, next) => req('/api/auth/password', { method: 'POST', auth: true, json: { current, new: next } }),
  setHome: (lat, lon) => req('/api/me/home', { method: 'PUT', auth: true, json: { lat, lon } }),
  addFavorite: (id) => req(`/api/me/favorites/${id}`, { method: 'PUT', auth: true }),
  removeFavorite: (id) => req(`/api/me/favorites/${id}`, { method: 'DELETE', auth: true }),
  mergeLocal: (favorites, home) => req('/api/me/merge', { method: 'POST', auth: true, json: { favorites, home } }),

  // admin: users and invites
  adminUsers: () => req('/api/admin/users', { auth: true }),
  adminDisable: (id, disabled) => req(`/api/admin/users/${id}/disabled`, { method: 'POST', auth: true, json: { disabled } }),
  adminSetAdmin: (id, is_admin) => req(`/api/admin/users/${id}/admin`, { method: 'POST', auth: true, json: { is_admin } }),
  adminResetPassword: (id, password) => req(`/api/admin/users/${id}/password`, { method: 'POST', auth: true, json: { password } }),
  adminInvites: () => req('/api/admin/invites', { auth: true }),
  adminCreateInvite: () => req('/api/admin/invites', { method: 'POST', auth: true }),
  adminRevokeInvite: (id) => req(`/api/admin/invites/${id}`, { method: 'DELETE', auth: true })
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

export const FISHERIES = [['trout', 'Stocked trout'], ['steelhead', 'Steelhead & salmon'], ['warmwater', 'Warmwater']];
export const dayLabel = (offset) => {
  if (offset === 0) return 'Today';
  if (offset === 1) return 'Tomorrow';
  const d = new Date(); d.setDate(d.getDate() + offset);
  return d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
};
export const FACTOR_LABEL = { stocking: 'Stocking', report: 'ODFW report', flow: 'Flow', forecast: 'Forecast', distance: 'Distance' };
