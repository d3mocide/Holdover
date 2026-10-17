<script>
  import { isoDay, longDate, weekLabel, hhmm } from './api.js';
  import { loadDay } from './conditions.js';
  import Conditions from './Conditions.svelte';
  import Icon from './Icon.svelte';
  let { id, onback, onlog, onoffline } = $props();
  let offset = $state(0);
  let d = $state(null);
  let error = $state('');
  let source = $state('live');
  let asof = $state(null);
  let online = $state(typeof navigator === 'undefined' ? true : navigator.onLine);
  $effect(() => {
    const up = () => (online = true), down = () => (online = false);
    addEventListener('online', up); addEventListener('offline', down);
    return () => { removeEventListener('online', up); removeEventListener('offline', down); };
  });
  $effect(() => {
    d = null; error = '';
    loadDay(id, isoDay(offset)).then((v) => { d = v.data; source = v.source; asof = v.as_of; }).catch((e) => (error = e.message));
  });
  const c = $derived(d?.conditions);
</script>

<section class="day" aria-label="Day-of view">
  <header>
    <button onclick={onback} aria-label="Back"><Icon name="close" /></button>
    <div class="grow">
      <h1>{d?.waterbody.name ?? 'Loading…'}</h1>
      <p class="quiet small zone">{longDate(isoDay(offset))} · {d?.waterbody.zone ?? ''}</p>
    </div>
    {#if !online || source === 'cached'}<span class="badge">Cached{asof ? ` ${hhmm(asof)}` : ''}</span>{/if}
  </header>
  <div class="chips" role="group" aria-label="Day">
    {#each [['Today', 0], ['Tomorrow', 1], ['In 2 days', 2]] as [l, o]}
      <button class="chip" aria-pressed={offset === o} onclick={() => (offset = o)}>{l}</button>
    {/each}
  </div>

  {#if error}
    <p role="alert">Couldn't load the day view ({error}).</p>
  {:else if c}
    <Conditions {c} />

    <h2 class="quiet small">What to expect</h2>
    <ul class="facts">
      {#each c.stocking as s}
        <li><span class="dot {s.freshness}"></span> {weekLabel(s.week_of)}{s.freshness === 'upcoming' ? ' (scheduled)' : ''}:
          <span class="mono">{s.legals.toLocaleString()} legals{s.trophy ? ` + ${s.trophy.toLocaleString()} trophy` : ''}</span></li>
      {:else}
        <li class="quiet">No stocking in the last two weeks or scheduled.</li>
      {/each}
      {#each c.report_items as r}
        <li>{r.note} <span class="quiet small">ODFW report, {longDate(r.issued_on)}: “{r.source_sentence}”</span></li>
      {/each}
    </ul>
    <p class="quiet small">Stocking is by week and the schedule may change. Facts only: this page doesn't state regulations.</p>

    <div class="note card" role="note">
      <a href={d.waterbody.regs_url} target="_blank" rel="noopener">Official regulations on ODFW <Icon name="external" /></a>
    </div>
  {:else}<p class="quiet">Loading…</p>{/if}

  <div class="bar">
    <button class="primary" onclick={() => onlog(id)}>Log a trip here</button>
    <button onclick={() => onoffline(id)}>Prepare for offline</button>
  </div>
</section>

<style>
  .day { padding: 16px 16px 96px; overflow-y: auto; height: 100%; max-width: 720px; display: flex; flex-direction: column; gap: 10px; position: relative; }
  header { display: flex; gap: 12px; align-items: center; } .grow { flex: 1; min-width: 0; }
  h1 { font-size: 20px; } .small { font-size: 13px; margin: 0; } .zone { text-transform: capitalize; }
  .badge { border: 1px solid var(--accent); color: var(--accent); border-radius: 999px; padding: 2px 10px; font-size: 12px; }
  .chips { display: flex; gap: 8px; flex-wrap: wrap; }
  .facts { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .bar { position: sticky; bottom: 0; display: flex; gap: 8px; padding: 12px 0; background: var(--bg); margin-top: auto; }
  .bar button { flex: 1; }
</style>
