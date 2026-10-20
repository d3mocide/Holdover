// Regenerate the brand review atlas: node scripts/render-icon-atlas.mjs
// Uses the same optional Playwright install as tests/e2e; no production dependency.
import { chromium } from 'playwright-core';
import { icons, mark, markers } from '../web/src/lib/icons.js';
import fs from 'node:fs/promises';
const theme = await fs.readFile('web/src/theme.css', 'utf8');
const svg = (art, size, grid = 24) => `<svg width="${size}" height="${size}" viewBox="0 0 ${grid} ${grid}" fill="none" stroke="${grid === 40 ? 'none' : 'currentColor'}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${art}</svg>`;
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1500 }, deviceScaleFactor: 1 });
  await page.setContent(`<html data-theme="fir"><head><style>${theme}
    body { height: auto; padding: 32px; } h1 { font-size: 28px; } h2 { margin: 28px 0 16px; font-size: 14px; letter-spacing: .08em; text-transform: uppercase; color: var(--text-quiet); }
    p { color: var(--text-quiet); } .grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; } .tile { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 16px; }
    .row { display: flex; align-items: center; gap: 12px; height: 52px; } .a { fill: currentColor; fill-opacity: .3; stroke: none; } .large { color: var(--fresh-1); } .label { margin-top: 12px; font-size: 13px; color: var(--text-quiet); }
    .markers .row { justify-content: center; height: 68px; } .markers .label { text-align: center; }
  </style></head><body><h1>Holdover icon atlas</h1><p>24 px UI grid · round caps · duotone accent. Map symbols share a compact footprint and shape carries meaning.</p><h2>Navigation, actions & subjects</h2><div class="grid">${Object.entries(icons).map(([name, art]) => `<div class="tile"><div class="row">${svg(art, 20)}${svg(art, 28)}<span class="large">${svg(art, 44)}</span></div><div class="label">${name}</div></div>`).join('')}</div><h2>Brand mark</h2>${svg(mark, 64, 32)}<h2>Map markers · enlarged for review (map: about 23 px; reports: 26 px)</h2><div class="grid markers" id="markers"></div></body></html>`);
  // Read colours from the actual theme tokens.
  const c = await page.evaluate(() => Object.fromEntries(['bg', 'accent', 'fresh-1', 'fresh-2', 'fresh-3', 'gauge', 'text', 'warn', 'alert'].map((name) => [name, getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim()])));
  const marker = (name, color, n) => markers[name]({ main: c[color], bg: c.bg, accent: c.accent, ring: c['fresh-3'] }, n);
  const cells = [
    ['This week', marker('stocking', 'fresh-1')], ['Last 2 weeks', marker('stocking_recent', 'fresh-2')], ['Older', marker('stocking_older', 'fresh-3')], ['Scheduled', marker('stocking_scheduled', 'fresh-1')], ['Selected', marker('selected', 'fresh-1')], ['River', marker('river', 'gauge')],
    ['Stream gauge', marker('gauge', 'gauge')], ['Advisory', marker('advisory', 'alert')], ['My trip', marker('journal', 'text')], ['Home', marker('home', 'accent')],
    ...[['excellent', 'fresh-1', 4], ['good', 'fresh-2', 3], ['fair', 'warn', 2], ['slow', 'fresh-3', 1], ['unknown', 'fresh-3', 0]].map(([name, color, n]) => [`Report: ${name}`, marker('report', color, n)])
  ];
  await page.locator('#markers').evaluate((el, body) => { el.innerHTML = body; }, cells.map(([label, art]) => `<div class="tile"><div class="row">${svg(art, 64, 40)}</div><div class="label">${label}</div></div>`).join(''));
  await page.screenshot({ path: 'docs/brand/icon-atlas.png', fullPage: true });
  console.log('Wrote docs/brand/icon-atlas.png');
} finally { await browser.close(); }
