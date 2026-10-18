<script>
  import { api, asOf, TREND } from './api.js';
  import Icon from './Icon.svelte';
  let gauges = $state([]);
  let note = $state('');
  let error = $state('');
  $effect(() => { api.gauges().then((r) => { gauges = r.gauges; note = r.note; }).catch((e) => (error = e.message)); });
</script>
<div class="page" tabindex="0" role="region" aria-label="Gauges">
  <header><span class="ico"><Icon name="gauge" size={26} /></span><div><h1>Gauges</h1><p class="quiet">{note || 'USGS values are provisional.'}</p></div></header>
  {#if error}<p role="alert">Couldn't load gauges ({error}).</p>{/if}
  <ul>
    {#each gauges as g (g.id)}
      <li class="card">
        <div class="top"><strong>{g.name}</strong>
          {#if g.stale}<span class="stale">Stale</span>{/if}</div>
        <div class="big mono">{g.values.discharge_cfs ? Math.round(g.values.discharge_cfs.value).toLocaleString() : '—'}<small> cfs</small></div>
        <div class="vals mono">
          {#if g.values.gage_height_ft}<span><Icon name="flow" size={14} /> {g.values.gage_height_ft.value} ft</span>{/if}
          {#if g.values.water_temp_f}<span><Icon name="temp" size={14} /> {Math.round(g.values.water_temp_f.value)}°F</span>{/if}
          {#if g.trend}<span class="trend">{TREND[g.trend]}</span>{/if}
        </div>
        <span class="quiet small">USGS {g.site_no} · provisional · {asOf(g.as_of)}</span>
      </li>
    {/each}
  </ul>
</div>
<style>
  .page { padding: 20px 16px 28px; height: 100%; overflow-y: auto; }
  header { display: flex; gap: 14px; align-items: center; margin-bottom: 16px; }
  .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--gauge); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } header p { margin: 2px 0 0; font-size: 13px; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 10px; }
  .top { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; } .top strong { font-weight: 500; line-height: 1.3; }
  .big { font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 10px 0 2px; color: var(--text); } .big small { font-size: 13px; color: var(--text-quiet); font-weight: 400; letter-spacing: 0; }
  .vals { display: flex; gap: 14px; margin: 2px 0 10px; flex-wrap: wrap; font-size: 13px; color: var(--text-quiet); }
  .vals span { display: inline-flex; align-items: center; gap: 5px; } .vals :global(svg) { color: var(--fresh-2); }
  .small { font-size: 12px; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 999px; padding: 0 8px; font-size: 11px; flex: none; }
</style>
