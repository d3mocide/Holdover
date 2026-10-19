<script>
  import Tile from './Tile.svelte';
  import Icon from './Icon.svelte';
  import { cToF, TREND } from './api.js';
  import { asOf, clockText } from './clock.svelte.js';
  import { floodText, floodElevated } from './floodText.js';
  import { dangerText, fireLine } from './fireText.js';
  import { qualityReadings, readingStale, gaugeStale } from './gaugeText.js';
  import { rangeText, speciesLine, shownSpecies } from './passageText.js';
  // level: the heading level for this block's section titles. A sheet titles itself with an h2, the day view with an h1,
  // so each passes the level that keeps the outline in order (no skipped levels).
  let { c, level = 3 } = $props();
  const w = $derived(c.weather?.day);
  const flowGauge = $derived(c.gauges.find((g) => g.values.discharge_cfs));
  const r = $derived(c.reservoir);
  const ps = $derived(c.passage);
  const passed = $derived(shownSpecies(ps));
  const fd = $derived(c.fire?.danger);
  const fn = $derived(c.fire?.nearby);
  const fires = $derived(fn?.fires ?? []);
  // Only alerts are shown: no fire nearby, and ODF danger at Low (or no ODF zone here), say nothing.
  const fdNotable = $derived(!!fd?.covered && fd.level >= 2);
  const ft = (v) => (v == null ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)} ft`);
</script>

<div class="grid">
  <Tile icon="forecast" label="Forecast" value={w ? `${w.temp_f}°F` : null}
    sub={w ? `${w.short}${w.precip_pct != null ? `, ${w.precip_pct}% rain` : ''}, wind ${w.wind} ${w.wind_dir ?? ''}` : 'No forecast cached'}
    stale={c.weather?.stale} asof={c.weather ? `NWS ${asOf(c.weather.as_of)}` : ''} />
  <Tile icon="sun" label="Daylight" value={c.daylight ? clockText(`${c.daylight.sunrise}–${c.daylight.sunset}`) : null}
    sub={c.daylight ? clockText(`Light ${c.daylight.first_light}–${c.daylight.last_light}`) : 'No location'} asof="computed" />
  <Tile icon="temp" label="Water temp" value={c.water_temp_f ? `${Math.round(c.water_temp_f.value)}°F` : null}
    sub={c.water_temp_f ? 'USGS, provisional' : 'No temperature gauge'} stale={c.water_temp_f && readingStale(c.water_temp_f)} asof={c.water_temp_f ? asOf(c.water_temp_f.observed_at) : ''} />
  <Tile icon="moon" label="Moon" value={c.moon.phase} sub={`Day ${c.moon.age_days} of cycle`} asof="computed" />
</div>

{#if r}
  <svelte:element this={`h${level}`} class="eyebrow head"><Icon name="gauge" size={14} /> Reservoir level</svelte:element>
  <div class="g">
    <span class="grow">Pool elevation</span>
    <span class="mono">{r.elevation_ft.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ft</span>
    <span class="quiet small full">Past 24 h {ft(r.change_24h_ft)} · past 7 days {ft(r.change_7d_ft)}</span>
    {#if r.earlier_years.length}
      <span class="quiet small full">Same date: {r.earlier_years.map((y) => `${y.year} ${y.elevation_ft.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} ft`).join(' · ')}</span>
    {/if}
    <span class="quiet small full">Feet above sea level, unverified Army Corps data, {asOf(r.as_of)} {#if r.stale}<b class="stale">Stale</b>{/if}
      · <a href={r.page} target="_blank" rel="noopener">Corps water data</a></span>
  </div>
{/if}

{#if c.gauges.length}
  <svelte:element this={`h${level}`} class="eyebrow head"><Icon name="flow" size={14} /> Flow</svelte:element>
  {#each c.gauges as g (g.id)}
    <div class="g">
      <span class="grow">{g.name}</span>
      <span class="mono">{g.values.discharge_cfs ? `${Math.round(g.values.discharge_cfs.value).toLocaleString()} cfs` : '—'}
      </span>
      <span class="quiet small full">{g.trend ? TREND[g.trend] + ' (3 h) · ' : ''}Provisional USGS data, {asOf(g.values.discharge_cfs?.observed_at ?? g.as_of)} {#if gaugeStale(g)}<b class="stale">Stale</b>{/if}</span>
      {#if g.values.gage_height_ft}<span class="quiet small full">Gauge height: {g.values.gage_height_ft.value} ft · {asOf(g.values.gage_height_ft.observed_at)} {#if readingStale(g.values.gage_height_ft)}<b class="stale">Stale</b>{/if}</span>{/if}
      {#if g.values.water_temp_f}<span class="quiet small full">Water temperature: {g.values.water_temp_f.value}°F · {asOf(g.values.water_temp_f.observed_at)} {#if readingStale(g.values.water_temp_f)}<b class="stale">Stale</b>{/if}</span>{/if}
      {#each qualityReadings(g) as reading}<span class="quiet small full">{reading.text} · {asOf(reading.observed_at)} {#if readingStale(reading)}<b class="stale">Stale</b>{/if}</span>{/each}
      {#if g.flood}<span class="quiet small full" class:warn={floodElevated(g.flood)}>{floodText(g.flood)} · {asOf(g.flood.as_of)} {#if g.flood.stale}<b class="stale">Stale</b>{/if} · <a href={g.flood.page} target="_blank" rel="noopener">NOAA</a></span>{/if}
    </div>
  {/each}
{/if}

{#if ps && passed.length}
  <svelte:element this={`h${level}`} class="eyebrow head"><Icon name="fish" size={14} /> Fish passage</svelte:element>
  <div class="g">
    <span class="grow">{ps.project} fishway, {rangeText(ps)}</span>
    {#each passed as s}<span class="full small">{speciesLine(s)}</span>{/each}
    <span class="quiet small full">{ps.note}</span>
    <span class="quiet small full">ODFW counts, via <a href={ps.page} target="_blank" rel="noopener">Columbia River DART</a></span>
  </div>
{/if}

{#if fires.length || fdNotable}
  <svelte:element this={`h${level}`} class="eyebrow head"><Icon name="advisory" size={14} /> Fire</svelte:element>
  {#if fires.length}
    <div class="adv" role="note">
      <span class="advh"><Icon name="advisory" size={18} /></span>
      <p><strong>Active wildfire nearby</strong></p>
      {#each fires as f}<p>{fireLine(f)}</p>{/each}
      <p class="quiet small">A fire nearby does not by itself mean a closure. Check the land manager and <a href={fn.page} target="_blank" rel="noopener">Oregon wildfire information</a>. NIFC data, {asOf(fn.as_of)}.</p>
    </div>
  {/if}
  {#if fdNotable}
    <div class="g">
      <span class="grow">ODF fire danger</span>
      <span class="warn mono">{dangerText(fd)}</span>
      <span class="quiet small full">Oregon Department of Forestry, {asOf(fd.as_of)} · <a href={fd.page} target="_blank" rel="noopener">ODF fire restrictions and closures</a></span>
    </div>
  {/if}
{/if}

{#if c.advisories.length}
  <div class="adv" role="note">
    <span class="advh"><Icon name="advisory" size={18} /></span>
    {#each c.advisories as a}<p><strong>{a.kind === 'algae:advisory' ? 'Algae advisory' : 'Algae precaution'}</strong> (OHA, issued {a.issued}). {a.text}</p>{/each}
    <a href={c.advisory_page} target="_blank" rel="noopener">OHA current advisories</a>
  </div>
{/if}

<style>
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .small { font-size: 13px; margin: 6px 0 0; }
  .g { display: flex; flex-wrap: wrap; gap: 4px 8px; padding: 6px 0; border-bottom: 1px solid var(--hair); }
  .grow { flex: 1; min-width: 140px; } .full { flex-basis: 100%; margin: 0; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 0 4px; }
  .head { display: flex; align-items: center; gap: 6px; margin-top: 10px; } .head :global(svg) { color: var(--fresh-2); }
  .warn { color: var(--accent); font-weight: 500; }
  .adv { border: 1px solid var(--accent); border-radius: 14px; padding: 8px 12px; margin-top: 8px; background: color-mix(in srgb, var(--accent) 8%, transparent); }
  .advh { color: var(--accent); display: inline-flex; margin-bottom: 2px; }
  .adv p { margin: 0 0 4px; font-size: 14px; }
</style>
