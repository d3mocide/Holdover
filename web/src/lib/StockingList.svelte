<script>
  import Icon from './Icon.svelte';
  import { FRESH_LABEL } from './api.js';
  import { hhmm } from './clock.svelte.js';
  import { stockingSections, weekLabelYear, split } from './stockingGroups.js';
  // The Stocking section of a waterbody: coming-up weeks first, then what was already stocked. Long lists show the first
  // few rows and keep the rest one tap away. `level` is the heading level, so the page outline stays in order.
  let { stocking, level = 3, asOfIso = null } = $props();
  const sections = $derived(stockingSections(stocking));
  const fish = (s) => [s.legals && `${s.legals.toLocaleString()} legals`, s.trophy && `${s.trophy.toLocaleString()} trophy`].filter(Boolean).join(' + ') || `${s.total.toLocaleString()} fish`;
</script>

{#if stocking.length}
<svelte:element this={`h${level}`} class="eyebrow head"><Icon name="stocking" size={14} /> Stocking</svelte:element>
{#each sections as sec (sec.key)}
  {@const { shown, rest } = split(sec.items)}
  <p class="sub">{sec.title}</p>
  <ul>
    {#each shown as s (s.week_of)}
      <li class="srow"><span class="dot {s.freshness}" title={FRESH_LABEL[s.freshness]}></span><span class="grow wk">{weekLabelYear(s.week_of)}</span>{#if s.freshness === 'upcoming'}<span class="tag">scheduled</span>{/if}<span class="fish">{fish(s)}</span></li>
    {/each}
  </ul>
  {#if rest.length}
    <details>
      <summary>Show {rest.length} more {sec.key === 'upcoming' ? 'scheduled' : 'earlier'} {rest.length === 1 ? 'week' : 'weeks'}</summary>
      <ul>
        {#each rest as s (s.week_of)}
          <li class="srow"><span class="dot {s.freshness}" title={FRESH_LABEL[s.freshness]}></span><span class="grow wk">{weekLabelYear(s.week_of)}</span>{#if s.freshness === 'upcoming'}<span class="tag">scheduled</span>{/if}<span class="fish">{fish(s)}</span></li>
        {/each}
      </ul>
    </details>
  {/if}
{:else}
  <p class="quiet small">No stocking in the last two weeks or scheduled.</p>
{/each}
<p class="quiet small note">Weeks, not days. The schedule can change without notice.{asOfIso ? ` As of ${hhmm(asOfIso)}.` : ''}</p>
{/if}  <!-- a river that has never been on ODFW's schedule gets no Stocking section at all -->

<style>
  .head { display: flex; align-items: center; gap: 6px; margin-top: 14px; } .head :global(svg) { color: var(--fresh-2); }
  .sub { margin: 8px 0 2px; font-size: 12.5px; color: var(--text-quiet); }
  ul { list-style: none; padding: 0; margin: 0; }
  .srow { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--hair); }
  .srow:last-child { border-bottom: 0; }
  .grow { flex: 1; min-width: 0; } .wk { white-space: nowrap; }
  .dot { width: 10px; height: 10px; border-radius: 50%; flex: none; border: 2px solid var(--fresh-1); box-sizing: border-box; }
  .dot.this_week { background: var(--fresh-1); } .dot.recent { background: var(--fresh-2); border-color: var(--fresh-2); } .dot.older { background: var(--fresh-3); border-color: var(--fresh-3); }
  .tag { font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--fresh-1); color: var(--fresh-1); }
  .fish { font-family: 'IBM Plex Mono', monospace; font-size: 13px; color: var(--text-quiet); white-space: nowrap; }
  details { margin: 2px 0 4px; } summary { cursor: pointer; color: var(--fresh-1); font-size: 13px; min-height: 44px; display: flex; align-items: center; }
  .note { margin: 8px 0 0; font-size: 12.5px; }
</style>
