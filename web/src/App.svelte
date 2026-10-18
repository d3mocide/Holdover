<script>
  import { api, isoDay } from './lib/api.js';
  import Icon from './lib/Icon.svelte';
  import Logo from './lib/Logo.svelte';
  import MapView from './lib/MapView.svelte';
  import Planner from './lib/Planner.svelte';
  import Sheet from './lib/Sheet.svelte';
  import Settings from './lib/Settings.svelte';
  import Gauges from './lib/Gauges.svelte';
  import Legend from './lib/Legend.svelte';
  import DayView from './lib/DayView.svelte';
  import Journal from './lib/Journal.svelte';
  import LogTrip from './lib/LogTrip.svelte';
  import Offline from './lib/Offline.svelte';
  import { liveQuery } from 'dexie';
  import { db, metaGet, metaSet } from './lib/db.js';
  import { startSync, syncState } from './lib/sync.svelte.js';
  import { getToken } from './lib/api.js';

  const stored = (k, d) => { try { return localStorage.getItem(k) || d; } catch { return d; } };
  let theme = $state(stored('holdover.theme', 'fir'));
  let view = $state('map');
  // The side panel sizes to its content: roomy for lists with detail, compact for the map list.
  const PANEL = { map: 'min(380px, 40vw)', plan: 'min(520px, 44vw)', journal: 'min(460px, 42vw)', gauges: 'min(660px, 52vw)', settings: 'min(520px, 44vw)' };
  let panelW = $state(380);
  let wide = $state(typeof innerWidth === 'number' ? innerWidth >= 900 : true);
  $effect(() => { const f = () => (wide = innerWidth >= 900); addEventListener('resize', f); return () => removeEventListener('resize', f); });
  let data = $state(null);
  let report = $state(null);
  let error = $state('');
  let selectedId = $state(null);
  let showStocking = $state(true);
  let showGauges = $state(true);
  let showAdvisories = $state(true);
  let showReports = $state(true);
  let dayFor = $state(null);
  let offset = $state(0);
  let fishery = $state('trout');
  let spots = $state(null);
  let spotsError = $state('');
  let showJournal = $state(true);
  let layersOpen = $state(false);
  let legendOpen = $state(false);
  let wbList = $state([]);
  let logFor = $state(undefined); // undefined: closed, null: open without a waterbody, number: preset
  let offlineFor = $state(undefined);
  let journalGeo = $state(null);

  $effect(() => {
    api.waterbodyList().then(async (l) => { wbList = l; await metaSet('wbList', l); }).catch(async () => { wbList = await metaGet('wbList', []); });
    startSync();
  });
  $effect(() => {
    const sub = liveQuery(async () => {
      const [pins, trips] = await Promise.all([db.pins.toArray(), db.trips.toArray()]);
      return { pins, trips };
    }).subscribe(({ pins, trips }) => {
      const feats = pins.filter((p) => !p.deleted).map((p) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [p.lon, p.lat] }, properties: { label: p.label || 'My pin' } }));
      for (const t of trips.filter((t) => !t.deleted && t.lat != null && t.lon != null))
        feats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: [t.lon, t.lat] }, properties: { label: `Trip ${t.started_at?.slice(0, 10) ?? ''}` } });
      journalGeo = { type: 'FeatureCollection', features: feats };
    });
    return () => sub.unsubscribe();
  });

  $effect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('holdover.theme', theme); } catch { /* storage blocked */ }
  });

  async function load() {
    try { data = await api.map(); error = ''; } catch (e) { error = e.message; }
  }
  $effect(() => {
    const o = offset, f = fishery;
    spotsError = '';
    api.spots(isoDay(o), f).then((v) => (spots = v)).catch((e) => (spotsError = e.message));
  });
  async function loadReport() { try { report = await api.report(); } catch { /* keep last */ } }
  $effect(() => { load(); loadReport(); });

  const tabs = [['map', 'Map', 'map'], ['plan', 'Plan', 'plan'], ['journal', 'Journal', 'journal'], ['gauges', 'Gauges', 'gauge']];
  const select = (id) => { selectedId = id; dayFor = null; if (view !== 'map') view = 'map'; };
</script>

