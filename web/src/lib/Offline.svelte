<script>
  import { prepareTiles, cachedTileCount, clearTiles, basemapInfo, tilePreview } from './tiles.js';
  import { areaAround, watersBounds, intersectBounds, tileCount, tripDates, hasPoint, MAX_OFFLINE_TILES } from './offlineArea.js';
  import { loadDay } from './conditions.js';
  import { api, isoDay, FISHERIES } from './api.js';
  import { requestPersistence, storageInfo, fmtBytes } from './storage.js';
  let { wbId = null, startDate = isoDay(), fishery = 'trout', waters = [], zones = [], zone = 'willamette', onclose } = $props();
  let scope = $state(wbId ? 'trip' : 'zone'), waterId = $state(wbId ? String(wbId) : '');
  let tripFishery = $state(fishery);
  let selectedZone = $state(zone), radius = $state(15), maxZ = $state(10), start = $state(startDate), days = $state(3);
  let progress = $state({ done:0,total:0 }), busy = $state(false), msg = $state(''), have = $state(0);
  let info = $state(null), loading = $state(true), storage = $state(null), preview = $state(null), previewError = $state('');
  let ctl = null;
  const water = $derived(waters.find(w => String(w.id) === waterId));
  const targetZone = $derived(scope === 'trip' ? water?.zone ?? selectedZone : selectedZone);
  const requested = $derived(scope === 'trip' ? areaAround(water,radius) : scope === 'oregon' ? info?.bbox : watersBounds(waters.filter(w => w.zone === selectedZone)));
  const bbox = $derived(intersectBounds(requested,info?.bbox));
  const zoom = $derived(Math.min(maxZ,info?.maxZ ?? maxZ));
  const minZ = $derived(Math.max(6,info?.minZ ?? 6));
  const total = $derived(tileCount(bbox,minZ,zoom));
  const dates = $derived(tripDates(start,days));
  const free = $derived(storage?.quota != null && storage?.usage != null ? Math.max(0,storage.quota-storage.usage) : null);
  const tooLarge = $derived(total > MAX_OFFLINE_TILES || (free != null && preview?.estimatedBytes > free));
  $effect(() => { Promise.all([basemapInfo(),cachedTileCount(),storageInfo()]).then(([b,n,s]) => {info=b;have=n;storage=s;loading=false;}).catch(() => {loading=false;}); });
  $effect(() => {
    const area=bbox, z=zoom, low=minZ, n=total;
    let current=true; preview=null; previewError='';
    if (area && n && n<=MAX_OFFLINE_TILES) tilePreview(area,low,z).then(v => {if(current) preview=v;}).catch(e => {if(current) previewError=e.message;});
    return () => {current=false;};
  });
  async function go() {
    busy=true;msg='';progress={done:0,total};ctl=new AbortController();
    requestPersistence();
    const parts=[];
    try {
      // Public data comes first; save only the selected zone (or each offered zone for the archive overview).
      const keys=scope==='oregon' ? zones.map(z=>z.key) : [targetZone];
      const checkStop=()=>{if(ctl.signal.aborted) throw new DOMException('Download cancelled','AbortError');};
      let failed=0;
      for (const key of keys) {
        checkStop();
        const results=await Promise.allSettled([api.map(key),api.report(key),api.gauges(key),api.spots(start,tripFishery,null,key)]);
        failed+=results.filter(r=>r.status==='rejected').length;
      }
      checkStop();
      const publicResults=await Promise.allSettled([api.waterbodyList(),api.fireMap()]);
      failed+=publicResults.filter(r=>r.status==='rejected').length;
      parts.push(failed ? `area data (${failed} requests unavailable)` : 'area data');
      if (scope==='trip' && water) {
        await api.waterbody(water.id).catch(()=>parts.push('water details unavailable'));
        let saved=0;
        for (const date of dates) {
          checkStop();
          try {await loadDay(water.id,date,tripFishery,false);saved++;} catch { /* report the exact count below */ }
        }
        parts.push(`${saved} of ${dates.length} days of conditions for ${water.name}`);
      }
      checkStop();
      if (info && bbox) {
        const r=await prepareTiles({bbox,minZ,maxZ:zoom,signal:ctl.signal,onProgress:(done,total)=>(progress={done,total})});
        parts.push(`${r.stored} new map tiles`);
        if(r.empty) parts.push(`${r.empty} tiles have no map data in the archive`);
        if(r.stopped) parts.push(`download stopped: ${r.stopped}; saved tiles are retained`);
      } else parts.push('no map tiles (no installed coverage for this area)');
      msg=`Saved ${parts.join(', ')}.`;
    } catch(e) {msg=e.name==='AbortError' ? 'Stopped. Data already saved is retained.' : `Could not finish: ${e.message}. Data already saved is retained.`;}
    finally {have=await cachedTileCount();storage=await storageInfo();if(bbox && total<=MAX_OFFLINE_TILES) preview=await tilePreview(bbox,minZ,zoom).catch(()=>null);busy=false;}
  }
  const close=()=>{ctl?.abort();onclose();};
  async function clear(){await clearTiles();have=0;storage=await storageInfo();preview=bbox && total<=MAX_OFFLINE_TILES ? await tilePreview(bbox,minZ,zoom) : null;msg='Offline map tiles cleared.';}
