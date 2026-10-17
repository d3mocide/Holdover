<script>
  import { FRESH_LABEL, weekLabel, hhmm } from './api.js';
  let { data, error, selectedId, onselect, onreview, canReview } = $props();

  const order = { this_week: 0, recent: 1, upcoming: 2, older: 3 };
  const spots = $derived(
    (data?.features ?? []).map((f) => f.properties)
      .sort((a, b) => order[a.freshness] - order[b.freshness] || (b.last_total ?? b.next_total ?? 0) - (a.last_total ?? a.next_total ?? 0))
  );
  const unlocated = $derived(data?.meta.needs_coords ?? []);
</script>

<section class="panel" aria-label="Stocked waterbodies">
  <header>
    <div class="row">
      <h1>Holdover</h1>
      <span class="quiet mono small">{data?.meta.as_of ? `Synced ${hhmm(data.meta.as_of)}` : 'Not synced'}</span>
    </div>
    <p class="quiet small">Willamette zone · Stocked trout</p>
  </header>

  {#if error}
    <p class="notice" role="alert">Couldn't load stocking data ({error}).</p>
  {/if}

  <h2 class="small quiet">{spots.length} waterbodies with stocking</h2>
  <ul>
    {#each spots as s (s.id)}
      <li>
        <button class="spot" class:sel={s.id === selectedId} onclick={() => onselect(s.id)}>
          <span class="dot {s.freshness}" title={FRESH_LABEL[s.freshness]}></span>
          <span class="body">
            <span class="name">{s.name}</span>
            <span class="quiet small">
              {#if s.last_week}{weekLabel(s.last_week)}{:else}Scheduled {weekLabel(s.next_week).toLowerCase()}{/if}
              {#if s.last_week && s.next_week} · next {weekLabel(s.next_week).replace('Week of ', '')}{/if}
            </span>
          </span>
          <span class="mono count">{(s.last_total ?? s.next_total).toLocaleString()}</span>
        </button>
      </li>
    {/each}
  </ul>

  {#if unlocated.length}
    <details>
      <summary class="small">{unlocated.length} stocked, no map location yet</summary>
      <ul class="plain small">
        {#each unlocated as u (u.id)}<li>{u.name} <span class="quiet">· {weekLabel(u.last_week ?? u.next_week)}</span></li>{/each}
      </ul>
    </details>
  {/if}
  {#if data?.meta.unconfirmed_aliases}
    <p class="notice small">
      {data.meta.unconfirmed_aliases} stocking label(s) need review and are not shown.
      {#if canReview}<button class="linkish" onclick={onreview}>Review</button>{/if}
    </p>
  {/if}

  <footer class="quiet small">Stocking is shown by week. The schedule may change without notice.</footer>
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  h1 { font-size: 20px; } h2 { font-weight: 500; }
  .small { font-size: 13px; margin: 0; }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; flex: 1 1 auto; min-height: 120px; }
  ul.plain { flex: none; min-height: 0; }
  .spot { width: 100%; justify-content: flex-start; text-align: left; border-radius: 12px; padding: 8px 12px; gap: 12px; height: auto; }
  .spot.sel { border-color: var(--fresh-2); }
  .body { display: flex; flex-direction: column; flex: 1; min-width: 0; }
  .name { font-weight: 500; }
  .count { font-size: 14px; }
  .notice { background: var(--surface); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; margin: 0; }
  .plain { padding: 8px 0 0 16px; list-style: disc; display: block; }
  summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0 4px; }
  footer { margin-top: auto; padding-top: 8px; }
</style>