<div class="shell" style:--panel-w={PANEL[view] ?? PANEL.map}>
  <nav class="rail" aria-label="Main">
    <span class="logo"><Logo /></span>
    {#each tabs as [k, label, icon]}
      <button class="navbtn" aria-current={view === k ? 'page' : undefined} onclick={() => (view = k)} aria-label={label}>
        <Icon name={icon} /><span class="lbl">{label}</span>
      </button>
    {/each}
    <span class="spacer"></span>
    <button class="navbtn" aria-current={view === 'settings' ? 'page' : undefined} onclick={() => (view = 'settings')} aria-label="Settings">
      <Icon name="settings" /><span class="lbl">Settings</span>
    </button>
  </nav>

  <main class="planner" bind:clientWidth={panelW} class:full={view === 'plan'} class:tall={view !== 'map' && view !== 'plan'}>
    {#if view === 'map' || view === 'plan'}
      <Planner {data} {report} {spots} {spotsError} {offset} {fishery} onoffset={(o) => (offset = o)} onfishery={(f) => (fishery = f)} {error} {selectedId} onselect={select} canReview={!!getToken()} onreview={() => (view = 'settings')} />
    {:else if view === 'settings'}
      <Settings {theme} onTheme={(t) => (theme = t)} onChanged={() => { load(); loadReport(); api.spots(isoDay(offset), fishery).then((v) => (spots = v)).catch(() => {}); }} />
    {:else if view === 'journal'}
      <Journal {wbList} onlog={() => (logFor = null)} />
    {:else}
      <Gauges />
    {/if}
  </main>
  <div class="mapwrap" class:hide={view === 'plan'} class:tall={view !== 'map' && view !== 'plan'} class:sheet={selectedId && !dayFor && view === 'map'} class:wide={!!dayFor && view === 'map'}>
      <MapView inset={wide ? panelW + 112 : 0} {data} journal={journalGeo} {showJournal} {selectedId} {theme} {showStocking} {showGauges} {showAdvisories} {showReports} onselect={select} />
      <div class="layers glass" role="group" aria-label="Map layers">
        <button class="pill" aria-expanded={layersOpen} onclick={() => (layersOpen = !layersOpen)}><Icon name="layers" /> Layers</button>
        {#if layersOpen}
          <label class="lyr"><input type="checkbox" bind:checked={showStocking} /> Stocking</label>
          <label class="lyr"><input type="checkbox" bind:checked={showReports} /> Report ratings</label>
          <label class="lyr"><input type="checkbox" bind:checked={showGauges} /> Gauges</label>
          <label class="lyr"><input type="checkbox" bind:checked={showJournal} /> My pins &amp; trips</label>
          <label class="lyr"><input type="checkbox" bind:checked={showAdvisories} /> Advisories</label>
        {/if}
      </div>
      <div class="legend glass" aria-label="Map legend">
        <button class="pill" aria-expanded={legendOpen} onclick={() => (legendOpen = !legendOpen)}><Icon name="legend" /> Legend</button>
        {#if legendOpen}<Legend {theme} />
        {/if}
      </div>
      <button class="offline" onclick={() => (offlineFor = selectedId)}><Icon name="offline" size={18} /> Prepare for offline</button>
  </div>
    {#if dayFor && view === 'map'}
      <div class="sheetwrap wide"><DayView id={dayFor} {fishery} startOffset={offset} onback={() => (dayFor = null)} onlog={(id) => (logFor = id)} onoffline={(id) => (offlineFor = id)} /></div>
    {:else if selectedId && view === 'map'}
      <div class="sheetwrap"><Sheet id={selectedId} onclose={() => (selectedId = null)} onday={(id) => (dayFor = id)} onlog={(id) => (logFor = id)} /></div>
    {/if}

  {#if logFor !== undefined}
    <div class="overlay"><LogTrip {wbList} initialWb={logFor} onclose={() => (logFor = undefined)} onsaved={() => { logFor = undefined; view = 'journal'; }} /></div>
  {/if}
  {#if offlineFor !== undefined}<Offline wbId={offlineFor} onclose={() => (offlineFor = undefined)} />{/if}
</div>

<style>
  .shell { position: relative; height: 100%; display: grid; grid-template-columns: 64px var(--panel-w, 380px) 1fr; grid-template-rows: 100%; gap: 16px; padding: 16px; transition: grid-template-columns 0.25s ease; }
  .shell > :global(*) { grid-row: 1; }
  .rail, .offline { background: var(--glass); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); border: 1px solid var(--glass-line); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
  .planner, .sheetwrap, .layers, .legend { background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense); border: 1px solid var(--glass-line); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
  .rail { grid-column: 1; z-index: 3; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 0; }
  .logo { margin-bottom: 12px; }
  .navbtn { flex-direction: column; border: 0; background: none; width: 56px; height: 56px; gap: 2px; border-radius: 12px; color: var(--text-quiet); padding: 0; }
  .navbtn[aria-current='page'] { background: var(--glass-fill); color: var(--fresh-1); box-shadow: inset 0 0 0 1px var(--glass-line), 0 0 18px var(--glow-1); }
  .lbl { font-size: 10px; }
  .spacer { flex: 1; }
  .planner { grid-column: 2; z-index: 3; border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
  .mapwrap { position: absolute; inset: 0; min-width: 0; z-index: 0; grid-column: 1 / -1; }
  .sheetwrap { position: absolute; top: 16px; right: 16px; bottom: 16px; width: 340px; border-radius: 20px; overflow: hidden; z-index: 5; }
  .mapwrap { --sheet-inset: 0px; }
  .mapwrap.sheet { --sheet-inset: 356px; }
  .mapwrap.wide { --sheet-inset: calc(min(520px, 60%) + 16px); }
  .mapwrap :global(.maplibregl-ctrl-top-right) { right: var(--sheet-inset); top: 16px; transition: right 0.25s ease; }
  .mapwrap :global(.maplibregl-ctrl-top-right .maplibregl-ctrl) { margin: 0 16px 0 0; }
  .layers { position: absolute; top: 16px; right: calc(76px + var(--sheet-inset)); padding: 6px; z-index: 2; border-radius: 14px; display: flex; flex-direction: column; transition: right 0.25s ease; }
  .layers .lyr { padding: 0 14px; gap: 12px; }
  .pill { border: 0; background: none; min-height: 44px; padding: 0 14px; font-size: 13px; gap: 10px; justify-content: flex-start; min-height: 44px; }
  .lyr { display: flex; align-items: center; gap: 8px; min-height: 36px; margin: 0; color: var(--text); font-size: 13px; }
  .lyr.off { color: var(--text-quiet); }
  .lyr input { width: 18px; height: 18px; accent-color: var(--accent); }
  .soon { font-size: 11px; }
  .legend { position: absolute; left: calc(112px + var(--panel-w, 380px)); transition: left 0.25s ease; bottom: 16px; border-radius: 14px; display: flex; padding: 6px; z-index: 2; flex-direction: column; align-items: flex-start; }
  .sm { font-size: 11px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .overlay { position: absolute; inset: 0; z-index: 15; background: var(--page-bg); overflow: hidden; }
  .sym { width: 10px; height: 10px; display: inline-block; border: 2px solid var(--text-quiet); }
  .sym.diamond { background: var(--gauge); border-color: var(--bg); box-shadow: 0 0 0 1px var(--gauge); }
  .sym.diamond { transform: rotate(45deg); }
  .sym.ring { border-radius: 50%; border-color: var(--accent); }
  .sheetwrap.wide { width: min(520px, 60%); }
  .offline { position: absolute; left: calc(112px + var(--panel-w, 380px)); transition: left 0.25s ease; top: 16px; z-index: 2; color: var(--text); gap: 10px; padding: 0 20px; }

  @media (max-width: 899px) {
    .shell { --nav-h: calc(64px + env(safe-area-inset-bottom, 0px)); grid-template-columns: 1fr; grid-template-rows: 1fr var(--nav-h); gap: 0; padding: 0; }
    .rail { grid-row: 2; grid-column: 1; flex-direction: row; justify-content: space-around; border-radius: 0; border-width: 1px 0 0; padding: 0 4px env(safe-area-inset-bottom, 0px); order: 9; gap: 0; }
    .logo, .spacer { display: none; }
    .navbtn { flex: 1; width: auto; height: 100%; }
    .shell > :global(*) { grid-column: 1; grid-row: 1; }
    .shell > .rail { grid-row: 2; }
    .planner { grid-column: 1; z-index: 3; align-self: end; height: 42%; border-radius: 20px 20px 0 0; }
    .planner.full { height: 100%; border-radius: 0; }
    .planner.tall { height: 68%; }
    .mapwrap.tall .legend { bottom: calc(68% + 16px); }
    .mapwrap.hide { display: none; }
    .sheetwrap, .sheetwrap.wide { width: 100%; top: auto; right: 0; bottom: var(--nav-h); height: calc(62% - var(--nav-h)); z-index: 6; border-radius: 20px 20px 0 0; background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; }
    .planner { background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; }
    .mapwrap.sheet, .mapwrap.wide { --sheet-inset: 0px; }
    .mapwrap :global(.maplibregl-ctrl-top-right) { display: none; }
    .layers { right: 16px; top: calc(16px + var(--safe-top)); }
    .offline { top: calc(16px + var(--safe-top)); }
    .lyr.off { display: none; }
    .legend { left: 16px; bottom: calc(42% + 16px); }
    .offline { left: 16px; }
    .mapwrap { inset: 0 0 var(--nav-h) 0; grid-column: 1; }
  }
</style>