</script>

<dialog open aria-label="Prepare for offline">
  <h2>Prepare for offline</h2>
  <p class="quiet">Save a trip area or another part of Oregon on this device. Forecasts keep their available dates and source times; saving does not extend their range.</p>
  <label for="offline-area">Area to save</label>
  <select id="offline-area" bind:value={scope} disabled={busy}>
    <option value="trip">Around a waterbody</option><option value="zone">Zone's pinned waters</option><option value="oregon">Installed Oregon basemap</option>
  </select>
  {#if scope==='trip'}
    <label for="offline-water">Trip waterbody</label>
    <select id="offline-water" bind:value={waterId} disabled={busy}><option value="">Choose a pinned waterbody</option>{#each waters.filter(hasPoint) as w}<option value={String(w.id)}>{w.name}</option>{/each}</select>
    <label for="offline-radius">Area around the pin</label>
    <select id="offline-radius" bind:value={radius} disabled={busy}>{#each [5,15,30,50] as km}<option value={km}>{km} km in each direction</option>{/each}</select>
    <label for="offline-date">Trip date</label><input id="offline-date" type="date" bind:value={start} disabled={busy}/>
    <label for="offline-fishery">Trip fishery</label><select id="offline-fishery" bind:value={tripFishery} disabled={busy}>{#each FISHERIES as [key,label]}<option value={key}>{label}</option>{/each}</select>
    <label for="offline-days">Days of conditions</label><select id="offline-days" bind:value={days} disabled={busy}>{#each [1,3,7] as n}<option value={n}>{n} {n===1?'day':'days'}</option>{/each}</select>
  {:else if scope==='zone'}
    <label for="offline-zone">Zone</label><select id="offline-zone" bind:value={selectedZone} disabled={busy}>{#each zones as z}<option value={z.key}>{z.label}</option>{/each}</select>
    <p class="quiet small">Rectangle around stored pins, not an official zone boundary.</p>
  {/if}
  {#if loading}<p role="status">Checking installed map…</p>
  {:else if info}
    <label for="mz">Map detail</label><select id="mz" bind:value={maxZ} disabled={busy}>{#each [8,10,11,12,13,14].filter(z=>z<=info.maxZ) as z}<option value={z}>Zoom {z}{z>=12?' · high detail':''}</option>{/each}</select>
    <p class="quiet small">Installed map supports detail through zoom {info.maxZ}. Only coverage inside this archive can be saved.</p>
    {#if !bbox}<p role="status">Choose an area with a stored pin inside the installed map.</p>{/if}
    {#if total>MAX_OFFLINE_TILES}<p role="status">{total.toLocaleString()} tiles. Choose a smaller area or lower detail (limit 25,000).</p>
    {:else if preview}<p class="quiet small mono">{preview.total.toLocaleString()} tiles · {preview.cached.toLocaleString()} already saved here · about {fmtBytes(preview.estimatedBytes)} additional storage</p>
      <p class="quiet small">Estimate uses 20 KB per new tile; actual size varies.</p>{/if}
  {:else}<p role="status">No basemap installed on the server. Public data and selected trip conditions can still be saved.</p>{/if}
  <p class="quiet small">{have.toLocaleString()} map tiles saved on this device{free!=null?` · ${fmtBytes(free)} storage available`:''}.</p>
  {#if free!=null && preview?.estimatedBytes>free}<p role="alert">The estimate exceeds available storage. Choose a smaller area or lower detail.</p>{/if}
  {#if previewError}<p role="alert">{previewError}</p>{/if}
  {#if busy}<progress max={progress.total||1} value={progress.done} aria-label="Download progress"></progress>{/if}
  {#if msg}<p role="status">{msg}</p>{/if}
  <div class="row">
    <button class="primary" onclick={go} disabled={busy||loading||tooLarge||!!previewError||(!!info&&!preview)||(scope==='trip'&&(!hasPoint(water)||!dates.length))||(!!info&&!bbox)}>{busy?'Saving…':'Save for offline'}</button>
    {#if busy}<button onclick={()=>ctl?.abort()}>Stop</button>{/if}
    {#if have}<button onclick={clear} disabled={busy}>Clear saved map</button>{/if}
    <button onclick={close}>Close</button>
  </div>
</dialog>
<style>
  dialog {position:fixed;inset:0;margin:auto;z-index:20;background:var(--surface);color:var(--text);border:1px solid var(--line);border-radius:16px;max-width:480px;width:calc(100% - 32px);max-height:calc(100dvh - 32px);overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:8px;}
  h2{font-size:18px;} .small{font-size:13px;margin:0;} .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;} progress{width:100%;accent-color:var(--accent);}
</style>
