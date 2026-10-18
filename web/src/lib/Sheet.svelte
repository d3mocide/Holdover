<script>
  import { api, longDate } from './api.js';
  import { hhmm } from './clock.svelte.js';
  import StockingList from './StockingList.svelte';
  import Conditions from './Conditions.svelte';
  import { db } from './db.js';
  import Icon from './Icon.svelte';
  import { liveQuery } from 'dexie';
  import { isFavorite, toggleFavorite } from './auth.svelte.js';
  import { waterbodyHistory } from './journalStats.js';
  let { id, onclose, onday, onlog } = $props();
  let allTrips = $state([]), allCatches = $state([]), allGear = $state([]);
  let wb = $state(null);
  let error = $state('');
  let favMsg = $state('');
  const star = async () => { favMsg = ''; try { await toggleFavorite(id); } catch (e) { favMsg = e.message; } };


  $effect(() => {
    const sub = liveQuery(async () => ({ trips: await db.trips.toArray(), catches: await db.catches.toArray(), gear: await db.gear.toArray() }))
      .subscribe((v) => { allTrips = v.trips; allCatches = v.catches; allGear = v.gear; });
    return () => sub.unsubscribe();
  });
  const history = $derived(waterbodyHistory({ trips: allTrips, catches: allCatches, gear: allGear, waterbodyId: id }));
  $effect(() => {
    wb = null; error = '';
    api.waterbody(id).then((v) => (wb = v)).catch((e) => (error = e.message));
  });
</script>

<aside class="sheet" aria-label="Waterbody details">
  <button class="close" onclick={onclose} aria-label="Close details"><Icon name="close" /></button>
  {#if error}
    <p role="alert">Couldn't load this waterbody ({error}).</p>
  {:else if !wb}
    <p class="quiet">Loading…</p>
  {:else}
    <h2>{wb.name}</h2>
    <button class="star" class:on={isFavorite(wb.id)} aria-pressed={isFavorite(wb.id)} onclick={star}
      aria-label={isFavorite(wb.id) ? `Remove ${wb.name} from favorites` : `Add ${wb.name} to favorites`}>
      <Icon name={isFavorite(wb.id) ? 'star_fill' : 'star'} size={22} /></button>
    <p class="quiet small">{wb.stocking[0]?.zone_office ?? wb.zone}</p>
    {#if favMsg}<p role="alert" class="small err">{favMsg}</p>{/if}

    <Conditions c={{ ...wb.conditions, waterbody_kind: wb.kind }} />

    <StockingList stocking={wb.stocking} level={3} asOfIso={wb.stocking[0]?.scraped_at} />

    {#if wb.report_items?.length}
      <h3 class="eyebrow">From the weekly report</h3>
      {#each wb.report_items as r}
        <blockquote>
          <p class="small">{r.note}{r.rating !== 'unknown' ? ` (${r.rating})` : ''}</p>
          <p class="quiet small">ODFW, {longDate(r.issued_on)}: “{r.source_sentence}”</p>
        </blockquote>
      {/each}
    {/if}

    {#if history.trips}
      <h3 class="eyebrow">Your history here</h3>
      <p class="small">{history.trips} trip{history.trips === 1 ? '' : 's'} · {history.fish} fish · last {longDate(history.last)}</p>
      {#if history.bySpecies.length}<p class="small quiet">{history.bySpecies.map((x) => `${x.count} ${x.species}`).join(', ')}</p>{/if}
      {#if history.best}
        <div class="best card">
          <span class="eyebrow">Best day</span>
          <strong>{longDate(history.best.date)} · {history.best.fish} fish</strong>
          {#if history.best.conditions.length}<span class="quiet small">{history.best.conditions.join(' · ')}</span>
          {:else}<span class="quiet small">No conditions were captured that day.</span>{/if}
        </div>
      {/if}
      {#if history.topGear}<p class="small">Most productive here: <strong>{history.topGear.name}</strong> <span class="quiet">({history.topGear.count} fish)</span></p>{/if}
    {/if}

    <div class="actions">
      <button class="primary" onclick={() => onday(wb.id)}><Icon name="plan" size={18} /> Plan the day</button>
      <button onclick={() => onlog(wb.id)}><Icon name="log" size={18} /> Log a trip here</button>
      {#if wb.regs_url}
        <a class="btn" href={wb.regs_url} target="_blank" rel="noopener">Official regulations on ODFW <Icon name="external" /></a>
      {/if}
    </div>
  {/if}
</aside>

<style>
  .sheet { position: relative; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; height: 100%; }
  h2 { font-size: 22px; letter-spacing: -0.01em; padding-right: 108px; }
  h3 { margin-top: 10px; }
  .close { position: absolute; top: 8px; right: 8px; padding: 0; }
  .star { position: absolute; top: 8px; right: 60px; padding: 0; border: 0; background: none; color: var(--text-quiet); }
  .star.on { color: var(--warn); }
  .small { font-size: 13px; margin: 0; } .err { color: var(--accent); }
  ul { list-style: none; margin: 0; padding: 0; }
  .grow { flex: 1; }
  blockquote { margin: 0; padding: 4px 0 4px 12px; border-left: 2px solid var(--fresh-2); background: linear-gradient(90deg, var(--glow-1), transparent 70%); border-radius: 2px; }
  blockquote p { margin: 2px 0; }
  .best { display: flex; flex-direction: column; gap: 2px; margin: 4px 0; } .best strong { font-weight: 500; }
  .actions { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
</style>
