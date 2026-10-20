import { gaugeStale } from './gaugeText.js';
import { icons } from './icons.js';
import { longDate } from './api.js';
import { firePerimeters } from './fireText.js';

// Bottom to top. Hit testing follows the same priority as drawing, including AI-read reports.
export const markerLayers = ['gauge-pts', 'river-pts', 'stocking-pts', 'journal-pts', 'home-pts', 'advisory-ring', 'report-badge'];

// A feature can be returned twice at a tile boundary; different layers/waters remain distinct.
export function markerChoices(features) {
  const seen = new Set(), choices = [];
  for (const layer of [...markerLayers].reverse()) {
    if (layer === 'home-pts') continue;
    for (const feature of features.filter((f) => f.layer.id === layer)) {
      const key = JSON.stringify([layer, feature.properties.id ?? feature.properties.site_no ?? [feature.properties.label, feature.geometry?.coordinates]]);
      if (seen.has(key)) continue;
      seen.add(key); choices.push(feature);
    }
  }
  return choices;
}

export function markerDescription(feature) {
  const p = feature.properties;
  switch (feature.layer.id) {
    case 'report-badge': return `Report · ${p.rating ?? 'Unknown rating'}${p.reviewed === false || p.reviewed === 'false' ? ' · AI-read, unreviewed' : ''}`;
    case 'advisory-ring': return 'Algae advisory · read details';
    case 'river-pts': return 'River · open details';
    case 'gauge-pts': return `Stream gauge · USGS ${p.site_no} · provisional`;
    case 'journal-pts': return 'My trip or pin';
    default: {
      const state = { this_week: 'Stocked this week', recent: 'Stocked in the last 2 weeks', older: 'Older stocking', upcoming: 'Scheduled stocking' }[p.freshness] ?? 'Stocking';
      return [p.kind, state, p.freshness === 'upcoming' && p.next_week ? `week of ${longDate(p.next_week)} · may change` : null].filter(Boolean).join(' · ');
    }
  }
}

export function markerPicker(choices, onchoose) {
  const content = document.createElement('div');
  content.className = 'marker-picker'; content.setAttribute('role', 'group'); content.setAttribute('aria-label', 'Map items here');
  const title = document.createElement('h3'); title.textContent = 'Choose a map item'; content.appendChild(title);
  const note = document.createElement('p'); note.textContent = `${choices.length} items nearby. Zoom in to separate places.`; content.appendChild(note);
  const list = document.createElement('div'); list.className = 'marker-choices'; content.appendChild(list);
  const names = { 'report-badge': 'reports', 'advisory-ring': 'advisory', 'river-pts': 'flow', 'gauge-pts': 'gauge', 'journal-pts': 'journal', 'stocking-pts': 'stocking' };
  for (const feature of choices) {
    const button = document.createElement('button'); button.type = 'button';
    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    for (const [key, value] of Object.entries({ viewBox: '0 0 24 24', width: '22', height: '22', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.75', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' })) icon.setAttribute(key, value);
    icon.innerHTML = icons[names[feature.layer.id]]; // trusted shared artwork; names/data below stay text
    const text = document.createElement('span'), name = document.createElement('strong'), detail = document.createElement('span');
    name.textContent = feature.properties.name ?? feature.properties.label ?? 'Map item';
    detail.textContent = markerDescription(feature); text.append(name, detail); button.append(icon, text);
    button.addEventListener('click', () => onchoose(feature)); list.appendChild(button);
  }
  return content;
}

export function fireDetails(features, clockMode = '12') {
  const content = document.createElement('div'); content.className = 'fire-details';
  content.setAttribute('role', 'group'); content.setAttribute('aria-label', 'Wildfire perimeter details');
  for (const p of firePerimeters(features)) {
    const name = document.createElement('h3'); name.textContent = `${p.name} fire`; content.appendChild(name);
    const updated = Date.parse(p.updated);
    const time = document.createElement('p');
    time.textContent = Number.isFinite(updated) ? `Perimeter updated ${new Date(updated).toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: clockMode !== '24', timeZoneName: 'short' })}` : 'Perimeter update time unavailable';
    content.appendChild(time);
  }
  const note = document.createElement('p'); note.textContent = 'NIFC mapped perimeter. Perimeters can lag conditions. This is not a closure notice.'; content.appendChild(note);
  const link = document.createElement('a'); link.href = 'https://wildfire.oregon.gov'; link.target = '_blank'; link.rel = 'noopener'; link.textContent = 'Official Oregon wildfire information'; content.appendChild(link);
  return content;
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
