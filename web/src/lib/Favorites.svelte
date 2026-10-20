<script>
  import { liveQuery } from 'dexie';
  import { db } from './db.js';
  import { api } from './api.js';
  import { asOf } from './clock.svelte.js';
  import { forecastNote } from './forecastText.js';
  import { recentTrips, forecastStale } from './favoriteSummary.js';
  import { gaugeStale } from './gaugeText.js';
  import Icon from './Icon.svelte';
  let { waters=[], onselect }=$props();
  let details=$state({}), trips=$state([]), catches=$state([]), loading=$state(false), revision=$state(0), now=$state(Date.now());
  $effect(()=>{const timer=setInterval(()=>{now=Date.now();},60000);return()=>clearInterval(timer);});
  $effect(()=>{
    const sub=liveQuery(async()=>({trips:await db.trips.toArray(),catches:await db.catches.toArray()})).subscribe(v=>{trips=v.trips;catches=v.catches;});
    return ()=>sub.unsubscribe();
  });
  $effect(()=>{
    revision;
    const ids=waters.map(w=>w.id);let current=true;loading=true;details={};
    // Bound concurrent reads and let the existing public API cache serve them offline.
    (async()=>{const out={};for(let i=0;i<ids.length;i+=4){await Promise.all(ids.slice(i,i+4).map(async id=>{try{out[id]=await api.waterbody(id);}catch{out[id]=null;}}));if(current) details={...out};}if(current)loading=false;})();
    return ()=>{current=false;};
  });
  const tripDate=t=>{const d=new Date(t.started_at);return Number.isNaN(d.getTime())?'Date not recorded':d.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'});};
</script>
<svelte:window ononline={()=>revision++}/>
<div class="favorites" aria-label="Favorite waters dashboard">
  {#if waters.length}<button onclick={()=>revision++} disabled={loading}>Refresh favorites</button>{/if}
  {#if !waters.length}<p class="quiet small">Star a waterbody to see its conditions and your recent trips here.</p>{/if}
  {#if loading}<p class="quiet small" role="status">Loading saved waters…</p>{/if}
  {#each waters as water (water.id)}
    {@const c=details[water.id]?.conditions}
    {@const wx=c?.weather}
    {@const gauge=c?.gauges?.find(g=>g.values?.discharge_cfs)}
    {@const visits=recentTrips(trips,catches,water.id)}
    <article class="favorite" aria-label={water.name}>
      <button class="water" aria-label={water.name} onclick={()=>onselect(water.id)}><Icon name={water.kind==='river'?'flow':'map'} size={18}/><strong>{water.name}</strong><Icon name="trend_steady" size={16}/></button>
      <p class="quiet small">{water.kind} · {water.zone}{water.lat==null?' · No map pin yet':''}</p>
      {#if c}
        <p class="small"><strong>Forecast</strong> {wx?.day?.temp_f!=null?`${wx.day.temp_f}°F · `:''}{forecastNote(wx)}</p>
        {#if wx}<p class="quiet small">{forecastStale(wx,now)?'Stale · ':''}NWS {asOf(wx.as_of)}</p>{/if}
        {#if gauge}<p class="small"><strong>Flow</strong> {Math.round(gauge.values.discharge_cfs.value).toLocaleString()} cfs · {gauge.trend??'trend unavailable'}</p><p class="quiet small">{gaugeStale(gauge,now)?'Stale · ':''}USGS, provisional · {asOf(gauge.values.discharge_cfs.observed_at)}</p>{/if}
        {#each c.advisories??[] as a}<p class="alert small"><Icon name="advisory" size={16}/> Algae advisory · {a.issued??'date not reported'} — open details for the source.</p>{/each}
        {#if c.fire?.nearby?.fires?.length}<p class="alert small"><Icon name="advisory" size={16}/> {c.fire.nearby.fires.length} nearby mapped {c.fire.nearby.fires.length===1?'fire':'fires'} — open details. Perimeters can lag; this is not a closure notice. NIFC {asOf(c.fire.nearby.as_of)}</p>{/if}
        {#if c.fire?.danger?.covered && c.fire.danger.level>=2}<p class="alert small">ODF fire danger: {c.fire.danger.label} · {asOf(c.fire.danger.as_of)}</p>{/if}
      {:else if water.id in details}<p class="quiet small">Conditions have not been saved on this device. Connect to load them.</p>{/if}
      <div class="recent"><strong class="small">Your recent trips</strong>
        {#each visits as t}<p class="small">{tripDate(t)} · {t.fish} fish{t.dirty?' · Waiting to sync':''}</p>{/each}
        {#if !visits.length}<p class="quiet small">No trips logged here on this device yet.</p>{/if}
      </div>
    </article>
  {/each}
</div>
<style>
  .favorites{display:flex;flex-direction:column;gap:12px;} .favorite{background:var(--glass-fill);border:1px solid var(--hair);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:6px;}
  .water{display:flex;gap:10px;justify-content:flex-start;text-align:left;width:100%;padding:0;border:0;background:none;min-height:44px;color:var(--text);} .water strong{flex:1;min-width:0;} .water :global(svg){color:var(--fresh-2);flex-shrink:0;}
  .small{font-size:12.5px;margin:0;overflow-wrap:anywhere;} .recent{border-top:1px solid var(--hair);padding-top:8px;margin-top:4px;display:flex;flex-direction:column;gap:4px;} .alert{display:flex;gap:6px;color:var(--accent);}
</style>
