<script>
  import { liveQuery } from 'dexie';
  import { db } from './db.js';
  import { KINDS, KIND_LABEL, FISHERY_LABEL } from './gearCatalog.js';
  import { gearStats } from './gearStats.js';
  import Icon from './Icon.svelte';
  let { wbList = [], onitem, onsetup } = $props();

  let tab = $state('items');
  let q = $state('');
  let group = $state('all');
  let gear = $state([]), setups = $state([]), trips = $state([]), catches = $state([]);
  $effect(() => {
    const sub = liveQuery(async () => ({ gear: await db.gear.toArray(), setups: await db.setups.toArray(), trips: await db.trips.toArray(), catches: await db.catches.toArray() }))
      .subscribe((v) => { gear = v.gear; setups = v.setups; trips = v.trips; catches = v.catches; });
    return () => sub.unsubscribe();
  });

  const GROUPS = [['all', 'All', null], ['rig', 'Rods & reels', ['rod', 'reel', 'line']], ['bait', 'Lures & flies', ['lure', 'fly']],
    ['term', 'Terminal', ['terminal']], ['wear', 'Wear & other', ['net', 'wearable', 'electronics', 'other']]];
  const items = $derived(gear.filter((g) => !g.deleted));
  const shown = $derived(items.filter((g) => {
    const kinds = GROUPS.find((x) => x[0] === group)?.[2];
    if (kinds && !kinds.includes(g.kind)) return false;
    const n = q.trim().toLowerCase();
    return !n || [g.name, g.brand, g.model, g.size, g.color].some((v) => (v || '').toLowerCase().includes(n));
  }));
  const byKind = $derived(KINDS.map(([k]) => [k, shown.filter((g) => g.kind === k).sort((a, b) => a.name.localeCompare(b.name))]).filter(([, l]) => l.length));
  const mySetups = $derived(setups.filter((s) => !s.deleted).sort((a, b) => a.name.localeCompare(b.name)));
  const stats = $derived(gearStats({ trips, catches, gear, setups }));
  const itemName = (u) => items.find((g) => g.uuid === u)?.name;
  const setupItems = (s) => { try { return JSON.parse(s.item_uuids_json).map(itemName).filter(Boolean); } catch { return []; } };
  const wbName = (id) => wbList.find((w) => w.id === id)?.name ?? 'Unnamed spot';
  const sub = (g) => [g.brand, g.model, g.size, g.color].filter(Boolean).join(' · ');
  const photoSrc = (g) => (g.photo_blob ? URL.createObjectURL(g.photo_blob) : g.photo_path ? `/api/journal/photo/${g.photo_path}` : null);
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
  const itemLine = (i) => [i.caught ? `${i.caught} caught on it` : null, `${i.fishOnTrips} on trips`, plural(i.trips, 'trip')].filter(Boolean).join(' · ');
  const setupLine = (s) => [`${s.fish} fish`, plural(s.trips, 'trip'), `${s.perTrip}/trip`].join(' · ');
  const tags = (g) => { try { return JSON.parse(g.fisheries_json || '[]'); } catch { return []; } };
</script>

