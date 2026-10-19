<script>
  import { api, localDay } from './api.js';
  import { hhmm, asOf } from './clock.svelte.js';
  import { chartLines } from './gaugeChart.js';
  let { gauges = [] } = $props();
  let selected = $state(''), parameter = $state('discharge_cfs'), hours = $state(168);
  let data = $state(null), error = $state('');
  const gaugeId = $derived(selected || String(gauges[0]?.id ?? ''));
  $effect(() => {
    if (!gaugeId) return;
    let active = true; data = null; error = '';
    api.gaugeHistory(gaugeId, hours).then((d) => { if (active) data = d; }).catch((e) => { if (active) error = e.message; });
    return () => { active = false; };
  });
  const series = $derived(data?.series[parameter]);
  const chart = $derived(chartLines(series?.points ?? []));
  const label = $derived(parameter === 'discharge_cfs' ? 'Flow' : 'Water temperature');
  const summary = $derived(chart.rows.length ? `${label}: ${chart.min.toLocaleString()} to ${chart.max.toLocaleString()} ${series.unit}, ${chart.rows.length} observations` : 'No observations stored for this period');
</script>

<section class="history" aria-label="River history">
  <h3>River history</h3>
  {#if gauges.length}
    <div class="controls">
      <label for="history-gauge">Gauge<select id="history-gauge" aria-label="Gauge" bind:value={selected}><option value="">{gauges[0].name}</option>{#each gauges.slice(1) as g}<option value={String(g.id)}>{g.name}</option>{/each}</select></label>
      <label for="history-measurement">Measurement<select id="history-measurement" aria-label="Measurement" bind:value={parameter}><option value="discharge_cfs">Flow</option><option value="water_temp_c">Water temperature</option></select></label>
    </div>
    <div class="chips" role="group" aria-label="History period">
      <button aria-pressed={hours === 24} onclick={() => (hours = 24)}>24 hours</button>
      <button aria-pressed={hours === 168} onclick={() => (hours = 168)}>7 days</button>
    </div>
    {#if error}<p class="quiet small" role="status">History unavailable ({error}). Previously loaded charts work offline.</p>
    {:else if !data}<p class="quiet small">Loading observations…</p>
    {:else if chart.rows.length}
      <p class="small">{summary}</p>
      <svg viewBox="0 0 400 144" role="img" aria-label={summary}>
        <path class="axis" d="M12 8V132H388" />
        {#each chart.lines as line}<polyline points={line} />{/each}
      </svg>
      <p class="quiet small range">{localDay(chart.rows[0].observed_at)} {hhmm(chart.rows[0].observed_at)} – {localDay(chart.rows.at(-1).observed_at)} {hhmm(chart.rows.at(-1).observed_at)}</p>
      <details><summary>Read recent values</summary><ul>{#each chart.rows.slice(-12).reverse() as point}<li>{localDay(point.observed_at)} {hhmm(point.observed_at)} · {point.value.toLocaleString()} {series.unit}</li>{/each}</ul></details>
      <p class="quiet small">USGS, provisional · latest observation {asOf(chart.rows.at(-1).observed_at)}{Date.now() - Date.parse(chart.rows.at(-1).observed_at) > 3 * 3600000 ? ' · Stale' : ''}. Gaps are left blank.</p>
    {:else}<p class="quiet small">No {label.toLowerCase()} observations stored for this period.</p>{/if}
    <p class="quiet small">Recent flow comparisons use stored readings from the past 7 days. They are not a seasonal normal or a validated fishing range.</p>
    <a href={`https://waterdata.usgs.gov/monitoring-location/${gauges.find((g) => String(g.id) === gaugeId)?.site_no ?? gauges[0].site_no}/`} target="_blank" rel="noopener">USGS gauge data</a>
  {:else}<p class="quiet small">No linked gauge for this river yet.</p>{/if}
</section>

<style>
  .history { border: 1px solid var(--hair); background: var(--glass-fill); border-radius: 14px; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
  h3 { margin: 0; font-size: 16px; } .small { margin: 0; font-size: 12.5px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; } label { flex: 1 1 160px; min-width: 0; font-size: 12px; }
  select { display: block; width: 100%; min-height: 44px; margin-top: 4px; }
  .chips { display: flex; gap: 8px; } button { min-height: 44px; }
  svg { width: 100%; height: auto; overflow: visible; } polyline { fill: none; stroke: var(--gauge); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .axis { fill: none; stroke: var(--hair); stroke-width: 1; } .range { line-height: 1.5; }
  summary, a { min-height: 44px; display: flex; align-items: center; } ul { margin: 0; padding-left: 18px; font-size: 12.5px; }
</style>
