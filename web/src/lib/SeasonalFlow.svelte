<script>
  import { api, isoDay, longDate, localDay } from './api.js';
  import { asOf } from './clock.svelte.js';
  import { seasonalChart, baselineStale, flowStale } from './seasonalChart.js';
  import Icon from './Icon.svelte';
  let { data = null, gauges = [], date = isoDay() } = $props();
  let selected = $state(''), open = $state(false), full = $state(null), error = $state(''), now = $state(Date.now());
  const field = $props.id();
  const gaugeId = $derived(selected || String(data?.gauge?.id ?? gauges[0]?.id ?? ''));
  const seed = $derived(data ?? gauges.find(g => String(g.id) === gaugeId)?.seasonal ?? null);
  $effect(() => { const timer = setInterval(() => { now = Date.now(); }, 60000); return () => clearInterval(timer); });
  $effect(() => {
    const initial = seed, id = gaugeId, day = date, expanded = open; let active = true;
    full = initial; error = '';
    if (expanded && id && !initial?.series?.length && !['disabled', 'pending', 'unavailable'].includes(initial?.status)) {
      api.seasonalFlow(id, day).then(v => { if (active) full = v; }).catch(() => { if (active) error = 'No saved seasonal chart for this gauge and date. Connect to load it.'; });
    }
    return () => { active = false; };
  });
  const d = $derived(full ?? seed);
  const stale = $derived(baselineStale(d, now));
  const currentStale = $derived(flowStale(d?.current, now));
  const chart = $derived(seasonalChart(d));
  const position = $derived(!stale && !currentStale ? d?.current?.position : null);
  const summary = $derived(position ? `Latest flow ${position}` : d?.status === 'ready' ? 'Historical baseline available' : 'Historical baseline unavailable');
</script>

{#if gaugeId}
<div class="seasonal" role="group" aria-label="Seasonal flow context">
  <details bind:open>
    <summary><span><strong>Seasonal flow context</strong><span class="quiet small">{summary}</span></span><span class="chev"><Icon name="trend_steady" size={16} /></span></summary>
    <div class="body">
      {#if gauges.length > 1}<label for={field}>Seasonal gauge<select id={field} aria-label="Seasonal gauge" bind:value={selected}><option value="">{gauges[0].name}</option>{#each gauges.slice(1) as g}<option value={String(g.id)}>{g.name}</option>{/each}</select></label>{/if}
      {#if error}<p class="quiet small" role="status">{error}</p>{/if}
      {#if !d}{#if !error}<p class="quiet small">Loading seasonal context…</p>{/if}
      {:else if d.status === 'disabled'}<p class="quiet small">Historical downloads are disabled. The server owner can configure a USGS API key to build seasonal baselines. Live flow still works.</p>
      {:else if d.status === 'pending'}<p class="quiet small">Historical data has not been downloaded for this gauge yet. Baselines build gradually in the background.</p>
      {:else if d.status === 'unavailable'}<p class="quiet small">Historical data could not be loaded for this gauge. The server will retry; live flow still works.</p>
      {:else}
        <p class="small">{d.gauge.name} · USGS {d.gauge.site_no}</p>
        <p class="small">{d.start_year}–{d.end_year} approved daily mean flows. Each calendar date pools a 15-day window (±7 days) across these years.</p>
        <p class="quiet small">USGS retrieved {localDay(d.as_of)} {asOf(d.as_of)}{stale ? ' · Stale baseline' : ''}.</p>
        {#if d.selected}<p class="small">{longDate(date)}: {d.selected.samples}/{d.selected.expected} daily values · {d.selected.years.length} years represented.
          {#if d.selected.median != null}Median {d.selected.median.toLocaleString()} cfs; middle 50% {d.selected.p25.toLocaleString()}–{d.selected.p75.toLocaleString()} cfs.
          {:else}Not enough coverage for a comparison (needs 75 daily values across 5 years).{/if}</p>{/if}
        {#if d.series?.length && chart.lines.length}
          <svg viewBox="0 0 400 160" role="img" aria-label="Historical daily mean flow: median line and middle 50 percent band; a single dot marks the latest observation when available.">
            <path class="axis" d="M12 16V144H388" />
            {#each chart.bands as points}<polygon {points} />{/each}
            {#each chart.lines as points}<polyline {points} />{/each}
            {#if chart.dot}<circle cx={chart.dot.x} cy={chart.dot.y} r="4" />{/if}
          </svg>
          <p class="quiet small">Line: historical median · Band: middle 50% · Dot: latest observation. Scale 0–{Math.ceil(chart.max).toLocaleString()} cfs.</p>
          <p class="quiet small">{longDate(d.series[0].date)} – {longDate(d.series.at(-1).date)}. Missing or insufficient days are left blank.</p>
        {/if}
        {#if d.current}<p class="small">Latest: {d.current.value.toLocaleString()} cfs · USGS, provisional · {localDay(d.current.observed_at)} {asOf(d.current.observed_at)}{currentStale ? ' · Stale reading' : ''}.
          {#if position}{position} for {longDate(d.current.date)}.{/if}</p>
        {:else}<p class="quiet small">No current discharge reading is stored for this gauge.</p>{/if}
        <p class="quiet small">An instantaneous reading is being compared with historical daily means; short peaks can differ. The dot is an observation, not a forecast. Calendar comparisons use Pacific time.</p>
        {#if d.series?.length}<details><summary>Read historical values and coverage</summary><ul>{#each d.series as row}<li>{longDate(row.date)} · {row.median == null ? 'Insufficient coverage' : `${row.p25.toLocaleString()} / ${row.median.toLocaleString()} / ${row.p75.toLocaleString()} cfs (25th / median / 75th)`} · {row.samples}/{row.expected} values, {row.years.length} years</li>{/each}</ul></details>{/if}
      {/if}
      <p class="quiet small">Informational context only. This is not a validated fishing range or a prediction of catches. Seasonal context does not change the fishing score.</p>
      <a href={`https://waterdata.usgs.gov/monitoring-location/USGS-${d?.gauge?.site_no ?? gauges.find(g => String(g.id) === gaugeId)?.site_no}/`} target="_blank" rel="noopener">Official USGS gauge data</a>
    </div>
  </details>
</div>
{/if}

<style>
  .seasonal{background:var(--glass-fill);border:1px solid var(--hair);border-radius:14px;padding:0 12px;}
  summary{min-height:44px;display:flex;align-items:center;justify-content:space-between;gap:8px;cursor:pointer;padding:6px 0;color:var(--fresh-2);}
  .chev{flex:none;transform:rotate(90deg);} .seasonal>details[open]>summary .chev{transform:rotate(-90deg);}
  summary span{display:flex;flex-direction:column;gap:3px;} .body{display:flex;flex-direction:column;gap:8px;padding-bottom:12px;}
  p{margin:0;overflow-wrap:anywhere;} .small{font-size:12.5px;} label{font-size:12.5px;} select{display:block;width:100%;min-height:44px;}
  svg{width:100%;height:auto;} polygon{fill:var(--fresh-3);fill-opacity:.3;} polyline{fill:none;stroke:var(--gauge);stroke-width:2;}
  circle{fill:var(--accent);stroke:var(--text);stroke-width:1;} .axis{fill:none;stroke:var(--hair);}
  ul{padding-left:18px;margin:0;font-size:12px;} li{margin:6px 0;}
  a{display:flex;align-items:center;min-height:44px;font-size:12.5px;}
</style>