<div class="page">
  <header>
    <span class="ico"><Icon name="gear" size={26} /></span>
    <div><h1>Gear</h1><p class="quiet small">{items.length} item{items.length === 1 ? '' : 's'} · {mySetups.length} setup{mySetups.length === 1 ? '' : 's'}</p></div>
    <button class="primary add" onclick={() => (tab === 'setups' ? onsetup(null) : onitem(null))}>{tab === 'setups' ? 'New setup' : 'Add gear'}</button>
  </header>

  <div class="tabs" role="group" aria-label="Gear sections">
    {#each [['items', 'Items'], ['setups', 'Setups'], ['stats', 'What works']] as [k, label]}
      <button class="chip" aria-pressed={tab === k} onclick={() => (tab = k)}>{label}</button>
    {/each}
  </div>

  {#if tab === 'items'}
    {#if !items.length}
      <div class="empty card">
        <span class="eico"><Icon name="gear" size={32} /></span>
        <strong>No gear yet</strong>
        <p class="quiet">Add what you fish with. Pick from a starter list of common Oregon lures, flies and tackle, or type your own. Gear stays on this device and syncs to your account when you sign in.</p>
        <button class="primary" onclick={() => onitem(null, true)}>Add from the starter list</button>
      </div>
    {:else}
      <input type="text" class="search" placeholder="Search gear" aria-label="Search gear" bind:value={q} />
      <div class="chips" role="group" aria-label="Filter by type">
        {#each GROUPS as [k, label]}<button class="chip" aria-pressed={group === k} onclick={() => (group = k)}>{label}</button>{/each}
      </div>
      {#each byKind as [kind, list] (kind)}
        <h2 class="eyebrow">{KIND_LABEL[kind]} · {list.length}</h2>
        <ul>
          {#each list as g (g.uuid)}
            <li>
              <button class="row" onclick={() => onitem(g)}>
                {#if photoSrc(g)}<img src={photoSrc(g)} alt="" class="thumb" />{:else}<span class="thumb ph"><Icon name="gear" size={18} /></span>{/if}
                <span class="body">
                  <span class="nm">{g.name}{#if g.status !== 'active'} <span class="tag off">{g.status}</span>{/if}</span>
                  {#if sub(g)}<span class="quiet small">{sub(g)}</span>{/if}
                  {#if tags(g).length}<span class="fish">{#each tags(g) as f}<span class="tag">{FISHERY_LABEL[f]}</span>{/each}</span>{/if}
                </span>
                <span class="qty mono" aria-label="Quantity {g.quantity}">×{g.quantity}</span>
              </button>
            </li>
          {/each}
        </ul>
      {:else}<p class="quiet">Nothing matches.</p>{/each}
    {/if}

  {:else if tab === 'setups'}
    {#if !mySetups.length}
      <div class="empty card">
        <span class="eico"><Icon name="plan" size={32} /></span>
        <strong>No setups yet</strong>
        <p class="quiet">A setup is a combination you fish together, like a rod, reel, line and leader. Name it once and pick it when you log a trip.</p>
        <button class="primary" onclick={() => onsetup(null)} disabled={!items.length}>{items.length ? 'Create a setup' : 'Add some gear first'}</button>
      </div>
    {:else}
      <ul>
        {#each mySetups as s (s.uuid)}
          <li><button class="row" onclick={() => onsetup(s)}>
            <span class="body"><span class="nm">{s.name}</span>
              <span class="quiet small">{setupItems(s).join(' · ') || 'No items'}</span></span>
          </button></li>
        {/each}
      </ul>
    {/if}

  {:else}
    {#if !stats.totals.trips}
      <div class="empty card"><span class="eico"><Icon name="fish" size={32} /></span><strong>Nothing to compare yet</strong>
        <p class="quiet">Log trips with the gear you used, and this fills in with what is working for you.</p></div>
    {:else}
      <p class="quiet small">{stats.totals.trips} trip{stats.totals.trips === 1 ? '' : 's'} · {stats.totals.fish} fish logged. "On trips" shares credit between everything used on a trip.</p>
      {#if stats.setups.some((s) => s.trips)}
        <h2 class="eyebrow">Setups</h2>
        <ul>{#each stats.setups.filter((s) => s.trips) as s (s.uuid)}
          <li class="card stat"><strong>{s.name}</strong>
            <span class="mono nums">{setupLine(s)}</span>
            {#if s.waters.length}<span class="quiet small">Best at {s.waters.map((w) => `${wbName(w.waterbody_id)} (${w.fish})`).join(', ')}</span>{/if}</li>
        {/each}</ul>
      {/if}
      {#if stats.items.some((i) => i.trips)}
        <h2 class="eyebrow">Lures, flies and tackle</h2>
        <ul>{#each stats.items.filter((i) => i.trips) as i (i.uuid)}
          <li class="card stat"><strong>{i.name}</strong>
            <span class="mono nums">{itemLine(i)}</span></li>
        {/each}</ul>
      {/if}
    {/if}
  {/if}
</div>

<style>
  .page { padding: 20px 16px 28px; height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
  header { display: flex; gap: 14px; align-items: center; }
  header > div { flex: 1; min-width: 0; } .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } header p { margin: 2px 0 0; } .small { font-size: 13px; margin: 0; }
  .add { flex: none; } .tabs, .chips { display: flex; gap: 6px; flex-wrap: wrap; } .chip { border-radius: 999px; padding: 0 14px; font-size: 13px; }
  .search { margin: 2px 0; }
  h2 { margin: 12px 0 2px; } ul { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
  .row { width: 100%; justify-content: flex-start; align-items: center; text-align: left; gap: 12px; height: auto; padding: 8px 12px; min-height: 60px; }
  .thumb { width: 44px; height: 44px; border-radius: 10px; object-fit: cover; flex: none; background: var(--glass-fill); }
  .ph { display: grid; place-items: center; color: var(--text-quiet); }
  .body { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; } .nm { font-weight: 500; }
  .fish { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
  .tag { font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fresh-2); border: 1px solid color-mix(in srgb, var(--fresh-2) 45%, transparent); border-radius: 999px; padding: 0 7px; }
  .tag.off { color: var(--text-quiet); border-color: var(--hair); }
  .qty { color: var(--text-quiet); flex: none; }
  .empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 32px 20px; }
  .eico { width: 64px; height: 64px; border-radius: 20px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); }
  .empty p { margin: 0 0 8px; max-width: 380px; }
  .stat { display: flex; flex-direction: column; gap: 2px; } .nums { font-size: 13px; color: var(--text-quiet); }
</style>
