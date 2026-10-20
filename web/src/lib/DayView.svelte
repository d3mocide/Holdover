<script>
  import { isoDay, longDate } from './api.js';
  import { hhmm } from './clock.svelte.js';
  import StockingList from './StockingList.svelte';
  import { loadDay } from './conditions.js';
  import Conditions from './Conditions.svelte';
  import { liveQuery } from 'dexie';
  import { db } from './db.js';
  import { ownedFor, ownedText } from './gearPack.js';
  import Icon from './Icon.svelte';
  import JournalAdvice from './JournalAdvice.svelte';
  import { journalAdvice, dayContext } from './journalAdvice.js';
  import { adviceState, adviceData } from './journalAdvice.svelte.js';
  let { id, fishery = 'trout', startOffset = 0, onback, onlog, onoffline } = $props();
  let offset = $state(startOffset);
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
    let active = true;
    d = null; error = '';
    loadDay(id, isoDay(offset), fishery).then((v) => { if (active) { d = v.data; source = v.source; asof = v.as_of; } }).catch((e) => { if (active) error = e.message; });
    return () => { active = false; };
  });
  const c = $derived(d?.conditions);
  const pack = $derived(d?.pack);
  const comparison = $derived(dayContext(c));
  const advice = $derived(d ? journalAdvice(d.waterbody, comparison, adviceData(), adviceState.now) : null);
  const packKey = $derived(`holdover.pack.${id}.${isoDay(offset)}.${fishery}`);
  let myGear = $state([]);
  $effect(() => { const sub = liveQuery(() => db.gear.toArray()).subscribe((v) => (myGear = v)); return () => sub.unsubscribe(); });
  let checked = $state({});
  $effect(() => { try { checked = JSON.parse(localStorage.getItem(packKey) || '{}'); } catch { checked = {}; } });
  const toggle = (itemId) => { checked = { ...checked, [itemId]: !checked[itemId] }; try { localStorage.setItem(packKey, JSON.stringify(checked)); } catch { /* storage blocked */ } };
  const groups = $derived(pack ? [...new Set(pack.items.map((i) => i.group))] : []);
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

  <div class="scroll">
  {#if error}
    <p role="alert">Couldn't load the day view ({error}).</p>
  {:else if c}
    <Conditions {c} level={2} />

    <StockingList stocking={c.stocking} level={2} />

    {#if c.report_items.length}
      <h2 class="eyebrow head">From the weekly report</h2>
      <ul class="facts">
        {#each c.report_items as r}
          <li>{r.note}{#if r.reviewed === false} <span class="aitag">AI-read, not yet reviewed</span>{/if} <span class="quiet small">ODFW report, {longDate(r.issued_on)}: “{r.source_sentence}”</span></li>
        {/each}
      </ul>
    {/if}
    <p class="quiet small">Facts only: this page doesn't state regulations.</p>
    <JournalAdvice {advice} />

    {#if pack}
      <h2 class="quiet small">Pack</h2>
      <p class="small">{pack.intro}</p>
      <p class="quiet small">{pack.intro_source === 'llm' ? 'Intro reworded by a local model. The checklist is a fixed template.' : 'Checklist is a fixed template for the season, fishery and forecast.'}</p>
      {#each groups as g}
        <fieldset class="pk"><legend class="small quiet">{g}</legend>
          {#each pack.items.filter((i) => i.group === g) as it (it.id)}
            <label class="ck"><input type="checkbox" checked={!!checked[it.id]} onchange={() => toggle(it.id)} /> <span class:done={checked[it.id]}>{it.label}{#if ownedText(ownedFor(it.id, myGear))}<span class="own">{ownedText(ownedFor(it.id, myGear))}</span>{/if}</span></label>
          {/each}
        </fieldset>
      {/each}
    {/if}

    <div class="note card" role="note">
      <a href={d.waterbody.regs_url} target="_blank" rel="noopener">Official regulations on ODFW <Icon name="external" /></a>
    </div>
  {:else}<p class="quiet">Loading…</p>{/if}
  </div>

  <div class="bar">
    <button class="primary" onclick={() => onlog(id)}>Log a trip here</button>
    <button onclick={() => onoffline(id, isoDay(offset))}>Prepare for offline</button>
  </div>
</section>

<style>
  .day { padding: 16px 16px 0; overflow: hidden; height: 100%; display: flex; flex-direction: column; gap: 10px; position: relative; }
  .scroll { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 8px; }
  header { display: flex; gap: 12px; align-items: center; } .grow { flex: 1; min-width: 0; }
  h1 { font-size: 20px; } .small { font-size: 13px; margin: 0; } .zone { text-transform: capitalize; }
  .badge { border: 1px solid var(--accent); color: var(--accent); border-radius: 999px; padding: 2px 10px; font-size: 12px; }
  .chips { display: flex; gap: 8px; flex-wrap: wrap; }
  .aitag { font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--text-quiet); border: 1px solid var(--hair); border-radius: 999px; padding: 1px 7px; white-space: nowrap; }
  .facts { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .pk { border: 0; padding: 0; margin: 0; } .pk legend { padding: 0; }
  .ck { display: flex; align-items: center; gap: 12px; min-height: 44px; color: var(--text); margin: 0; font-size: 14px; }
  .own { display: block; font-size: 12.5px; color: var(--fresh-2); }
  .ck { align-items: flex-start; padding: 6px 0; } .ck input { margin-top: 2px; }
  .ck input { width: 22px; height: 22px; accent-color: var(--accent); flex: none; } .done { text-decoration: line-through; color: var(--text-quiet); }
  .bar { flex: none; display: flex; gap: 8px; padding: 12px 0 16px; border-top: 1px solid var(--hair); }
  .bar button { flex: 1; }
</style>
