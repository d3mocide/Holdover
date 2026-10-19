<script>
  import Icon from './Icon.svelte';
  import { api, longDate, localDay } from './api.js';
  import { hhmm } from './clock.svelte.js';
  // The weekly ODFW Recreation Report, reposted as ODFW wrote it (nothing generated), one zone at a time.
  let { zone: appZone = 'willamette' } = $props();
  let data = $state(null);
  let error = $state('');
  let zone = $state('week');  // the tab: 'week' is the briefing; the rest are ODFW's report zones
  let brief = $state(null);
  let briefError = $state('');
  $effect(() => { const z = appZone; briefError = ''; api.briefing(z).then((v) => (brief = v)).catch((e) => (briefError = e.message)); });
  let issue = $state(null);
  $effect(() => {
    const d = issue;
    error = '';
    api.reportsAll(d).then((v) => { data = v; }).catch((e) => (error = e.message));
  });
  const current = $derived(data?.zones.find((z) => z.zone === zone));
</script>

<section class="panel" aria-label="Weekly reports">
  <header>
    <div class="row"><span class="ico"><Icon name="reports" size={26} /></span>
      <div><h1>Weekly <span class="ov">reports</span></h1>
        <p class="quiet small">{zone === 'week' ? `This week's briefing for the ${brief?.label ?? ''} zone, from the data Holdover gathers. Week of ${brief?.week_of ? longDate(brief.week_of) : '…'}.` : `ODFW's Recreation Report, in ODFW's own words.${data?.issued_on ? ` Issued ${longDate(data.issued_on)}.` : ''}`}</p></div>
    </div>
    {#if zone !== 'week' && data && data.available.length > 1}
      <label class="small" for="issue">Issue</label>
      <select id="issue" value={data.issued_on} onchange={(e) => (issue = e.currentTarget.value)}>
        {#each data.available as d}<option value={d}>{longDate(d)}</option>{/each}
      </select>
    {/if}
  </header>

  {#if error}<p class="notice" role="alert">Couldn't load the reports ({error}).</p>{/if}

  <div class="tabs" role="group" aria-label="Report">
    <button class="tab" aria-pressed={zone === 'week'} onclick={() => (zone = 'week')}>This week</button>
    {#if data}{#each data.zones as z (z.zone)}
      <button class="tab" aria-pressed={zone === z.zone} onclick={() => (zone = z.zone)}>{z.label}</button>
    {/each}{/if}
  </div>

  {#if zone === 'week'}
    {#if briefError}<p class="notice" role="alert">Couldn't load the briefing ({briefError}).</p>{/if}
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
        {:else}
          <ul class="facts">{#each s.facts as f}<li>{f}</li>{/each}</ul>
        {/if}
      </article>
    {:else}
      {#if brief}<p class="quiet">Nothing to report yet: the data sources are still loading.</p>{:else if !briefError}<p class="quiet">Loading…</p>{/if}
    {/each}
    {#if brief}<footer class="quiet small">{brief.note}</footer>{/if}
  {:else if data && data.zones.length}
    {#if current}
      <article>
        <h2 class="eyebrow">{current.label} zone</h2>
        {#each current.bullets as b}<p class="bullet">{b}</p>{:else}<p class="quiet">ODFW listed nothing for this zone this week.</p>{/each}
      </article>
    {/if}
    <footer class="quiet small">
      Source: Oregon Department of Fish &amp; Wildlife{data.fetched_at ? `, fetched ${localDay(data.fetched_at)}` : ''}.
      <a href={data.source_url} target="_blank" rel="noopener">Read the original report on ODFW <Icon name="external" size={14} /></a><br />
      Conditions change. This page does not state regulations: check ODFW's e-regulations before you fish.
    </footer>
  {:else if data}
    <p class="quiet">No report has been fetched yet. It is checked a few times on Wednesday to Friday, when ODFW publishes it.</p>
  {:else if !error}<p class="quiet">Loading…</p>{/if}
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; height: 100%; }
  header { display: flex; flex-direction: column; gap: 6px; }
  .row { display: flex; gap: 14px; align-items: center; }
  .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } .ov { color: var(--fresh-1); }
  .small { font-size: 13px; margin: 2px 0 0; }
  .tabs { display: flex; gap: 20px; border-bottom: 1px solid var(--hair); overflow-x: auto; flex: none; }
  .tab { flex: none; border: 0; border-bottom: 2px solid transparent; border-radius: 0; background: none; min-height: 44px; padding: 0 2px; margin-bottom: -1px; color: var(--text-quiet); font-weight: 500; }
  .tab[aria-pressed='true'] { color: var(--text); border-bottom-color: var(--accent); }
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
