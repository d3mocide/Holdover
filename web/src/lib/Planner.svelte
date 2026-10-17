<script>
  import { FRESH_LABEL, weekLabel, hhmm, longDate, dayLabel, FISHERIES, FACTOR_LABEL } from './api.js';
  let { data, report, spots, offset, fishery, onoffset, onfishery, spotsError, selectedId, error, onselect, onreview, canReview } = $props();
  const rep = $derived(report?.report);
  const unlocated = $derived(data?.meta.needs_coords ?? []);
  const fresh = $derived(Object.fromEntries((data?.features ?? []).filter((f) => f.properties.layer === 'stocking').map((f) => [f.properties.id, f.properties])));
  const days = [0, 1, 2, 3, 4];
</script>

<section class="panel" aria-label="Ranked spots">
  <header>
    <div class="row">
      <h1>Holdover</h1>
      <span class="quiet mono small">{data?.meta.as_of ? `Synced ${hhmm(data.meta.as_of)}` : 'Not synced'}</span>
    </div>
    <p class="quiet small">Willamette zone</p>
    <div class="chips" role="group" aria-label="Day">
      {#each days as o}<button class="chip accent" aria-pressed={offset === o} onclick={() => onoffset(o)}>{dayLabel(o)}</button>{/each}
    </div>
    <div class="chips" role="group" aria-label="Fishery">
      {#each FISHERIES as [k, label]}<button class="chip" aria-pressed={fishery === k} onclick={() => onfishery(k)}>{label}</button>{/each}
    </div>
  </header>

  {#if error}<p class="notice" role="alert">Couldn't load map data ({error}).</p>{/if}

  {#if rep}
    <details class="report">
      <summary class="small"><strong>From the weekly report</strong> · {longDate(rep.issued_on)}</summary>
      {#if rep.digest}
        <p class="digest">{rep.digest.text}</p>
        <p class="quiet small">Summary generated {hhmm(rep.digest.as_of)} by a local model from the report text. Check the original wording.</p>
      {/if}
      <p class="small quiet">{rep.digest ? 'Original ODFW wording' : 'ODFW wording (no summary yet)'}</p>
      {#each rep.bullets as b}<p class="small bullet">{b}</p>{/each}
      <a class="small" href={rep.source_url} target="_blank" rel="noopener">Read the original report on ODFW</a>
      {#if rep.pending_review && canReview}<p class="quiet small">{rep.pending_review} item(s) awaiting your review. <button class="linkish" onclick={onreview}>Review</button></p>{/if}
    </details>
  {/if}

  <h2 class="small quiet">{spots ? `${spots.spots.length} spots ranked` : 'Ranking…'}</h2>
  {#if spotsError}<p class="notice" role="alert">Couldn't rank spots ({spotsError}).</p>{/if}
  <ul>
    {#each spots?.spots ?? [] as s (s.waterbody.id)}
      {@const f = fresh[s.waterbody.id]}
      <li class="spotli" class:sel={s.waterbody.id === selectedId}>
        <button class="spot" onclick={() => onselect(s.waterbody.id)}>
          <span class="mono rank">{s.rank}</span>
          <span class="body">
            <span class="name">{s.waterbody.name}</span>
            <span class="why small quiet">{s.explanation.text}</span>
          </span>
          <span class="end">
            {#if f}<span class="dot {f.freshness}" title={FRESH_LABEL[f.freshness]}></span>{/if}
            <span class="mono score">{Math.round(s.score)}</span>
          </span>
        </button>
        <details class="how">
          <summary class="small">Why this score</summary>
          <p class="small quiet">{s.explanation.source === 'llm' ? `Wording by a local model from the facts below, ${hhmm(s.explanation.as_of)}.` : 'Wording built directly from the facts below.'}
            {Math.round(s.coverage * 100)}% of the score is backed by data; missing inputs count as neutral.</p>
          {#each s.factors as ft}
            {#if ft.applicable}
              <div class="frow small">
                <span class="fl">{FACTOR_LABEL[ft.name]}</span>
                <span class="bar" aria-hidden="true"><i style="width:{ft.value == null ? 50 : ft.value * 100}%" class:nodata={ft.value == null}></i></span>
                <span class="mono pts">{ft.points}</span>
                <span class="quiet fd">{ft.value == null ? 'no data (neutral)' : ft.detail}</span>
              </div>
            {/if}
          {/each}
          {#if s.report_sentence}<p class="small quiet">ODFW: “{s.report_sentence}”</p>{/if}
        </details>
      </li>
    {/each}
  </ul>
  {#if spots && !spots.spots.length}<p class="quiet small">Nothing matches this fishery and date yet. Stocking is the main trout signal; steelhead and warmwater lists grow as you accept report items.</p>{/if}

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

  <footer class="quiet small">Stocking is shown by week and the schedule may change. Scores are starting points, not validated. Check ODFW for regulations.</footer>
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  h1 { font-size: 20px; } h2 { font-weight: 500; }
  .small { font-size: 13px; margin: 0; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .chip { padding: 0 12px; min-height: 44px; font-size: 13px; }
  .chip.accent[aria-pressed='true'] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  ul.plain { display: block; list-style: disc; padding: 8px 0 0 16px; }
  .spotli { border: 1px solid var(--line); border-radius: 12px; background: var(--surface); }
  .spotli.sel { border-color: var(--fresh-2); }
  .spot { width: 100%; justify-content: flex-start; align-items: flex-start; text-align: left; border: 0; background: none; padding: 8px 12px; gap: 10px; height: auto; }
  .rank { color: var(--text-quiet); min-width: 18px; padding-top: 2px; }
  .body { display: flex; flex-direction: column; flex: 1; min-width: 0; }
  .name { font-weight: 500; }
  .why { white-space: pre-line; }
  .end { display: flex; align-items: center; gap: 8px; padding-top: 2px; }
  .score { font-size: 16px; font-weight: 500; }
  .how { padding: 0 12px 8px 40px; }
  .how summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; color: var(--text-quiet); }
  .frow { display: grid; grid-template-columns: 78px 1fr 40px; gap: 2px 8px; align-items: center; margin: 4px 0; }
  .fl { color: var(--text); } .pts { text-align: right; }
  .fd { grid-column: 1 / -1; }
  .bar { height: 6px; background: var(--line); border-radius: 3px; overflow: hidden; }
  .bar i { display: block; height: 100%; background: var(--fresh-2); } .bar i.nodata { background: var(--fresh-3); }
  .report { border: 1px solid var(--line); border-radius: 12px; padding: 4px 12px; background: var(--surface); }
  .report summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; }
  .digest { margin: 4px 0; } .bullet { margin: 6px 0; } .report p { margin: 4px 0; }
  .notice { background: var(--surface); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; margin: 0; }
  summary { cursor: pointer; }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0 4px; }
  footer { margin-top: auto; padding-top: 8px; }
</style>
