<script>
  import { onMount } from 'svelte';
  import * as maplibregl from 'maplibre-gl';
  import { Protocol } from 'pmtiles';
  import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';

  // Bundlers don't emit MapLibre's worker on their own, so ship it as a hashed asset (precached by the PWA).
  maplibregl.setWorkerUrl(workerUrl);

  let { data, selectedId = null, theme, onselect, showStocking = true } = $props();
  let el;
  let map;
  let ready = $state(false);
  let hasBasemap = $state(false);

  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  function palette() {
    return {
      land: css('--land'), water: css('--water'), river: css('--river'), line: css('--line'),
      f1: css('--fresh-1'), f2: css('--fresh-2'), f3: css('--fresh-3'), accent: css('--accent'), bg: css('--bg')
    };
  }

  function baseStyle(withTiles) {
    const c = palette();
    const style = { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': c.land } }] };
    if (withTiles) {
      style.sources.oregon = { type: 'vector', url: 'pmtiles:///tiles/oregon.pmtiles' };
      style.layers.push(
        { id: 'water', type: 'fill', source: 'oregon', 'source-layer': 'water', paint: { 'fill-color': c.water } },
        { id: 'waterway', type: 'line', source: 'oregon', 'source-layer': 'water', filter: ['==', '$type', 'LineString'],
          paint: { 'line-color': c.river, 'line-width': 1 } },
        { id: 'roads', type: 'line', source: 'oregon', 'source-layer': 'roads',
          paint: { 'line-color': c.line, 'line-width': 0.8 } }
      );
    }
    return style;
  }

  function freshnessPaint() {
    const c = palette();
    return {
      color: ['match', ['get', 'freshness'], 'this_week', c.f1, 'recent', c.f2, 'older', c.f3, 'upcoming', c.bg, c.f3],
      stroke: ['match', ['get', 'freshness'], 'upcoming', c.f1, c.bg]
    };
  }

  function addLayers() {
    const p = freshnessPaint();
    const c = palette();
    map.addSource('stocking', { type: 'geojson', data: data ?? { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'stocking-pts', type: 'circle', source: 'stocking', paint: {
      'circle-radius': 8, 'circle-color': p.color, 'circle-stroke-color': p.stroke, 'circle-stroke-width': 2 } });
    map.addLayer({ id: 'stocking-sel', type: 'circle', source: 'stocking', filter: ['==', ['get', 'id'], -1], paint: {
      'circle-radius': 12, 'circle-color': p.color, 'circle-stroke-color': c.accent, 'circle-stroke-width': 3 } });
    map.on('click', 'stocking-pts', (e) => onselect?.(e.features[0].properties.id));
    map.on('mouseenter', 'stocking-pts', () => (map.getCanvas().style.cursor = 'pointer'));
    map.on('mouseleave', 'stocking-pts', () => (map.getCanvas().style.cursor = ''));
  }

  onMount(() => {
    maplibregl.addProtocol('pmtiles', new Protocol().tile);
    let dead = false;
    (async () => {
      // The basemap is optional: with no PMTiles file the map still renders pins on a themed ground.
      let withTiles = false;
      try { withTiles = (await fetch('/tiles/oregon.pmtiles', { method: 'HEAD' })).ok; } catch { /* offline */ }
      if (dead) return;
      hasBasemap = withTiles;
      map = new maplibregl.Map({
        container: el, style: baseStyle(withTiles), center: [-122.9, 44.6], zoom: 7.4,
        attributionControl: { compact: true }, maxBounds: [[-125.5, 41.5], [-116, 47]]
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      map.on('load', () => { addLayers(); ready = true; });
    })();
    return () => { dead = true; map?.remove(); };
  });

  let fitted = false;
  $effect(() => {
    if (!ready || !data) return;
    map.getSource('stocking').setData(data);
    if (!fitted && data.features.length) {
      fitted = true;
      const b = new maplibregl.LngLatBounds();
      data.features.forEach((f) => b.extend(f.geometry.coordinates));
      map.fitBounds(b, { padding: 60, maxZoom: 9, duration: 0 });
    }
  });
  $effect(() => {
    if (!ready) return;
    map.setLayoutProperty('stocking-pts', 'visibility', showStocking ? 'visible' : 'none');
    map.setLayoutProperty('stocking-sel', 'visibility', showStocking ? 'visible' : 'none');
  });
  $effect(() => {
    if (!ready) return;
    map.setFilter('stocking-sel', ['==', ['get', 'id'], selectedId ?? -1]);
    const f = data?.features.find((x) => x.properties.id === selectedId);
    if (f) map.easeTo({ center: f.geometry.coordinates, zoom: Math.max(map.getZoom(), 10), duration: 400 });
  });
  $effect(() => {
    theme; // re-read CSS variables when the theme changes
    if (!ready) return;
    queueMicrotask(() => {
      const c = palette(); const p = freshnessPaint();
      map.setPaintProperty('bg', 'background-color', c.land);
      if (hasBasemap) {
        map.setPaintProperty('water', 'fill-color', c.water);
        map.setPaintProperty('waterway', 'line-color', c.river);
        map.setPaintProperty('roads', 'line-color', c.line);
      }
      map.setPaintProperty('stocking-pts', 'circle-color', p.color);
      map.setPaintProperty('stocking-pts', 'circle-stroke-color', p.stroke);
      map.setPaintProperty('stocking-sel', 'circle-color', p.color);
      map.setPaintProperty('stocking-sel', 'circle-stroke-color', c.accent);
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
