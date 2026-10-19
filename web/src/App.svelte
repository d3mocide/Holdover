<script>
  import { api, isoDay } from './lib/api.js';
  import Icon from './lib/Icon.svelte';
  import Logo from './lib/Logo.svelte';
  import MapView from './lib/MapView.svelte';
  import PlanView from './lib/PlanView.svelte';
  import MapCard from './lib/MapCard.svelte';
  import ReportsView from './lib/ReportsView.svelte';
  import ZonePicker from './lib/ZonePicker.svelte';
  import Sheet from './lib/Sheet.svelte';
  import Settings from './lib/Settings.svelte';
  import Gauges from './lib/Gauges.svelte';
  import Legend from './lib/Legend.svelte';
  import DayView from './lib/DayView.svelte';
  import Journal from './lib/Journal.svelte';
  import Gear from './lib/Gear.svelte';
  import GearForm from './lib/GearForm.svelte';
  import SetupForm from './lib/SetupForm.svelte';
  import LogTrip from './lib/LogTrip.svelte';
  import Offline from './lib/Offline.svelte';
  import { liveQuery } from 'dexie';
  import { db, metaGet, metaSet } from './lib/db.js';
  import { startSync, syncState } from './lib/sync.svelte.js';
  import { auth, loadAuth, prefs, homeForRequests, setHome } from './lib/auth.svelte.js';

  const stored = (k, d) => { try { return localStorage.getItem(k) || d; } catch { return d; } };
  let theme = $state(stored('holdover.theme', 'fir'));
  let view = $state('map');
  // Hide the side panel (or the bottom panel on a phone) to see the whole map. Remembered on this device.
  let collapsed = $state(stored('holdover.panelHidden', '') === '1');
  const setCollapsed = (v) => { collapsed = v; try { localStorage.setItem('holdover.panelHidden', v ? '1' : ''); } catch { /* not remembered */ } };
  const go = (k) => { view = k; if (collapsed) setCollapsed(false); };  // choosing a tab means you want its content
  // The side panel sizes to its content. The Map tab is the map alone (no panel); the spot list lives in Plan.
  const PANEL = { map: '0px', plan: 'min(520px, 44vw)', reports: 'min(560px, 46vw)', journal: 'min(460px, 42vw)', gear: 'min(520px, 44vw)', gauges: 'min(660px, 46vw)', settings: 'min(520px, 44vw)' };
  let panelW = $state(520);
  let wide = $state(typeof innerWidth === 'number' ? innerWidth >= 900 : true);
  $effect(() => { const f = () => (wide = innerWidth >= 900); addEventListener('resize', f); return () => removeEventListener('resize', f); });
  let data = $state(null);
  let report = $state(null);
  let error = $state('');
  let selectedId = $state(null);
  let showStocking = $state(true);
  let showGauges = $state(true);
  let showAdvisories = $state(true);
  let showFire = $state(true);
  let fireData = $state(null);
  let showReports = $state(true);
  let dayFor = $state(null);
  let offset = $state(0);
  let fishery = $state('trout');
  // The ODFW zone every view follows (remembered on this device); the list comes from the server.
  let zones = $state([]);
  let zone = $state(stored('holdover.zone', 'willamette'));
  const setZone = (z) => { if (z === zone) return; zone = z; data = null; mapSpots = null; selectedId = null; dayFor = null; try { localStorage.setItem('holdover.zone', z); } catch { /* not remembered */ } };
  $effect(() => { api.zones().then((r) => { zones = r.zones; if (!r.zones.some((z) => z.key === zone) && r.zones.length) setZone(r.zones[0].key); }).catch(() => { /* one zone: nothing to pick */ }); });
  let mapSpots = $state(null);  // today's ranking, for the Map card
  let mapSpotsError = $state('');
  let showJournal = $state(true);
  let layersOpen = $state(false);
  let legendOpen = $state(false);
  let wbList = $state([]);
  let picking = $state(false);
  // An invite link looks like /?invite=CODE. Read it once, then clean the address bar so the code is not bookmarked.
  const inviteCode = typeof location !== 'undefined' ? new URLSearchParams(location.search).get('invite') : null;
  let invite = $state(inviteCode);
  if (inviteCode) { view = 'settings'; try { history.replaceState(null, '', location.pathname); } catch { /* ignore */ } }
  let gearEdit = $state(undefined); // undefined: closed, null: new item, object: editing
  let gearBrowse = $state(false);
  let setupEdit = $state(undefined);
  let editTrip = $state(undefined); // undefined: closed, otherwise the trip row being edited
  let logFor = $state(undefined); // undefined: closed, null: open without a waterbody, number: preset
  let offlineFor = $state(undefined);
  let journalGeo = $state(null);

  $effect(() => {
    api.waterbodyList().then(async (l) => { wbList = l; await metaSet('wbList', l); }).catch(async () => { wbList = await metaGet('wbList', []); });
    loadAuth().then(startSync); // sync needs to know who is signed in
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
    try { data = await api.map(zone); error = ''; } catch (e) { error = e.message; }
  }
  function loadMapSpots() {
    mapSpotsError = '';
    const home = homeForRequests(); // signed in: the server uses the account's home; signed out: this device's
    api.spots(isoDay(0), fishery, home, zone).then((v) => (mapSpots = v)).catch((e) => (mapSpotsError = e.message));
  }
  $effect(() => { fishery; zone; loadMapSpots(); });
  async function loadReport() { try { report = await api.report(); } catch { /* keep last */ } }
  $effect(() => { zone; load(); });
  $effect(() => { loadReport(); api.fireMap().then((v) => (fireData = v)).catch(() => { /* the layer just stays empty */ }); });

  const tabs = [['map', 'Map', 'map'], ['plan', 'Plan', 'plan'], ['reports', 'Reports', 'reports'], ['journal', 'Journal', 'journal'], ['gear', 'Gear', 'gear'], ['gauges', 'Gauges', 'gauge']];
  // Where a waterbody's sheet can open: over the map, which is visible on the Map tab and, on a wide screen, beside the Plan list.
  const drawerOpen = $derived(gearEdit !== undefined || setupEdit !== undefined || editTrip !== undefined || logFor !== undefined);
  $effect(() => { if (drawerOpen) legendOpen = false; });
  const onMap = $derived(view === 'map' || (view === 'plan' && wide));
  // Only on a tight window (under 1280 px) does the Plan list narrow while a sheet is open; with room to spare it stays put.
  let tight = $state(typeof innerWidth === 'number' ? innerWidth < 1280 : false);
  $effect(() => { const f = () => (tight = innerWidth < 1280); addEventListener('resize', f); return () => removeEventListener('resize', f); });
  const select = (id) => { selectedId = id; dayFor = null; if (!onMap) view = 'map'; };
</script>

<div class="shell" class:haszones={zones.length > 1} class:sheetopen={onMap && !!(selectedId || dayFor)} class:drawer={drawerOpen} class:nopanel={view === 'map'} class:collapsed class:full={view === 'plan'} class:tall={view !== 'map' && view !== 'plan'} style:--panel-w={collapsed && wide ? '0px' : (view === 'plan' && tight && (selectedId || dayFor) ? 'min(380px, 36vw)' : (PANEL[view] ?? PANEL.map))}>
  <nav class="rail" aria-label="Main">
    <span class="logo"><Logo /></span>
    {#each tabs as [k, label, icon]}
      <button class="navbtn" aria-current={view === k ? 'page' : undefined} onclick={() => go(k)} aria-label={label}>
        <Icon name={icon} /><span class="lbl">{label}</span>
      </button>
    {/each}
    <span class="spacer"></span>
    <button class="navbtn" aria-current={view === 'settings' ? 'page' : undefined} onclick={() => go('settings')} aria-label="Settings">
      <Icon name="settings" /><span class="lbl">Settings</span>
    </button>
  </nav>

  <button class="ptoggle" onclick={() => setCollapsed(!collapsed)} aria-expanded={!collapsed} aria-label={collapsed ? 'Show panel' : 'Hide panel'} title={collapsed ? 'Show panel' : 'Hide panel'}><Icon name="trend_steady" size={18} /></button>
  <main class="planner" bind:clientWidth={panelW} class:gone={collapsed} class:full={view === 'plan'} class:tall={view !== 'map' && view !== 'plan'}>
    {#if view === 'plan'}
      <PlanView {data} {report} {zone} {zones} onzone={setZone} {offset} {fishery} onoffset={(o) => (offset = o)} onfishery={(f) => (fishery = f)} {error} {selectedId} onselect={select} canReview={!!auth.user?.is_admin} onreview={() => (view = 'settings')} onreports={() => go('reports')} />
    {:else if view === 'reports'}
      <ReportsView {zone} />
    {:else if view === 'settings'}
      <Settings {theme} {wbList} {invite} {picking} onpick={() => { picking = !picking; if (picking && !wide) view = 'map'; }} oninvitedone={() => (invite = null)} onTheme={(t) => (theme = t)} onChanged={() => { load(); loadReport(); loadMapSpots(); }} />
    {:else if view === 'journal'}
      <Journal {wbList} onlog={() => (logFor = null)} onedit={(t) => (editTrip = t)} />
    {:else if view === 'gear'}
      <Gear {wbList} onitem={(g, browse = false) => { gearBrowse = browse; gearEdit = g; }} onsetup={(st) => (setupEdit = st)} />
    {:else}
      <Gauges {zone} {zones} onzone={setZone} />
    {/if}
  </main>
  <div class="mapwrap" class:hide={view === 'plan'} class:tall={view !== 'map' && view !== 'plan'} class:sheet={selectedId && !dayFor && onMap} class:wide={!!dayFor && onMap}>
      <MapView zoneKey={zone} inset={wide ? panelW + 112 : 0} home={prefs.home} pickMode={picking} onpick={async (p) => { picking = false; try { await setHome(p); } catch { /* shown in Settings next time */ } }} {data} journal={journalGeo} {showJournal} {selectedId} {theme} {showStocking} {showGauges} {showAdvisories} {showReports} fire={fireData} {showFire} onselect={select} />
      <div class="layers glass" class:open={layersOpen} role="group" aria-label="Map layers">
        <button class="pill" aria-expanded={layersOpen} onclick={() => (layersOpen = !layersOpen)}><Icon name="layers" /> Layers</button>
        {#if layersOpen}
          <label class="lyr"><input type="checkbox" bind:checked={showStocking} /> Stocking</label>
          <label class="lyr"><input type="checkbox" bind:checked={showReports} /> Report ratings</label>
          <label class="lyr"><input type="checkbox" bind:checked={showGauges} /> Gauges</label>
          <label class="lyr"><input type="checkbox" bind:checked={showJournal} /> My pins &amp; trips</label>
          <label class="lyr"><input type="checkbox" bind:checked={showAdvisories} /> Advisories</label>
          <label class="lyr"><input type="checkbox" bind:checked={showFire} /> Fire danger and fires</label>
        {/if}
      </div>
      {#if zones.length > 1}
        <div class="zonepill glass"><ZonePicker variant="map" {zones} {zone} onzone={setZone} /></div>
      {/if}
      <div class="legend glass" class:open={legendOpen} role="group" aria-label="Map legend">
        <button class="pill" aria-label="Legend" aria-expanded={legendOpen} onclick={() => (legendOpen = !legendOpen)}><Icon name="legend" /> <span class="lgl">Legend</span></button>
        {#if legendOpen}<Legend {theme} />
        {/if}
      </div>
      {#if picking}
        <div class="pickbar glass" role="status">Tap the map to set your home <button class="pill" onclick={() => (picking = false)}>Cancel</button></div>
      {/if}
      <button class="offline" onclick={() => (offlineFor = selectedId)} aria-label="Prepare for offline" title="Prepare for offline"><Icon name="offline" size={18} /></button>
      {#if view === 'map' && !drawerOpen && !(tight && (selectedId || dayFor))}
        <MapCard spots={mapSpots} {zones} {zone} onzone={setZone} {fishery} onfishery={(f) => (fishery = f)} {selectedId} onselect={select} onplan={() => go('plan')} error={mapSpotsError} />
      {/if}
  </div>
    {#if dayFor && onMap}
      <div class="sheetwrap wide"><DayView id={dayFor} {fishery} startOffset={offset} onback={() => (dayFor = null)} onlog={(id) => (logFor = id)} onoffline={(id) => (offlineFor = id)} /></div>
    {:else if selectedId && onMap}
      <div class="sheetwrap"><Sheet id={selectedId} onclose={() => (selectedId = null)} onday={(id) => (dayFor = id)} onlog={(id) => (logFor = id)} /></div>
    {/if}

  {#if gearEdit !== undefined}
    <div class="overlay"><GearForm item={gearEdit} browse={gearBrowse} onclose={() => (gearEdit = undefined)} onsaved={() => (gearEdit = undefined)} /></div>
  {/if}
  {#if setupEdit !== undefined}
    <div class="overlay"><SetupForm setup={setupEdit} onclose={() => (setupEdit = undefined)} onsaved={() => (setupEdit = undefined)} /></div>
  {/if}
  {#if editTrip !== undefined}
    <div class="overlay"><LogTrip {wbList} trip={editTrip} onclose={() => (editTrip = undefined)} onsaved={() => (editTrip = undefined)} /></div>
  {/if}
  {#if logFor !== undefined}
    <div class="overlay"><LogTrip {wbList} initialWb={logFor} onclose={() => (logFor = undefined)} onsaved={() => { logFor = undefined; view = 'journal'; }} /></div>
  {/if}
  {#if offlineFor !== undefined}<Offline wbId={offlineFor} onclose={() => (offlineFor = undefined)} />{/if}
</div>

<style>
  .shell { --sheet-w: min(clamp(440px, 38vw, 700px), calc(100% - var(--panel-w, 380px) - 128px)); --wide-w: min(clamp(560px, 46vw, 860px), calc(100% - var(--panel-w, 380px) - 128px)); position: relative; height: 100%; display: grid; grid-template-columns: 64px var(--panel-w, 380px) 1fr; grid-template-rows: 100%; gap: 16px; padding: 16px; transition: grid-template-columns 0.25s ease; }
  .shell > :global(*) { grid-row: 1; }
  .planner.gone, .shell.nopanel .planner, .shell.nopanel .ptoggle { display: none; }
  /* The toggle straddles the panel's right edge (desktop) or its top edge (phone). The arrow is the trend_steady icon, rotated. */
  .ptoggle { position: absolute; z-index: 4; top: 50%; left: calc(96px + var(--panel-w, 380px) - 22px); width: 44px; height: 44px; margin-top: -22px; padding: 0; border-radius: 999px;
    background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense); border: 1px solid var(--glass-line); color: var(--text);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4); transition: left 0.25s ease; }
  .ptoggle :global(svg) { transform: rotate(180deg); transition: transform 0.2s ease; }
  .shell.collapsed .ptoggle { left: 92px; } .shell.collapsed .ptoggle :global(svg) { transform: none; }
  .rail, .offline, .layers, .legend { background: var(--glass); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); border: 1px solid var(--glass-line); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
  /* Layers and Legend are small buttons until opened: clear chrome glass like the rail, dense once their text list is showing. */
  .planner, .sheetwrap, .layers.open, .legend.open { background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense); border: 1px solid var(--glass-line); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
  .rail { grid-column: 1; z-index: 3; border-radius: 20px; display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 0; }
  .logo { margin-bottom: 12px; }
  .navbtn { flex-direction: column; border: 0; background: none; width: 56px; height: 56px; gap: 2px; border-radius: 12px; color: var(--text-quiet); padding: 0; }
  .navbtn[aria-current='page'] { background: var(--glass-fill); color: var(--fresh-1); box-shadow: inset 0 0 0 1px var(--glass-line); }
  .lbl { font-size: 10px; }
  .spacer { flex: 1; }
  .planner { grid-column: 2; z-index: 3; border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
  /* grid-area: auto keeps absolutely positioned children relative to the shell's padding box, so the map is
     full-bleed and every overlay offset is measured from the screen edge, not from the grid's inner padding. */
  .mapwrap { position: absolute; inset: 0; min-width: 0; z-index: 0; grid-area: auto !important; }
  .sheetwrap { grid-area: auto !important; position: absolute; top: 16px; right: 16px; bottom: 16px; width: var(--sheet-w); border-radius: 20px; overflow: hidden; z-index: 5; }
  .mapwrap { --sheet-inset: 0px; }
  .mapwrap.sheet { --sheet-inset: calc(var(--sheet-w) + 16px); }
  .mapwrap.wide { --sheet-inset: calc(var(--wide-w) + 16px); }
  .mapwrap :global(.maplibregl-ctrl-top-right) { right: var(--sheet-inset); top: 16px; transition: right 0.25s ease; }
  .mapwrap :global(.maplibregl-ctrl-top-right .maplibregl-ctrl) { margin: 0 16px 0 0; }
  .layers { position: absolute; top: 16px; right: calc(76px + var(--sheet-inset)); padding: 6px; z-index: 2; border-radius: 14px; display: flex; flex-direction: column; transition: right 0.25s ease; }
  .layers .lyr { padding: 0 14px; gap: 12px; }
  .pill { border: 0; background: none; min-height: 44px; padding: 0 14px; font-size: 13px; gap: 10px; justify-content: flex-start; min-height: 44px; }
  .lyr { display: flex; align-items: center; gap: 8px; min-height: 36px; margin: 0; color: var(--text); font-size: 13px; }
  .lyr.off { color: var(--text-quiet); }
  .lyr input { width: 18px; height: 18px; accent-color: var(--accent); }
  .soon { font-size: 11px; }
  /* One left edge for everything that sits beside the panel: 16 px after the rail, or after the panel (--base). The zone pill sits there
     first and Legend follows it; with the panel hidden (collapsed or the Map tab) there is no panel gap. */
  .shell { --panel-gap: 16px; --zp-w: 0px; --base: calc(96px + var(--panel-w, 0px) + var(--panel-gap) + var(--drawer-shift, 0px)); }
  .shell.collapsed, .shell.nopanel { --panel-gap: 0px; }
  .shell.haszones { --zp-w: 164px; }
  .zonepill { position: absolute; left: var(--base); transition: left 0.25s ease; top: 16px; z-index: 2; border-radius: 14px; width: 156px; padding: 6px; display: none; }
  .legend { position: absolute; left: calc(var(--base) + var(--zp-w)); transition: left 0.25s ease; top: 16px; border-radius: 14px; display: flex; padding: 6px; z-index: 2; flex-direction: column; align-items: flex-start; }
  .sm { font-size: 11px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .overlay { grid-area: auto !important; position: absolute; inset: 0; z-index: 15; background: var(--page-bg); overflow: hidden; }
  /* On a wide screen, forms (log a trip, gear, setups) open as a side drawer over the map instead of taking the whole page. */
  @media (min-width: 900px) {
    /* While a form drawer is open the map's left-hand controls (Legend) slide over to clear it. */
    .shell.drawer { --drawer-shift: calc(min(520px, calc(100% - 128px - var(--panel-w, 0px))) + 16px); }
    /* With a sheet open the top row is full (panel or card, Legend, Layers, zoom): Legend drops to the bottom-left, its list opening upward. */
    .shell.sheetopen .legend { top: auto; bottom: 16px; flex-direction: column-reverse; }
    .shell.sheetopen .zonepill { top: auto; bottom: 16px; }
    .shell.sheetopen .lgl { display: none; }  /* icon only, so the pill and Legend fit between the panel and the sheet */
    /* On the Map tab the Best bets card sits where the side panel does, and Legend moves to its right. */
    .shell.nopanel { --base: calc(96px + min(380px, calc(100% - 144px)) + 16px); }
    .shell.nopanel.drawer { --base: calc(96px + var(--drawer-shift, 0px)); }
    .zonepill { display: block; }
    /* Beside the drawer there is little room: Legend shrinks to its icon (and its list is closed when a drawer opens). */
    .shell.drawer .lgl { display: none; }
    /* It opens right beside the panel it came from (Journal, Gear, ...), not at the far edge of the screen. */
    .overlay { inset: 16px auto 16px calc(96px + var(--panel-w, 0px) + var(--panel-gap, 16px)); width: min(520px, calc(100% - 128px - var(--panel-w, 0px))); border-radius: 20px; background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense);
      border: 1px solid var(--glass-line); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
  }
  @media (min-width: 900px) and (max-width: 1279px) {
    .shell.sheetopen .zonepill { display: none; }  /* no room beside a sheet on a tight window; it returns when the sheet closes */
    .shell.sheetopen { --zp-w: 0px; }
  }
  @media (min-width: 900px) and (max-width: 1299px) {
    .shell.drawer .legend, .shell.drawer .zonepill { display: none; }  /* no room beside the drawer; they return when it closes */
  }
  .sym { width: 10px; height: 10px; display: inline-block; border: 2px solid var(--text-quiet); }
  .sym.diamond { background: var(--gauge); border-color: var(--bg); box-shadow: 0 0 0 1px var(--gauge); }
  .sym.diamond { transform: rotate(45deg); }
  .sym.ring { border-radius: 50%; border-color: var(--accent); }
  .sheetwrap.wide { width: var(--wide-w); }
  .pickbar { position: absolute; left: var(--base); top: 72px; z-index: 3; border-radius: 14px; padding: 4px 4px 4px 16px; display: flex; align-items: center; gap: 8px; font-size: 14px; }
  /* Icon only, tucked under the zoom control in the top-right column; it slides over with the sheet like Layers and zoom do. */
  .offline { position: absolute; right: calc(16px + var(--sheet-inset, 0px)); transition: right 0.25s ease; top: 114px; z-index: 2; color: var(--text); padding: 0; width: 44px; justify-content: center; }

  @media (max-width: 1099px) {
    .mapwrap :global(.maplibregl-ctrl-top-right) { display: none; }
    .layers { right: calc(16px + var(--sheet-inset)); }
  }
  @media (min-width: 900px) and (max-width: 1099px) {
    .offline { top: 82px; }  /* the zoom control is hidden at this width, so it tucks under Layers instead */
  }
  @media (max-width: 899px) {
    .shell { --nav-h: calc(64px + env(safe-area-inset-bottom, 0px)); grid-template-columns: 1fr; grid-template-rows: 1fr var(--nav-h); gap: 0; padding: 0; }
    .rail { grid-row: 2; grid-column: 1; flex-direction: row; justify-content: space-around; border-radius: 0; border-width: 1px 0 0; padding: 0 4px env(safe-area-inset-bottom, 0px); order: 9; gap: 0; }
    .logo, .spacer { display: none; }
    .navbtn { flex: 1; width: auto; height: 100%; }
    .shell > :global(*) { grid-column: 1; grid-row: 1; }
    .shell > .rail { grid-row: 2; }
    .ptoggle { top: auto; left: 50%; margin: 0 0 0 -22px; transition: none; bottom: calc(var(--nav-h) + (100% - var(--nav-h)) * 0.42 - 22px); }
    .shell.tall .ptoggle { bottom: calc(var(--nav-h) + (100% - var(--nav-h)) * 0.68 - 22px); }
    .shell.full .ptoggle { bottom: auto; top: 6px; }
    /* Collapsed: bottom right, above the map's attribution (a licence requirement, never covered). */
    .shell.collapsed .ptoggle, .shell.collapsed.tall .ptoggle, .shell.collapsed.full .ptoggle { top: auto; left: auto; right: 16px; margin: 0; bottom: calc(var(--nav-h) + 52px); }
    .ptoggle :global(svg) { transform: rotate(90deg); } .shell.collapsed .ptoggle :global(svg) { transform: rotate(-90deg); }
    .shell.collapsed .mapwrap.hide { display: block; }  /* Plan hides the map on a phone: hiding the panel brings it back */
    .planner { grid-column: 1; z-index: 3; align-self: end; height: 42%; border-radius: 20px 20px 0 0; }
    .planner.full { height: 100%; border-radius: 0; }
    .planner.tall { height: 68%; }
    .mapwrap.hide { display: none; }
    .sheetwrap, .sheetwrap.wide { width: 100%; top: auto; right: 0; bottom: var(--nav-h); height: calc(62% - var(--nav-h)); z-index: 6; border-radius: 20px 20px 0 0; background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; }
    .planner { background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; }
    .mapwrap.sheet, .mapwrap.wide { --sheet-inset: 0px; }
    .mapwrap :global(.maplibregl-ctrl-top-right) { display: none; }
    .layers { right: 16px; top: calc(16px + var(--safe-top)); }
    .offline { top: calc(16px + var(--safe-top)); }
    .lyr.off { display: none; }
    .legend { left: 68px; top: calc(16px + var(--safe-top)); }  /* beside the offline icon */
    .legend.open { left: 16px; top: calc(68px + var(--safe-top)); right: 16px; }
    .offline { left: 16px; right: auto; }
    .pickbar { left: 16px; }
    .mapwrap { inset: 0 0 var(--nav-h) 0; }
  }
</style>
