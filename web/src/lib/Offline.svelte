<script>
  import { prepareTiles, tileList, cachedTileCount, clearTiles, basemapAvailable } from './tiles.js';
  import { loadDay } from './conditions.js';
  import { api, isoDay } from './api.js';
  let { wbId = null, onclose } = $props();
  let maxZ = $state(10);
  let progress = $state({ done: 0, total: 0 });
  let busy = $state(false);
  let msg = $state('');
  let have = $state(0);
  let basemap = $state(true);
  let ctl = null;
  const total = $derived(tileList(undefined, 6, maxZ).length);

  $effect(() => { cachedTileCount().then((n) => (have = n)); basemapAvailable().then((b) => (basemap = b)); });

  async function go() {
    busy = true; msg = ''; ctl = new AbortController();
    const parts = [];
    try {
      // data first (small), so a quota error on tiles can't cost us the conditions
      await Promise.all([api.map(), api.report(), api.gauges(), api.waterbodyList(), api.spots(isoDay(0), 'trout')]);
      if (wbId) { await loadDay(wbId, isoDay(0)); await loadDay(wbId, isoDay(1)).catch(() => {}); parts.push('conditions for the selected waterbody'); }
      parts.unshift('map data, report and gauges');
    } catch (e) { parts.push(`(data failed: ${e.message})`); }
    if (basemap) {
      const r = await prepareTiles({ minZ: 6, maxZ, signal: ctl.signal, onProgress: (done, t) => (progress = { done, total: t }) });
      parts.push(`${r.stored} new map tiles`);
      if (r.stopped) msg = `Map download stopped: ${r.stopped}. What was saved still works offline.`;
    } else msg = 'No basemap installed on the server, so there are no map tiles to save.';
    have = await cachedTileCount();
    if (!msg) msg = `Saved ${parts.join(', ')}.`; else msg = `Saved ${parts.join(', ')}. ${msg}`;
    busy = false;
  }
  async function clear() { await clearTiles(); have = 0; msg = 'Offline map tiles cleared.'; }
</script>

<dialog open aria-label="Prepare for offline">
  <h2>Prepare for offline</h2>
  <p class="quiet">Saves the map for the Willamette zone, today's data and the selected waterbody's conditions on this device. The app itself is already cached.</p>
  {#if basemap}
    <label for="mz">Map detail</label>
    <select id="mz" bind:value={maxZ} disabled={busy}>
      <option value={8}>Overview (zoom 8, small)</option>
      <option value={10}>Regional (zoom 10)</option>
      <option value={11}>Detailed (zoom 11, larger)</option>
      <option value={12}>Very detailed (zoom 12, large)</option>
    </select>
    <p class="quiet small mono">{total.toLocaleString()} tiles · {have.toLocaleString()} saved now</p>
  {/if}
  {#if busy}<progress max={progress.total || 1} value={progress.done} aria-label="Download progress"></progress>{/if}
  {#if msg}<p role="status">{msg}</p>{/if}
  <div class="row">
    <button class="primary" onclick={go} disabled={busy}>{busy ? 'Saving…' : 'Save for offline'}</button>
    {#if busy}<button onclick={() => ctl?.abort()}>Stop</button>{/if}
    {#if have}<button onclick={clear} disabled={busy}>Clear saved map</button>{/if}
    <button onclick={onclose}>Close</button>
  </div>
</dialog>

<style>
  dialog { position: fixed; inset: 0; margin: auto; z-index: 20; background: var(--surface); color: var(--text); border: 1px solid var(--line); border-radius: 16px; max-width: 440px; width: calc(100% - 32px); padding: 16px; display: flex; flex-direction: column; gap: 8px; }
  h2 { font-size: 18px; } .small { font-size: 13px; margin: 0; } .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
  progress { width: 100%; accent-color: var(--accent); }
</style>
