<script>
  import { liveQuery } from 'dexie';
  import { db, nowIso } from './db.js';
  import { syncState, syncNow, countPending } from './sync.svelte.js';
  import { longDate } from './api.js';
  import { hhmm } from './clock.svelte.js';
  import { auth } from './auth.svelte.js';
  import Icon from './Icon.svelte';
  import { namesFor } from './gearStats.js';

  let { wbList = [], onlog, onedit } = $props();
  let trips = $state([]), catches = $state([]), gear = $state([]), setups = $state([]);
  $effect(() => {
    const s1 = liveQuery(() => db.trips.toArray()).subscribe((v) => (trips = v.filter((t) => !t.deleted).sort((a, b) => (b.started_at ?? '').localeCompare(a.started_at ?? ''))));
    const s2 = liveQuery(() => db.catches.toArray()).subscribe((v) => (catches = v.filter((c) => !c.deleted)));
    const s3 = liveQuery(() => db.gear.toArray()).subscribe((v) => (gear = v));
    const s4 = liveQuery(() => db.setups.toArray()).subscribe((v) => (setups = v));
    return () => { s1.unsubscribe(); s2.unsubscribe(); s3.unsubscribe(); s4.unsubscribe(); };
  });
  const name = (id) => wbList.find((w) => w.id === id)?.name;
  const catchesFor = (t) => catches.filter((c) => c.trip_uuid === t.uuid && (c.species || c.count));
  const setupName = (t) => setups.find((x) => x.uuid === t.setup_uuid && !x.deleted)?.name;
  const gearNames = (t) => namesFor(t.gear_json, gear);
  const caughtOn = (c) => gear.find((g) => g.uuid === c.gear_uuid && !g.deleted)?.name;
  const total = (t) => catchesFor(t).reduce((n, c) => n + (c.count || 0), 0);

  async function remove(t) {
    if (!confirm('Delete this trip? It will be removed from your synced journal too.')) return;
    const now = nowIso();
    await db.trips.update(t.uuid, { deleted: 1, updated_at: now, dirty: 1 });
    for (const c of catches.filter((c) => c.trip_uuid === t.uuid)) await db.catches.update(c.uuid, { deleted: 1, updated_at: now, dirty: 1 });
    await countPending(); syncNow();
  }

  async function exportFile(format) {
    const r = await fetch(`/api/journal/export?format=${format}`, { credentials: 'same-origin', headers: { 'X-Holdover': '1' } });
    if (!r.ok) { alert(r.status === 401 ? 'Sign in to export your synced journal.' : `Export failed (${r.status}). Export needs a connection.`); return; }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(await r.blob()); a.download = `holdover-journal.${format}`; a.click();
  }
  const cond = (t) => { try { return JSON.parse(t.conditions_json); } catch { return null; } };
  const statusText = $derived(
    { 'signed-out': 'Saved on this device only. Sign in (Settings) to sync across devices.', offline: 'Offline', syncing: 'Syncing…', error: `Sync error (${syncState.error}), retrying`, idle: syncState.lastSync ? `Synced ${hhmm(syncState.lastSync)}` : 'Ready' }[syncState.status]
  );
</script>

<div class="page">
  <header><h1>Journal</h1>{#if trips.length}<button class="primary" onclick={() => onlog()}><Icon name="log" size={18} /> Log a trip</button>{/if}</header>
  <p class="quiet small" role="status">{statusText}{syncState.pending ? ` · ${syncState.pending} waiting to sync` : ''}</p>

  {#if !trips.length}
    <div class="empty card">
      <span class="eico"><Icon name="fish" size={34} /></span>
      <strong>No trips yet</strong>
      <p class="quiet">Trips are saved on this device first, so logging works with no signal.</p>
      <button class="primary" onclick={() => onlog()}><Icon name="log" size={18} /> Log your first trip</button>
    </div>
  {/if}
  <ul>
    {#each trips as t (t.uuid)}
      <li class="card">
        <div class="top">
          <strong>{name(t.waterbody_id) ?? 'GPS pin'}</strong>
          <span class="mono small">{t.started_at ? longDate(t.started_at.slice(0, 10)) : ''}</span>
        </div>
        <p class="small">{total(t)} fish{catchesFor(t).length ? ': ' + catchesFor(t).map((c) => `${c.count || 0} ${c.species ?? '?'}`).join(', ') : ''}</p>
        {#if setupName(t) || gearNames(t).length}<p class="gearline small"><Icon name="gear" size={14} /> {[setupName(t), ...gearNames(t)].filter(Boolean).join(' · ')}</p>{/if}
        {#each catchesFor(t).filter(caughtOn) as c}<p class="quiet small">{c.count || 0} {c.species ?? 'fish'} on {caughtOn(c)}</p>{/each}
        {#if catchesFor(t)[0]?.method}<p class="quiet small">{catchesFor(t)[0].method}</p>{/if}
        {#if t.notes}<p class="small">{t.notes}</p>{/if}
        <p class="quiet small">
          {t.dirty ? 'Waiting to sync' : 'Synced'}
          {#if t.conditions_source}· conditions {t.conditions_source}{cond(t)?.cache_as_of ? ` (as of ${hhmm(cond(t).cache_as_of)})` : ''}{/if}
        </p>
        <div class="acts"><button onclick={() => onedit(t)} aria-label="Edit trip">Edit</button><button onclick={() => remove(t)} aria-label="Delete trip"><Icon name="close" /></button></div>
      </li>
    {/each}
  </ul>

  <div class="row">
    <button onclick={() => exportFile('json')}>Export JSON</button>
    <button onclick={() => exportFile('csv')}>Export CSV</button>
  </div>
</div>

<style>
  .page { padding: 20px 16px; height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
  header { display: flex; justify-content: space-between; align-items: center; min-height: 44px; } h1 { font-size: 24px; letter-spacing: -0.01em; }
  ul { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 10px; margin: 0; }
  .card { position: relative; } .acts { position: absolute; right: 6px; bottom: 6px; display: flex; gap: 2px; }
  .acts button { border: 0; background: none; color: var(--text-quiet); font-size: 13px; } .acts button:first-child { color: var(--fresh-1); }
  .top { display: flex; justify-content: space-between; gap: 8px; } .small { font-size: 13px; margin: 2px 0; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
  .gearline { display: flex; align-items: center; gap: 6px; color: var(--fresh-2); }
  .empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 36px 20px; }
  .empty .eico { width: 64px; height: 64px; border-radius: 20px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair), 0 0 28px var(--glow-1); }
  .empty p { margin: 0 0 8px; max-width: 360px; } .empty button { position: static; color: var(--on-accent); border: 1px solid var(--accent); background: var(--accent); }
</style>
