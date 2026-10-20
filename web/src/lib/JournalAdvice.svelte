<script>
  import { asOf } from './clock.svelte.js';
  let { advice, compact = false } = $props();
  const date = stamp => new Date(stamp).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
</script>
<details class="advice">
  <summary>Your journal · {advice.matched.length} comparable {advice.matched.length === 1 ? 'trip' : 'trips'}</summary>
  <div class="body">
    <p>{advice.rule}</p>
    {#if advice.current}<p class="quiet">{advice.current.value.toLocaleString()} {advice.flow ? `cfs · Latest flow, not a forecast · USGS ${advice.current.site_no}, provisional` : '°F air · NWS forecast'} · {asOf(advice.current.as_of)}</p>{/if}
    {#if !advice.ready}<p>Current comparison data is missing or stale. No journal adjustment.</p>
    {:else if !advice.matched.length}<p>No comparable trips yet. Log trips with conditions to build your history.</p>
    {:else}<p>{advice.successes} of {advice.matched.length} comparable trips have recorded catches. Trips without recorded catches are included.</p>{/if}
    <p class="quiet">All species; target fisheries were not recorded. This is your recorded history, not a catch probability or a validated fishing range. {advice.total - advice.matched.length} other trips here lack comparable conditions or outcomes.</p>
    {#if advice.eligible}<p>Optional journal adjustment: {advice.adjustment > 0 ? '+' : ''}{advice.adjustment} points. Based on trips with catches, reduced for small samples; capped at ±5.</p>
    {:else}<p>At least 3 comparable trips are needed to adjust rankings. Public score unchanged.</p>{/if}
    {#if advice.gear.length}<p><strong>Lures and flies with recorded catches</strong></p>
      {#each advice.gear as g}<p>{g.name}: {g.fish} fish recorded with it across {g.successes} of {g.trips} comparable trips where it was logged.</p>{/each}
    {/if}
    {#if advice.setups.length}<p><strong>Setups used on trips with catches</strong></p>
      {#each advice.setups as s}<p>{s.name}: used on {s.trips} comparable trips; {s.successes} had recorded catches.</p>{/each}
    {/if}
    {#if advice.gear.length || advice.setups.length}<p class="quiet">Consider these for your pack. Recorded use does not establish that the gear caused the result.</p>{/if}
    {#if advice.matched.length}
      <details><summary>Trips behind this comparison</summary>
        <ul>{#each advice.matched.slice(0, compact ? 5 : 20) as t (t.uuid)}<li>{date(t.started_at)} · {t.fish} fish recorded · {t.comparison_value.toLocaleString()} {advice.flow ? 'cfs, provisional' : '°F air'} · {asOf(t.comparison_as_of)}{t.dirty ? ' · Waiting to sync' : ''}</li>{/each}</ul>
        {#if advice.matched.length > (compact ? 5 : 20)}<p class="quiet">Showing the most recent {compact ? 5 : 20}; all {advice.matched.length} count in the comparison.</p>{/if}
      </details>
    {/if}
  </div>
</details>
<style>
  .advice{border-top:1px solid var(--hair);font-size:12.5px;}
  summary{min-height:44px;display:flex;align-items:center;cursor:pointer;color:var(--fresh-2);}
  .body{display:flex;flex-direction:column;gap:6px;padding-bottom:10px;}
  p{margin:0;overflow-wrap:anywhere;} ul{margin:0;padding-left:18px;} li{margin:4px 0;}
</style>
