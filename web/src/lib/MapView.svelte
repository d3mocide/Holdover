<script module>
  let protocolDone = false; // addProtocol is global: register once per page load
</script>

<script>
  import { onMount } from 'svelte';
  import * as maplibregl from 'maplibre-gl';
  import { registerTileProtocol, basemapAvailable } from './tiles.js';
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

  function icon(draw) {
    const cv = document.createElement('canvas'); cv.width = cv.height = 32;
    const g = cv.getContext('2d'); draw(g);
    return g.getImageData(0, 0, 32, 32);
  }
  function addIcons() {
    const c = palette();
    const stroke = css('--text');
    for (const [name, img] of Object.entries({
      'gauge-icon': icon((g) => { g.fillStyle = c.gauge; g.strokeStyle = c.bg; g.lineWidth = 3; g.beginPath();
        g.moveTo(16, 3); g.lineTo(29, 16); g.lineTo(16, 29); g.lineTo(3, 16); g.closePath(); g.fill(); g.stroke(); }),
      ...Object.fromEntries([['excellent', c.f1], ['good', c.f2], ['fair', c.warn], ['slow', c.f3], ['unknown', c.f3]].map(([k, col]) => [`report-${k}`,
        icon((g) => { g.fillStyle = c.bg; g.beginPath(); g.roundRect(4, 4, 24, 24, 7); g.fill();
          g.fillStyle = col; g.beginPath(); g.roundRect(8, 8, 16, 16, 4); g.fill(); })]))
    })) { if (map.hasImage(name)) map.removeImage(name); map.addImage(name, img); }
  }

  const isL = (l) => ['==', ['get', 'layer'], l];
  const selFilter = (id) => ['all', isL('stocking'), ['==', ['get', 'id'], id]];

  function addLayers() {
    addIcons();
    const p = freshnessPaint();
    const c = palette();
    map.addSource('stocking', { type: 'geojson', data: data ?? { type: 'FeatureCollection', features: [] } });
    map.addSource('journal', { type: 'geojson', data: journal ?? { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'journal-pts', type: 'circle', source: 'journal', paint: {
      'circle-radius': 5, 'circle-color': css('--text'), 'circle-stroke-color': c.bg, 'circle-stroke-width': 2, 'circle-opacity': 0.9 } });
    map.addLayer({ id: 'advisory-ring', type: 'circle', source: 'stocking', filter: isL('advisory'), paint: {
      'circle-radius': 15, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': c.accent, 'circle-stroke-width': 3 } });
    map.addLayer({ id: 'report-badge', type: 'symbol', source: 'stocking', filter: isL('report'), layout: {
      'icon-image': ['concat', 'report-', ['coalesce', ['get', 'rating'], 'unknown']], 'icon-size': 0.55, 'icon-offset': [18, -18], 'icon-allow-overlap': true } });
    const fishN = ['coalesce', ['get', 'last_total'], ['get', 'next_total'], 0];
    const rad = ['interpolate', ['linear'], ['sqrt', fishN], 0, 6, 30, 8, 60, 11, 100, 14];
    map.addLayer({ id: 'stocking-halo', type: 'circle', source: 'stocking', filter: isL('stocking'), paint: {
      'circle-radius': ['+', rad, 7], 'circle-color': p.halo, 'circle-opacity': ['match', ['get', 'freshness'], 'upcoming', 0, 'older', 0.1, 0.24], 'circle-blur': 0.9 } });
    map.addLayer({ id: 'stocking-pts', type: 'circle', source: 'stocking', filter: isL('stocking'), paint: {
      'circle-radius': rad, 'circle-color': p.color, 'circle-stroke-color': p.stroke, 'circle-stroke-width': 2.5 } });
    map.addLayer({ id: 'gauge-pts', type: 'symbol', source: 'stocking', filter: isL('gauge'), layout: {
      'icon-image': 'gauge-icon', 'icon-size': 0.75, 'icon-allow-overlap': true } });
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
        attributionControl: { compact: true }, padding: { left: window.innerWidth >= 900 ? 456 : 0 }, maxBounds: [[-125.5, 41.5], [-116, 47]]
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      map.on('load', () => { addLayers(); ready = true; });
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
      map.setPaintProperty('advisory-ring', 'circle-stroke-color', c.accent);
      map.setPaintProperty('journal-pts', 'circle-color', css('--text'));
      map.setPaintProperty('journal-pts', 'circle-stroke-color', c.bg);
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
