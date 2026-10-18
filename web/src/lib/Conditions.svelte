<script>
  import Tile from './Tile.svelte';
  import Icon from './Icon.svelte';
  import { asOf, cToF, TREND } from './api.js';
  // level: the heading level for this block's section titles. A sheet titles itself with an h2, the day view with an h1,
  // so each passes the level that keeps the outline in order (no skipped levels).
  let { c, level = 3 } = $props();
  const w = $derived(c.weather?.day);
  const flowGauge = $derived(c.gauges.find((g) => g.values.discharge_cfs));
</script>

<div class="grid">
  <Tile icon="forecast" label="Forecast" value={w ? `${w.temp_f}°F` : null}
    sub={w ? `${w.short}${w.precip_pct != null ? `, ${w.precip_pct}% rain` : ''}, wind ${w.wind} ${w.wind_dir ?? ''}` : 'No forecast cached'}
    stale={c.weather?.stale} asof={c.weather ? `NWS ${asOf(c.weather.as_of)}` : ''} />
  <Tile icon="sun" label="Daylight" value={c.daylight ? `${c.daylight.sunrise}–${c.daylight.sunset}` : null}
    sub={c.daylight ? `Light ${c.daylight.first_light}–${c.daylight.last_light}` : 'No location'} asof="computed" />
  <Tile icon="temp" label="Water temp" value={c.water_temp_f ? `${Math.round(c.water_temp_f.value)}°F` : null}
    sub={c.water_temp_f ? 'USGS, provisional' : 'No temperature gauge'} asof={c.water_temp_f ? asOf(c.water_temp_f.observed_at) : ''} />
  <Tile icon="moon" label="Moon" value={c.moon.phase} sub={`Day ${c.moon.age_days} of cycle`} asof="computed" />
</div>

{#if c.gauges.length}
  <svelte:element this={`h${level}`} class="eyebrow head"><Icon name="flow" size={14} /> Flow</svelte:element>
  {#each c.gauges as g (g.id)}
    <div class="g">
      <span class="grow">{g.name}</span>
      <span class="mono">{g.values.discharge_cfs ? `${Math.round(g.values.discharge_cfs.value).toLocaleString()} cfs` : '—'}
        {#if g.values.gage_height_ft}· {g.values.gage_height_ft.value} ft{/if}</span>
      <span class="quiet small full">{g.trend ? TREND[g.trend] + ' (3 h) · ' : ''}Provisional USGS data, {asOf(g.as_of)} {#if g.stale}<b class="stale">Stale</b>{/if}</span>
    </div>
  {/each}
{/if}

{#if c.advisories.length}
  <div class="adv" role="note">
    <span class="advh"><Icon name="advisory" size={18} /></span>
    {#each c.advisories as a}<p><strong>{a.kind === 'algae:advisory' ? 'Algae advisory' : 'Algae precaution'}</strong> (OHA, issued {a.issued}). {a.text}</p>{/each}
    <a href={c.advisory_page} target="_blank" rel="noopener">OHA current advisories</a>
  </div>
{:else if c.waterbody_kind !== 'river'}
  <p class="quiet small">No algae advisory listed for this waterbody. Only some waters are monitored. <a href={c.advisory_page} target="_blank" rel="noopener">Check OHA</a>.</p>
{/if}

<style>
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .small { font-size: 13px; margin: 6px 0 0; }
  .g { display: flex; flex-wrap: wrap; gap: 4px 8px; padding: 6px 0; border-bottom: 1px solid var(--hair); }
  .grow { flex: 1; min-width: 140px; } .full { flex-basis: 100%; margin: 0; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 0 4px; }
  .head { display: flex; align-items: center; gap: 6px; margin-top: 10px; } .head :global(svg) { color: var(--fresh-2); }
  .adv { border: 1px solid var(--accent); border-radius: 14px; padding: 8px 12px; margin-top: 8px; background: color-mix(in srgb, var(--accent) 8%, transparent); }
  .advh { color: var(--accent); display: inline-flex; margin-bottom: 2px; }
  .adv p { margin: 0 0 4px; font-size: 14px; }
</style>
