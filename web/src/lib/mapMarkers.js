import { gaugeStale } from './gaugeText.js';

// Bottom to top. Hit testing follows the same priority as drawing, including AI-read reports.
export const markerLayers = ['stocking-pts', 'gauge-pts', 'river-pts', 'journal-pts', 'home-pts', 'advisory-ring', 'report-badge'];

export function markerHit(features) {
  for (const id of [...markerLayers].reverse()) {
    const hit = features.find((f) => f.layer.id === id);
    if (hit) return hit;
  }
  return null;
}

export function gaugeDetails(p, now = Date.now(), clockMode = '12') {
  const content = document.createElement('div');
  content.className = 'gauge-details';
  content.setAttribute('role', 'group');
  content.setAttribute('aria-label', `Stream gauge: ${p.name}`);
  const line = (tag, text, cls) => {
    const el = document.createElement(tag); el.textContent = text; el.className = cls;
    content.appendChild(el); return el;
  };
  line('h3', p.name, 'gauge-title');
  line('div', p.flow_cfs != null ? `${Math.round(p.flow_cfs).toLocaleString()} cfs` : 'No flow data', 'gauge-value mono');
  if (p.trend && p.flow_cfs != null) line('div', p.trend, 'gauge-trend');
  const observed = Date.parse(p.as_of);
  const stale = gaugeStale({ as_of: p.as_of, stale: p.stale === true || p.stale === 'true' }, now);
  line('div', `USGS ${p.site_no} · Provisional${stale ? ' · Stale' : ''}`, 'gauge-meta');
  const time = line('time', Number.isFinite(observed) ? `As of ${new Date(observed).toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: clockMode !== '24', timeZoneName: 'short' })}` : 'Observation time unavailable', 'gauge-meta');
  if (Number.isFinite(observed)) time.dateTime = new Date(observed).toISOString();
  if (p.waterbody_id != null && p.waterbody_id !== 'null') line('button', 'Open waterbody', 'pill gauge-action');
  return content;
}
