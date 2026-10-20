<script>
  import Icon from './Icon.svelte';
  import { isFavorite } from './auth.svelte.js';
  import { FRESH_LABEL, FACTOR_LABEL } from './api.js';
  import { hhmm, clockText } from './clock.svelte.js';
  import { evidenceText } from './waterSearch.js';
  import JournalAdvice from './JournalAdvice.svelte';
  // A ranked list of spots for one day, each with a "why this score" breakdown.
  let { spots, fresh = {}, selectedId = null, onselect } = $props();
</script>

<ul>
  {#each spots as s (s.waterbody.id)}
    {@const f = fresh[s.waterbody.id]}
    <li class="spotli" class:sel={s.waterbody.id === selectedId}>
      <button class="spot" onclick={() => onselect(s.waterbody.id)}>
        <span class="mono rank">{s.rank}</span>
        <span class="body">
          <span class="name">{s.waterbody.name}{#if isFavorite(s.waterbody.id)} <span class="fav" title="Favorite"><Icon name="star_fill" size={14} /></span>{/if}</span>
          <span class="why small quiet">{clockText(s.explanation.text)}</span>
          <span class="small quiet">{evidenceText(s.coverage)} · share of scoring inputs backed by data</span>
          {#if s.personal}<span class="small quiet">Public {Math.round(s.public_score)} · journal {s.advice.adjustment > 0 ? '+' : ''}{s.advice.adjustment} points</span>{/if}
        </span>
        <span class="end">
          {#if f}<span class="dot {f.freshness}" title={FRESH_LABEL[f.freshness]}></span>{/if}
          <span class="mono score" class:hi={s.score >= 60} class:mid={s.score >= 45 && s.score < 60}>{s.personal ? s.score.toFixed(1) : Math.round(s.score)}</span>
        </span>
      </button>
      <details class="how">
        <summary class="small">Why this score</summary>
        <p class="small quiet">{s.explanation.source === 'llm' ? `Wording by a local model from the facts below, ${hhmm(s.explanation.as_of)}.` : 'Wording built directly from the facts below.'}
          {Math.round(s.coverage * 100)}% of the public score is backed by data; missing inputs count as neutral. {#if s.personal}The factors below add up to the public score of {s.public_score}; your optional journal adjustment is shown separately.{/if}</p>
        {#each s.factors as ft}
          {#if ft.applicable}
            <div class="frow small">
              <span class="fl">{FACTOR_LABEL[ft.name]}</span>
              <span class="bar" aria-hidden="true"><i style="width:{ft.value == null ? 50 : ft.value * 100}%" class:nodata={ft.value == null}></i></span>
              <span class="mono pts">{ft.points}</span>
              <span class="quiet fd">{ft.value == null ? 'no data (neutral)' : clockText(ft.detail)}</span>
            </div>
          {/if}
        {/each}
        {#if s.report_sentence}<p class="small quiet">ODFW: “{s.report_sentence}”</p>{/if}
      </details>
      {#if s.advice}<div class="personal"><JournalAdvice advice={s.advice} compact /></div>{/if}
    </li>
  {/each}
</ul>

<style>
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .small { font-size: 13px; margin: 0; }
  .spotli { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); transition: border-color 0.15s, background 0.15s; }
  .spotli:hover { background: rgba(255, 255, 255, 0.07); }
  .spotli.sel { border-color: var(--fresh-1); box-shadow: 0 0 0 1px var(--fresh-1); }
  .spot { width: 100%; justify-content: flex-start; align-items: flex-start; text-align: left; border: 0; background: none; padding: 8px 12px; gap: 10px; height: auto; }
  .rank { color: var(--text-quiet); min-width: 18px; padding-top: 2px; }
  .body { display: flex; flex-direction: column; flex: 1; min-width: 0; }
  .name { font-weight: 500; } .fav { color: var(--warn); display: inline-flex; vertical-align: -2px; }
  .why { white-space: pre-line; }
  .end { display: flex; align-items: center; gap: 8px; padding-top: 2px; }
  .score { font-size: 24px; font-weight: 600; line-height: 1; color: var(--text-quiet); }
  .score.hi { color: var(--fresh-1); } .score.mid { color: var(--fresh-2); }
  .how { padding: 0 12px 8px 40px; }
  .personal { padding: 0 12px; }
  .how summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; color: var(--text-quiet); }
  .frow { display: grid; grid-template-columns: 78px 1fr 40px; gap: 2px 8px; align-items: center; margin: 4px 0; }
  .fl { color: var(--text); } .pts { text-align: right; }
  .fd { grid-column: 1 / -1; }
  .bar { height: 6px; background: var(--line); border-radius: 3px; overflow: hidden; }
  .bar i { display: block; height: 100%; background: linear-gradient(90deg, var(--fresh-2), var(--fresh-1)); border-radius: 3px; } .bar i.nodata { background: var(--fresh-3); }
</style>
