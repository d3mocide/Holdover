<script module>
  let protocolDone = false; // addProtocol is global: register once per page load
</script>

<script>
  import { onMount } from 'svelte';
  import * as maplibregl from 'maplibre-gl';
  import { registerTileProtocol, basemapAvailable } from './tiles.js';
  import { markers } from './icons.js';
  import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';

  // Bundlers don't emit MapLibre's worker on their own, so ship it as a hashed asset (precached by the PWA).
  maplibregl.setWorkerUrl(workerUrl);

  let { journal = null, showJournal = true, data, selectedId = null, theme, onselect, showStocking = true, showGauges = true, showAdvisories = true, showReports = true } = $props();
  let el;
  let map;
  let ready = $state(false);
  let hasBasemap = $state(false);

  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  function palette() {
    return {
      land: css('--land'), forest: css('--forest'), water: css('--water'), river: css('--river'), shore: css('--shore'), line: css('--road'), minor: css('--road-minor'), gauge: css('--gauge'), warn: css('--warn'),
      f1: css('--fresh-1'), f2: css('--fresh-2'), f3: css('--fresh-3'), accent: css('--accent'), bg: css('--bg')
    };
  }

  function baseStyle(withTiles) {
    const c = palette();
    const style = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': c.land } }] };
    if (withTiles) {
      style.sources.oregon = { type: 'vector', tiles: ['holdover://{z}/{x}/{y}'], minzoom: 0, maxzoom: 14 };
      style.layers.push(
        { id: 'landuse', type: 'fill', source: 'oregon', 'source-layer': 'landuse',
          filter: ['in', ['get', 'kind'], ['literal', ['park', 'forest', 'wood', 'national_park', 'nature_reserve', 'protected_area']]],
          paint: { 'fill-color': c.forest, 'fill-opacity': 0.7 } },
        { id: 'natural', type: 'fill', source: 'oregon', 'source-layer': 'natural',
          filter: ['in', ['get', 'kind'], ['literal', ['forest', 'wood']]], paint: { 'fill-color': c.forest, 'fill-opacity': 0.7 } },
        { id: 'water', type: 'fill', source: 'oregon', 'source-layer': 'water', paint: { 'fill-color': c.water } },
        { id: 'water-edge', type: 'line', source: 'oregon', 'source-layer': 'water', filter: ['==', '$type', 'Polygon'],
          layout: { 'line-join': 'round' },
          paint: { 'line-color': c.shore, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.6, 12, 1.4], 'line-opacity': 0.55, 'line-blur': 0.6 } },
        { id: 'waterway', type: 'line', source: 'oregon', 'source-layer': 'water', filter: ['==', '$type', 'LineString'],
          paint: { 'line-color': c.river, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.4, 10, 0.8, 13, 1.8], 'line-opacity': ['interpolate', ['linear'], ['zoom'], 7, 0.25, 12, 0.6] } },
        { id: 'roads-minor', type: 'line', source: 'oregon', 'source-layer': 'roads', minzoom: 10,
          filter: ['!', ['in', ['get', 'kind'], ['literal', ['highway', 'major_road']]]],
          paint: { 'line-color': c.minor, 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.4, 14, 1.2] } },
        { id: 'roads', type: 'line', source: 'oregon', 'source-layer': 'roads',
          filter: ['in', ['get', 'kind'], ['literal', ['highway', 'major_road']]],
          paint: { 'line-color': c.line, 'line-width': ['interpolate', ['linear'], ['zoom'], 6, 0.5, 10, 1, 14, 2.2] } }
      );
    }
    return style;
  }

  function freshnessPaint() {
    const c = palette();
    return {
      color: ['match', ['get', 'freshness'], 'this_week', c.f1, 'recent', c.f2, 'older', c.f3, 'upcoming', c.bg, c.f3],
      stroke: ['match', ['get', 'freshness'], 'upcoming', c.f1, c.bg],
      halo: ['match', ['get', 'freshness'], 'this_week', c.f1, 'recent', c.f2, 'older', c.f3, c.f1]
    };
  }

  // Marker art lives in icons.js as SVG; rasterise at 2x so it stays sharp on phones.
  function svgImage(inner, size = 40) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const cv = document.createElement('canvas'); cv.width = cv.height = size * 2;
        const g = cv.getContext('2d'); g.drawImage(img, 0, 0, size * 2, size * 2);
        resolve(g.getImageData(0, 0, size * 2, size * 2));
      };
      img.onerror = reject;
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="${size * 2}" height="${size * 2}" viewBox="0 0 40 40">${inner}</svg>`);
    });
  }
  async function addIcons() {
    const c = palette();
    const base = { ring: 'rgba(255,255,255,0.18)', bg: c.bg, accent: c.accent };
    const defs = {
      'gauge-icon': markers.gauge({ ...base, main: c.gauge }),
      'advisory-icon': markers.advisory({ ...base, main: c.accent }),
      'journal-icon': markers.journal({ ...base, main: css('--text') }),
      ...Object.fromEntries([['excellent', c.f1, 4], ['good', c.f2, 3], ['fair', c.warn, 2], ['slow', c.f3, 1], ['unknown', c.f3, 0]]
        .map(([k, col, n]) => [`report-${k}`, markers.report({ ...base, main: col }, n)]))
    };
    const imgs = await Promise.all(Object.entries(defs).map(async ([n, inner]) => [n, await svgImage(inner)]));
    for (const [name, img] of imgs) {
      if (map.hasImage(name)) map.removeImage(name);
      map.addImage(name, img, { pixelRatio: 2 });
    }
  }

  const isL = (l) => ['==', ['get', 'layer'], l];
  const selFilter = (id) => ['all', isL('stocking'), ['==', ['get', 'id'], id]];

  async function addLayers() {
    await addIcons();
    const p = freshnessPaint();
    const c = palette();
    map.addSource('stocking', { type: 'geojson', data: data ?? { type: 'FeatureCollection', features: [] } });
    map.addSource('journal', { type: 'geojson', data: journal ?? { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'journal-pts', type: 'symbol', source: 'journal', layout: {
      'icon-image': 'journal-icon', 'icon-size': 0.6, 'icon-anchor': 'bottom', 'icon-allow-overlap': true } });
    map.addLayer({ id: 'advisory-ring', type: 'symbol', source: 'stocking', filter: isL('advisory'), layout: {
      'icon-image': 'advisory-icon', 'icon-size': 0.9, 'icon-allow-overlap': true } });
    map.addLayer({ id: 'report-badge', type: 'symbol', source: 'stocking', filter: isL('report'), layout: {
      'icon-image': ['concat', 'report-', ['coalesce', ['get', 'rating'], 'unknown']], 'icon-size': 0.52, 'icon-offset': [20, -20], 'icon-allow-overlap': true } });
    const fishN = ['coalesce', ['get', 'last_total'], ['get', 'next_total'], 0];
    const rad = ['interpolate', ['linear'], ['sqrt', fishN], 0, 6, 30, 8, 60, 11, 100, 14];
    map.addLayer({ id: 'stocking-halo', type: 'circle', source: 'stocking', filter: isL('stocking'), paint: {
      'circle-radius': ['+', rad, 7], 'circle-color': p.halo, 'circle-opacity': ['match', ['get', 'freshness'], 'upcoming', 0, 'older', 0.1, 0.24], 'circle-blur': 0.9 } });
    map.addLayer({ id: 'stocking-pts', type: 'circle', source: 'stocking', filter: isL('stocking'), paint: {
      'circle-radius': rad, 'circle-color': p.color, 'circle-stroke-color': p.stroke, 'circle-stroke-width': 2.5 } });
    map.addLayer({ id: 'gauge-pts', type: 'symbol', source: 'stocking', filter: isL('gauge'), layout: {
      'icon-image': 'gauge-icon', 'icon-size': 0.72, 'icon-allow-overlap': true } });
    map.addLayer({ id: 'stocking-sel-glow', type: 'circle', source: 'stocking', filter: selFilter(-1), paint: {
      'circle-radius': 26, 'circle-color': c.accent, 'circle-opacity': 0.22, 'circle-blur': 0.8 } });
    map.addLayer({ id: 'stocking-sel', type: 'circle', source: 'stocking', filter: selFilter(-1), paint: {
      'circle-radius': ['+', rad, 5], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': c.accent, 'circle-stroke-width': 2.5 } });
    for (const l of ['stocking-pts', 'advisory-ring', 'report-badge']) {
      map.on('click', l, (e) => onselect?.(e.features[0].properties.id));
    }
    map.on('click', 'journal-pts', (e) => {
      const p = e.features[0].properties;
      const el = document.createElement('div'); el.textContent = p.label; 
      new maplibregl.Popup({ offset: 8 }).setLngLat(e.lngLat).setDOMContent(el).addTo(map);
    });
    map.on('click', 'gauge-pts', (e) => {
      const p = e.features[0].properties;
      const el = document.createElement('div');
      const t = (txt, cls) => { const d = document.createElement('div'); d.textContent = txt; if (cls) d.className = cls; el.appendChild(d); };
      t(p.name); t(p.flow_cfs != null ? `${Math.round(p.flow_cfs).toLocaleString()} cfs${p.trend ? ' · ' + p.trend : ''}` : 'No flow data', 'mono');
      t(`USGS ${p.site_no} · provisional${p.stale === true || p.stale === 'true' ? ' · STALE' : ''}`);
      new maplibregl.Popup({ offset: 12 }).setLngLat(e.lngLat).setDOMContent(el).addTo(map);
    });
    for (const l of ['stocking-pts', 'gauge-pts', 'advisory-ring', 'report-badge']) {
      map.on('mouseenter', l, () => (map.getCanvas().style.cursor = 'pointer'));
      map.on('mouseleave', l, () => (map.getCanvas().style.cursor = ''));
    }
  }

  onMount(() => {
    if (!protocolDone) { registerTileProtocol(maplibregl); protocolDone = true; }
    let dead = false;
    (async () => {
      // The basemap is optional: with no PMTiles file the map still renders pins on a themed ground.
      let withTiles = false;
      withTiles = await basemapAvailable();
      if (dead) return;
      hasBasemap = withTiles;
      map = new maplibregl.Map({
        container: el, style: baseStyle(withTiles), center: [-122.9, 44.6], zoom: 7.4,
        attributionControl: { compact: true }, padding: { left: window.innerWidth >= 900 ? 492 : 0 }, maxBounds: [[-125.5, 41.5], [-116, 47]]
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      map.on('load', async () => { await addLayers(); ready = true; });
    })();
    return () => { dead = true; map?.remove(); };
  });

  $effect(() => { if (ready && journal) map.getSource('journal').setData(journal); });
  $effect(() => { if (ready) map.setLayoutProperty('journal-pts', 'visibility', showJournal ? 'visible' : 'none'); });
  let fitted = false;
  $effect(() => {
    if (!ready || !data) return;
    map.getSource('stocking').setData(data);
    if (!fitted && data.features.length) {
      fitted = true;
      const b = new maplibregl.LngLatBounds();
      data.features.filter((f) => f.properties.layer === 'stocking').forEach((f) => b.extend(f.geometry.coordinates));
      map.fitBounds(b, { padding: 60, maxZoom: 9, duration: 0 });
    }
  });
  $effect(() => {
    if (!ready) return;
    const vis = (on) => (on ? 'visible' : 'none');
    map.setLayoutProperty('stocking-pts', 'visibility', vis(showStocking));
    map.setLayoutProperty('stocking-sel', 'visibility', vis(showStocking));
    map.setLayoutProperty('stocking-halo', 'visibility', vis(showStocking));
    map.setLayoutProperty('stocking-sel-glow', 'visibility', vis(showStocking));
    map.setLayoutProperty('gauge-pts', 'visibility', vis(showGauges));
    map.setLayoutProperty('advisory-ring', 'visibility', vis(showAdvisories));
    map.setLayoutProperty('report-badge', 'visibility', vis(showReports));
  });
  $effect(() => {
    if (!ready) return;
    map.setFilter('stocking-sel', selFilter(selectedId ?? -1));
    map.setFilter('stocking-sel-glow', selFilter(selectedId ?? -1));
    const f = data?.features.find((x) => x.properties.layer === 'stocking' && x.properties.id === selectedId);
    if (f) map.easeTo({ center: f.geometry.coordinates, zoom: Math.max(map.getZoom(), 10), duration: 400 });
  });
  $effect(() => {
    theme; // re-read CSS variables when the theme changes
    if (!ready) return;
    queueMicrotask(() => {
      const c = palette(); const p = freshnessPaint();
      map.setPaintProperty('bg', 'background-color', c.land);
      if (hasBasemap) {
        map.setPaintProperty('landuse', 'fill-color', c.forest);
        map.setPaintProperty('natural', 'fill-color', c.forest);
        map.setPaintProperty('water', 'fill-color', c.water);
        map.setPaintProperty('waterway', 'line-color', c.river);
        map.setPaintProperty('water-edge', 'line-color', c.shore);
        map.setPaintProperty('roads', 'line-color', c.line);
        map.setPaintProperty('roads-minor', 'line-color', c.minor);
      }
      map.setPaintProperty('stocking-pts', 'circle-color', p.color);
      map.setPaintProperty('stocking-pts', 'circle-stroke-color', p.stroke);
      map.setPaintProperty('stocking-halo', 'circle-color', p.halo);
      map.setPaintProperty('stocking-sel', 'circle-stroke-color', c.accent);
      map.setPaintProperty('stocking-sel-glow', 'circle-color', c.accent);
      addIcons();
    });
  });
</script>

<div class="map" bind:this={el} role="application" aria-label="Map of stocked waterbodies. The Plan list has the same waterbodies as buttons."></div>
{#if ready && !hasBasemap}
  <p class="nobase quiet">No basemap installed: showing pins only. See docs/basemap.md.</p>
{/if}

<style>
  .map { position: absolute; inset: 0; }
  .nobase { position: absolute; left: 12px; bottom: 56px; margin: 0; font-size: 12px; background: var(--surface);
    border: 1px solid var(--line); border-radius: 8px; padding: 4px 8px; pointer-events: none; }
</style>
