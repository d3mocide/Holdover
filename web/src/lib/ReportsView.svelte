<script>
  import Icon from './Icon.svelte';
  import { api, longDate, localDay } from './api.js';
  import { hhmm } from './clock.svelte.js';
  // This zone's weekly report: a briefing built from the data Holdover gathers, ending with ODFW's own words for the zone.
  let { zone = 'willamette' } = $props();
  const sourceUrl = 'https://myodfw.com/recreation-report';
  let brief = $state(null);
  let briefError = $state('');
  $effect(() => { const z = zone; briefError = ''; api.briefing(z).then((v) => (brief = v)).catch((e) => (briefError = e.message)); });
</script>

<section class="panel" aria-label="Weekly report">
  <header>
    <div class="row"><span class="ico"><Icon name="reports" size={26} /></span>
      <div><h1>Weekly <span class="ov">report</span></h1>
        <p class="quiet small">The {brief?.label ?? ''} zone, week of {brief?.week_of ? longDate(brief.week_of) : '…'}. Built from the data Holdover gathers, ending with ODFW's own words.</p></div>
    </div>
  </header>

  {#if briefError}<p class="notice" role="alert">Couldn't load the report ({briefError}).</p>{/if}
  {#each brief?.sections ?? [] as s (s.key)}
    <article class="sec">
      <h2 class="eyebrow">{s.title}</h2>
      {#if s.narrated}
        <p class="para">{s.text}</p>
        <details><summary class="small cap">AI-written {hhmm(s.as_of)}, {localDay(s.as_of)} · the facts behind it</summary>
          <p class="quiet small">Written by {s.model} from these facts only and checked against them.</p>
          <ul class="facts">{#each s.facts as f}<li>{f}</li>{/each}</ul></details>
      {:else if s.key === 'report'}
        {#each s.facts as f}<p class="bullet">{f}</p>{/each}
        <p class="quiet small">Source: Oregon Department of Fish &amp; Wildlife. <a href={sourceUrl} target="_blank" rel="noopener">Read the original report on ODFW <Icon name="external" size={14} /></a></p>
      {:else}
        <ul class="facts">{#each s.facts as f}<li>{f}</li>{/each}</ul>
      {/if}
    </article>
  {:else}
    {#if brief}<p class="quiet">Nothing to report yet: the data sources are still loading.</p>{:else if !briefError}<p class="quiet">Loading…</p>{/if}
  {/each}
  {#if brief}<footer class="quiet small">{brief.note}</footer>{/if}
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; height: 100%; }
  header { display: flex; flex-direction: column; gap: 6px; }
  .row { display: flex; gap: 14px; align-items: center; }
  .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } .ov { color: var(--fresh-1); }
  .small { font-size: 13px; margin: 2px 0 0; }
  article { display: flex; flex-direction: column; gap: 6px; }
  .sec { padding-bottom: 6px; border-bottom: 1px solid var(--hair); } .sec:last-of-type { border-bottom: 0; }
  .para { margin: 0; font-size: 15.5px; line-height: 1.6; }
  .facts { list-style: disc; margin: 6px 0 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; font-size: 14px; line-height: 1.5; }
  .cap { font-size: 12.5px; }
  details summary { cursor: pointer; min-height: 44px; display: flex; align-items: center; color: var(--text-quiet); }
  article h2 { margin: 6px 0 2px; }
  .bullet { margin: 0; padding: 12px 14px; background: var(--glass-fill); border: 1px solid var(--hair); border-radius: 14px; line-height: 1.5; }
  .notice { background: var(--glass-fill); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; margin: 0; }
  footer { margin-top: auto; padding-top: 8px; line-height: 1.6; }
</style>
