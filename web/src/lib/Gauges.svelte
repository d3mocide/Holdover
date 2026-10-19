<script>
  import { api, TREND } from './api.js';
  import { asOf } from './clock.svelte.js';
  import Icon from './Icon.svelte';
  import { floodShort, floodElevated } from './floodText.js';
  import { SORTS, sortGauges, detailParts, unusual } from './gaugeText.js';
  let gauges = $state([]);
  let note = $state('');
  let error = $state('');
  let sort = $state('name');
  $effect(() => { api.gauges().then((r) => { gauges = r.gauges; note = r.note; }).catch((e) => (error = e.message)); });
  const sorted = $derived(sortGauges(gauges, sort));
</script>
<div class="page" tabindex="0" role="region" aria-label="Gauges">
  <header><span class="ico"><Icon name="gauge" size={26} /></span><div><h1>Gauges</h1><p class="quiet">{note || 'USGS values are provisional.'}</p></div></header>
  {#if error}<p role="alert">Couldn't load gauges ({error}).</p>{/if}
  <div class="chips" role="group" aria-label="Sort gauges">
    {#each SORTS as [k, label]}<button class="chip" aria-pressed={sort === k} onclick={() => (sort = k)}>{label}</button>{/each}
  </div>
  <ul>
    {#each sorted as g (g.id)}
      <li class="card">
        <h2 title={`USGS ${g.site_no}`}>{g.name}</h2>
        <div class="flow">
          <span class="num mono">{g.values.discharge_cfs ? Math.round(g.values.discharge_cfs.value).toLocaleString() : '—'}</span>
          <span class="unit">cfs</span>
          {#if g.trend}<span class="trend small">{TREND[g.trend]}</span>{/if}
        </div>
        {#if detailParts(g).length}
          <p class="line mono">{#each detailParts(g) as part, i}{#if i}<span class="sep" aria-hidden="true">·</span>{/if}<span class:flag={i === 0 && unusual(g.vs_median_pct)}>{part}</span>{/each}</p>
        {/if}
        {#if g.flood}<p class="small noaa" class:warn={floodElevated(g.flood)}>{floodShort(g.flood)}</p>{/if}
        <p class="foot quiet">{asOf(g.as_of)}{#if g.stale} <b class="stale">Stale</b>{/if}</p>
      </li>
    {/each}
  </ul>
</div>
<style>
  .page { padding: 20px 16px 28px; height: 100%; overflow-y: auto; }
  header { display: flex; gap: 14px; align-items: center; margin-bottom: 12px; }
  .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--gauge); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } header p { margin: 2px 0 0; font-size: 13px; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
  .chip { padding: 0 12px; min-height: 44px; font-size: 13px; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }
  .card { display: flex; flex-direction: column; gap: 2px; }
  h2 { font-size: 14.5px; font-weight: 500; line-height: 1.3; margin: 0 0 6px; }
  .flow { display: flex; align-items: baseline; gap: 6px; }
  .num { font-size: 30px; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; }
  .unit { font-size: 13px; color: var(--text-quiet); }
  .trend { margin-left: auto; color: var(--text-quiet); }
  .line { margin: 2px 0 0; font-size: 13px; color: var(--text-quiet); display: flex; flex-wrap: wrap; gap: 0 8px; }
  .flag { color: var(--accent); font-weight: 600; }
  .small { font-size: 12.5px; margin: 2px 0 0; } .noaa { color: var(--text-quiet); } .warn { color: var(--accent); font-weight: 500; }
  .foot { margin: 6px 0 0; font-size: 12px; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 999px; padding: 0 8px; font-size: 11px; font-weight: 500; margin-left: 4px; }
</style>
