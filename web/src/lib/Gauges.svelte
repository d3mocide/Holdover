<script>
  import { api, asOf, TREND } from './api.js';
  let gauges = $state([]);
  let note = $state('');
  let error = $state('');
  $effect(() => { api.gauges().then((r) => { gauges = r.gauges; note = r.note; }).catch((e) => (error = e.message)); });
</script>
<div class="page">
  <h1>Gauges</h1>
  <p class="quiet">{note || 'USGS values are provisional.'}</p>
  {#if error}<p role="alert">Couldn't load gauges ({error}).</p>{/if}
  <ul>
    {#each gauges as g (g.id)}
      <li class="card">
        <div class="top"><strong>{g.name}</strong>
          {#if g.stale}<span class="stale">Stale</span>{/if}</div>
        <div class="mono vals">
          <span>{g.values.discharge_cfs ? `${Math.round(g.values.discharge_cfs.value).toLocaleString()} cfs` : '—'}</span>
          {#if g.values.gage_height_ft}<span>{g.values.gage_height_ft.value} ft</span>{/if}
          {#if g.values.water_temp_f}<span>{Math.round(g.values.water_temp_f.value)}°F</span>{/if}
          {#if g.trend}<span>{TREND[g.trend]}</span>{/if}
        </div>
        <span class="quiet small">USGS {g.site_no} · provisional · {asOf(g.as_of)}</span>
      </li>
    {/each}
  </ul>
</div>
<style>
  .page { padding: 16px; max-width: 720px; height: 100%; overflow-y: auto; }
  h1 { font-size: 22px; } ul { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; }
  .top { display: flex; justify-content: space-between; gap: 8px; } .vals { display: flex; gap: 16px; margin: 4px 0; flex-wrap: wrap; }
  .small { font-size: 12px; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 0 6px; font-size: 12px; }
</style>
