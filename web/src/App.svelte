<script>
  import { api, isoDay } from './lib/api.js';
  import Icon from './lib/Icon.svelte';
  import Logo from './lib/Logo.svelte';
  import MapView from './lib/MapView.svelte';
  import Planner from './lib/Planner.svelte';
  import Sheet from './lib/Sheet.svelte';
  import Settings from './lib/Settings.svelte';
  import Gauges from './lib/Gauges.svelte';
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

<div class="shell">
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

  {#if view === 'map' || view === 'plan'}
    <div class="planner" class:full={view === 'plan'}>
      <Planner {data} {report} {spots} {spotsError} {offset} {fishery} onoffset={(o) => (offset = o)} onfishery={(f) => (fishery = f)} {error} {selectedId} onselect={select} canReview={!!getToken()} onreview={() => (view = 'settings')} />
    </div>
    <main class="mapwrap" class:hide={view === 'plan'}>
      <MapView {data} journal={journalGeo} {showJournal} {selectedId} {theme} {showStocking} {showGauges} {showAdvisories} {showReports} onselect={select} />
      <div class="layers card" role="group" aria-label="Map layers">
        <label class="lyr"><input type="checkbox" bind:checked={showStocking} /> Stocking</label>
        <label class="lyr"><input type="checkbox" bind:checked={showReports} /> Report ratings</label>
        <label class="lyr"><input type="checkbox" bind:checked={showGauges} /> Gauges</label>
        <label class="lyr"><input type="checkbox" bind:checked={showJournal} /> My pins &amp; trips</label>
        <label class="lyr"><input type="checkbox" bind:checked={showAdvisories} /> Advisories</label>
      </div>
      <div class="legend card" aria-label="Stocking freshness legend">
        <span><i class="dot this_week"></i> This week</span>
        <span><i class="dot recent"></i> Last 2 weeks</span>
        <span><i class="dot older"></i> Older</span>
        <span><i class="dot upcoming"></i> Scheduled</span>
        <span><i class="sym diamond"></i> Gauge (provisional)</span>
        <span><i class="sym ring"></i> Algae advisory/precaution</span>
      </div>
      <button class="offline" onclick={() => (offlineFor = selectedId)}>Prepare for offline</button>
    </main>
    {#if dayFor && view === 'map'}
      <div class="sheetwrap wide"><DayView id={dayFor} {fishery} startOffset={offset} onback={() => (dayFor = null)} onlog={(id) => (logFor = id)} onoffline={(id) => (offlineFor = id)} /></div>
    {:else if selectedId && view === 'map'}
      <div class="sheetwrap"><Sheet id={selectedId} onclose={() => (selectedId = null)} onday={(id) => (dayFor = id)} onlog={(id) => (logFor = id)} /></div>
    {/if}
  {:else if view === 'settings'}
    <main class="page"><Settings {theme} onTheme={(t) => (theme = t)} onChanged={() => { load(); loadReport(); api.spots(isoDay(offset), fishery).then((v) => (spots = v)).catch(() => {}); }} /></main>
  {:else if view === 'journal'}
    <main class="page"><Journal {wbList} onlog={() => (logFor = null)} /></main>
  {:else}
    <main class="page"><Gauges /></main>
  {/if}

  {#if logFor !== undefined}
    <div class="overlay"><LogTrip {wbList} initialWb={logFor} onclose={() => (logFor = undefined)} onsaved={() => { logFor = undefined; view = 'journal'; }} /></div>
  {/if}
  {#if offlineFor !== undefined}<Offline wbId={offlineFor} onclose={() => (offlineFor = undefined)} />{/if}
</div>

<style>
  .shell { position: relative; height: 100%; display: grid; grid-template-columns: 64px 380px 1fr; grid-template-rows: 100%; }
  .shell > :global(.page) { grid-column: 2 / -1; }
  .rail { background: var(--bg); border-right: 1px solid var(--line); display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 0; }
  .logo { margin-bottom: 12px; }
  .navbtn { flex-direction: column; border: 0; background: none; width: 56px; height: 56px; gap: 2px; border-radius: 12px; color: var(--text-quiet); padding: 0; }
  .navbtn[aria-current='page'] { background: var(--surface); color: var(--fresh-1); }
  .lbl { font-size: 10px; }
  .spacer { flex: 1; }
  .planner { border-right: 1px solid var(--line); background: var(--bg); overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
  .mapwrap { position: relative; min-width: 0; }
  .sheetwrap { position: absolute; top: 0; right: 0; bottom: 0; width: 340px; background: var(--bg); border-left: 1px solid var(--line); z-index: 5; }
  .page { overflow: auto; }
  .layers { position: absolute; top: 12px; right: 56px; padding: 6px 12px; z-index: 2; background: var(--surface); }
  .lyr { display: flex; align-items: center; gap: 8px; min-height: 36px; margin: 0; color: var(--text); font-size: 13px; }
  .lyr.off { color: var(--text-quiet); }
  .lyr input { width: 18px; height: 18px; accent-color: var(--accent); }
  .soon { font-size: 11px; }
  .legend { position: absolute; left: 12px; bottom: 12px; display: flex; gap: 14px; padding: 8px 12px; font-size: 12px; z-index: 2; flex-wrap: wrap; max-width: calc(100% - 24px); }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .overlay { position: absolute; inset: 0; z-index: 15; background: var(--bg); }
  .sym { width: 10px; height: 10px; display: inline-block; border: 2px solid var(--text-quiet); }
  .sym.diamond { transform: rotate(45deg); }
  .sym.ring { border-radius: 50%; border-color: var(--accent); }
  .sheetwrap.wide { width: min(520px, 60%); }
  .offline { position: absolute; left: 12px; top: 12px; z-index: 2; }

  @media (max-width: 899px) {
    .shell { grid-template-columns: 1fr; grid-template-rows: 1fr 64px; }
    .rail { grid-row: 2; grid-column: 1; flex-direction: row; justify-content: space-around; border-right: 0; border-top: 1px solid var(--line); padding: 0 4px; order: 9; gap: 0; }
    .logo, .spacer { display: none; }
    .navbtn { flex: 1; width: auto; height: 100%; }
    .shell > :global(*) { grid-column: 1; grid-row: 1; }
    .shell > .rail { grid-row: 2; }
    .planner { z-index: 3; align-self: end; height: 42%; border: 1px solid var(--line); border-radius: 16px 16px 0 0; }
    .planner.full { height: 100%; border-radius: 0; }
    .mapwrap.hide { display: none; }
    .sheetwrap, .sheetwrap.wide { width: 100%; top: auto; height: 62%; z-index: 4; border-left: 0; border-top: 1px solid var(--line); border-radius: 16px 16px 0 0; }
    .layers { right: 12px; top: 64px; }
    .offline { top: 64px; }
    .lyr.off { display: none; }
    .legend { bottom: calc(42% + 12px); }
  }
</style>
