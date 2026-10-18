// Holdover icon set. 24x24 grid, 1.75 stroke, round caps and joins. Strokes use currentColor.
// Elements inside <g class="a"> are the duotone accent: filled, no stroke, drawn at reduced opacity.
// One source for the UI (Icon.svelte) and the atlas used for review.

const FISH = 'M2.5 12c2.2-3.6 6-5 9.5-4.2 2 .5 3.5 1.7 4.8 3.2l4.7-3.3v8.6l-4.7-3.3c-1.3 1.5-2.8 2.7-4.8 3.2-3.5.8-7.3-.6-9.5-4.2z';

export const icons = {
  // --- navigation ---
  map: '<path d="M9 4.5 3.5 6.5v13L9 17.5l6 2 5.5-2v-13L15 6.5z"/><path d="M9 4.5v13M15 6.5v13"/><g class="a"><path d="M9 4.5v13l6 2v-13z"/></g>',
  plan: '<path d="M4.5 6.5h15v13h-15zM4.5 10.5h15M8.5 4v3.5M15.5 4v3.5M9 15.2l2.1 2.1 4-4.3"/><g class="a"><path d="M4.5 6.5h15v4h-15z"/></g>',
  journal: '<path d="M7 3.5h10.5a1 1 0 0 1 1 1v15a1 1 0 0 1-1 1H7z"/><path d="M7 3.5v17M10.5 8.5h5M10.5 12h5"/><g class="a"><path d="M14.5 3.5v6l1.75-1.4 1.75 1.4v-6z"/></g>',
  gauge: '<path d="M12 3 21 12 12 21 3 12z"/><path d="M12 8c1.9 2.5 3 3.9 3 5.4a3 3 0 0 1-6 0C9 11.9 10.1 10.5 12 8z"/><g class="a"><path d="M12 8c1.9 2.5 3 3.9 3 5.4a3 3 0 0 1-6 0C9 11.9 10.1 10.5 12 8z"/></g>',
  settings: '<path d="M4 8h8.5M17.5 8H20M4 16h2.5M11.5 16H20"/><circle cx="15" cy="8" r="2.5"/><circle cx="9" cy="16" r="2.5"/><g class="a"><circle cx="15" cy="8" r="2.5"/><circle cx="9" cy="16" r="2.5"/></g>',
  layers: '<path d="M12 3.5 3.5 8.2 12 13l8.5-4.8z"/><path d="M3.5 12.2 12 17l8.5-4.8M3.5 16.2 12 21l8.5-4.8"/><g class="a"><path d="M12 3.5 3.5 8.2 12 13l8.5-4.8z"/></g>',
  legend: '<circle cx="6.5" cy="7" r="2"/><circle cx="6.5" cy="12" r="2"/><circle cx="6.5" cy="17" r="2"/><path d="M12 7h8M12 12h8M12 17h8"/>',
  close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  external: '<path d="M14 4.5h5.5V10M19.5 4.5 11 13M17.5 14v5.5h-13v-13H10"/>',
  offline: '<path d="M7 18a4.4 4.4 0 0 1-.7-8.7 6 6 0 0 1 11.5 1.5A3.6 3.6 0 0 1 17 18"/><path d="M12 11.5V19M9.2 16.4 12 19.2l2.8-2.8"/><g class="a"><path d="M7 18a4.4 4.4 0 0 1-.7-8.7 6 6 0 0 1 11.5 1.5A3.6 3.6 0 0 1 17 18z"/></g>',
  log: '<path d="M12 21s-6.2-5.3-6.2-10.2a6.2 6.2 0 1 1 12.4 0C18.2 15.7 12 21 12 21z"/><path d="M12 8v5.5M9.2 10.8h5.6"/><g class="a"><path d="M12 21s-6.2-5.3-6.2-10.2a6.2 6.2 0 1 1 12.4 0C18.2 15.7 12 21 12 21z"/></g>',

  // --- subjects ---
  fish: `<path d="${FISH}"/><path d="M9.6 9.3c.9 1.6.9 4.1 0 5.7"/><circle cx="6.6" cy="11" r=".9" fill="currentColor" stroke="none"/><g class="a"><path d="${FISH}"/></g>`,
  stocking: `<path d="M3 17.5h11.5V9.5H3zM14.5 12h3.8l2.7 3v2.5h-6.5"/><circle cx="7" cy="18.5" r="1.8"/><circle cx="17" cy="18.5" r="1.8"/><g class="a"><path d="M3 9.5h11.5v8H3z"/></g>`,
  flow: '<path d="M3 9c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0M3 15c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0"/>',
  temp: '<path d="M10 14.2V5.5a2 2 0 1 1 4 0v8.7a4 4 0 1 1-4 0z"/><path d="M12 9.5v7"/><g class="a"><circle cx="12" cy="17.5" r="2.6"/></g>',
  sun: '<circle cx="12" cy="12" r="3.8"/><path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.4 1.4M16.6 16.6 18 18M18 6l-1.4 1.4M7.4 16.6 6 18"/><g class="a"><circle cx="12" cy="12" r="3.8"/></g>',
  moon: '<path d="M19.5 14.6A8 8 0 1 1 9.4 4.5a6.4 6.4 0 0 0 10.1 10.1z"/><g class="a"><path d="M19.5 14.6A8 8 0 1 1 9.4 4.5a6.4 6.4 0 0 0 10.1 10.1z"/></g>',
  forecast: '<path d="M7.2 18.5a4 4 0 0 1-.6-7.9 5.6 5.6 0 0 1 10.8 1.3 3.3 3.3 0 0 1-.4 6.6z"/><g class="a"><path d="M7.2 18.5a4 4 0 0 1-.6-7.9 5.6 5.6 0 0 1 10.8 1.3 3.3 3.3 0 0 1-.4 6.6z"/></g>',
  advisory: '<path d="M12 3.8 21.2 19.5H2.8z"/><path d="M12 10v4.2"/><circle cx="12" cy="16.9" r=".9" fill="currentColor" stroke="none"/><g class="a"><path d="M12 3.8 21.2 19.5H2.8z"/></g>',
  star: '<path d="M12 3.8l2.5 5.2 5.7.8-4.1 4 1 5.7-5.1-2.7-5.1 2.7 1-5.7-4.1-4 5.7-.8z"/>',
  trend_up: '<path d="M5 15l5-5 3.5 3.5L19 8M14.5 8H19v4.5"/>',
  trend_down: '<path d="M5 9l5 5 3.5-3.5L19 16M14.5 16H19v-4.5"/>',
  trend_steady: '<path d="M5 12h14M15 8l4 4-4 4"/>'
};

/** Brand mark: a steelhead leaping over two lines of water. 32x32. */
export const mark =
  `<g transform="translate(16.5 11.5) rotate(-26) scale(.95) translate(-12 -12)"><path d="${FISH}"/><g class="a"><path d="${FISH}"/></g></g>` +
  '<path d="M3.5 25c3-2.8 6-2.8 9 0s6 2.8 9 0c1.8-1.7 3.6-2.2 5.5-1.4"/>';

// ---- Map markers: 40x40 art for the basemap. c = {main, ring, bg, accent} ----
export const markers = {
  stocking: (c) => `<circle cx="20" cy="20" r="14" fill="${c.main}" opacity=".22"/><circle cx="20" cy="20" r="9" fill="${c.main}" stroke="${c.bg}" stroke-width="2.5"/>`,
  stocking_scheduled: (c) => `<circle cx="20" cy="20" r="9" fill="none" stroke="${c.main}" stroke-width="2.5"/><circle cx="20" cy="20" r="2.2" fill="${c.main}"/>`,
  selected: (c) => `<circle cx="20" cy="20" r="17" fill="${c.accent}" opacity=".2"/><circle cx="20" cy="20" r="13" fill="none" stroke="${c.accent}" stroke-width="2.5"/><circle cx="20" cy="20" r="8" fill="${c.main}" stroke="${c.bg}" stroke-width="2.5"/>`,
  gauge: (c) => `<path d="M20 3 37 20 20 37 3 20z" fill="${c.main}" stroke="${c.bg}" stroke-width="3" stroke-linejoin="round"/><path d="M20 10.5c4.2 5.4 6.8 8.4 6.8 11.9a6.8 6.8 0 0 1-13.6 0c0-3.5 2.6-6.5 6.8-11.9z" fill="${c.bg}"/>`,
  advisory: (c) => `<circle cx="20" cy="20" r="14" fill="${c.accent}" opacity=".15"/><circle cx="20" cy="20" r="12" fill="none" stroke="${c.accent}" stroke-width="3"/><path d="M20 13.5v8" stroke="${c.accent}" stroke-width="3" stroke-linecap="round"/><circle cx="20" cy="26.2" r="1.8" fill="${c.accent}"/>`,
  report: (c, pips) => `<rect x="4" y="4" width="32" height="32" rx="10" fill="${c.bg}" stroke="${c.main}" stroke-width="2"/><g transform="translate(8.5 6.5) scale(.96)" fill="none" stroke="${c.main}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="${FISH}"/></g>` +
    [0, 1, 2, 3].map((i) => `<circle cx="${12.5 + i * 5}" cy="29.5" r="1.7" fill="${i < pips ? c.main : c.ring}"/>`).join(''),
  journal: (c) => `<path d="M20 36s-10-8.4-10-16.4a10 10 0 1 1 20 0C30 27.6 20 36 20 36z" fill="${c.main}" stroke="${c.bg}" stroke-width="2.5"/><circle cx="20" cy="19.5" r="4" fill="${c.bg}"/>`
};
