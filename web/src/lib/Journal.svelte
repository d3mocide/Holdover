<script>
  import { liveQuery } from 'dexie';
  import { db, nowIso } from './db.js';
  import { syncState, syncNow, countPending } from './sync.svelte.js';
  import { getToken, longDate, hhmm } from './api.js';
  import Icon from './Icon.svelte';

  let { wbList = [], onlog } = $props();
  let trips = $state([]), catches = $state([]);
  $effect(() => {
    const s1 = liveQuery(() => db.trips.toArray()).subscribe((v) => (trips = v.filter((t) => !t.deleted).sort((a, b) => (b.started_at ?? '').localeCompare(a.started_at ?? ''))));
    const s2 = liveQuery(() => db.catches.toArray()).subscribe((v) => (catches = v.filter((c) => !c.deleted)));
    return () => { s1.unsubscribe(); s2.unsubscribe(); };
  });
  const name = (id) => wbList.find((w) => w.id === id)?.name;
  const catchesFor = (t) => catches.filter((c) => c.trip_uuid === t.uuid && (c.species || c.count));
  const total = (t) => catchesFor(t).reduce((n, c) => n + (c.count || 0), 0);

  async function remove(t) {
    if (!confirm('Delete this trip? It will be removed from your synced journal too.')) return;
    const now = nowIso();
    await db.trips.update(t.uuid, { deleted: 1, updated_at: now, dirty: 1 });
    for (const c of catches.filter((c) => c.trip_uuid === t.uuid)) await db.catches.update(c.uuid, { deleted: 1, updated_at: now, dirty: 1 });
    await countPending(); syncNow();
  }

  async function exportFile(format) {
    const r = await fetch(`/api/journal/export?format=${format}`, { headers: { Authorization: `Bearer ${getToken()}` } });
    if (!r.ok) { alert(`Export failed (${r.status}). Needs a connection and the admin token.`); return; }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(await r.blob()); a.download = `holdover-journal.${format}`; a.click();
  }
  const cond = (t) => { try { return JSON.parse(t.conditions_json); } catch { return null; } };
  const statusText = $derived(
    { 'no-token': 'Local only: add the token in Settings to sync', offline: 'Offline', syncing: 'Syncing…', error: `Sync error (${syncState.error}), retrying`, idle: syncState.lastSync ? `Synced ${hhmm(syncState.lastSync)}` : 'Ready' }[syncState.status]
  );
</script>

<div class="page">
  <header><h1>Journal</h1><button class="primary" onclick={() => onlog()}>Log a trip</button></header>
  <p class="quiet small" role="status">{statusText}{syncState.pending ? ` · ${syncState.pending} waiting to sync` : ''}</p>

  {#if !trips.length}<p class="quiet">No trips yet. Trips are saved on this device first, so logging works with no signal.</p>{/if}
  <ul>
    {#each trips as t (t.uuid)}
      <li class="card">
        <div class="top">
          <strong>{name(t.waterbody_id) ?? 'GPS pin'}</strong>
          <span class="mono small">{t.started_at ? longDate(t.started_at.slice(0, 10)) : ''}</span>
        </div>
        <p class="small">{total(t)} fish{catchesFor(t).length ? ': ' + catchesFor(t).map((c) => `${c.count || 0} ${c.species ?? '?'}`).join(', ') : ''}</p>
        {#if catchesFor(t)[0]?.method}<p class="quiet small">{catchesFor(t)[0].method}</p>{/if}
        {#if t.notes}<p class="small">{t.notes}</p>{/if}
        <p class="quiet small">
          {t.dirty ? 'Waiting to sync' : 'Synced'}
          {#if t.conditions_source}· conditions {t.conditions_source}{cond(t)?.cache_as_of ? ` (as of ${hhmm(cond(t).cache_as_of)})` : ''}{/if}
        </p>
        <button onclick={() => remove(t)} aria-label="Delete trip"><Icon name="close" /></button>
      </li>
    {/each}
  </ul>

  <div class="row">
    <button onclick={() => exportFile('json')}>Export JSON</button>
    <button onclick={() => exportFile('csv')}>Export CSV</button>
  </div>
</div>

<style>
  .page { padding: 16px; max-width: 720px; height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
  header { display: flex; justify-content: space-between; align-items: center; } h1 { font-size: 22px; }
  ul { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; margin: 0; }
  .card { position: relative; } .card button { position: absolute; right: 6px; bottom: 6px; border: 0; background: none; color: var(--text-quiet); }
  .top { display: flex; justify-content: space-between; gap: 8px; } .small { font-size: 13px; margin: 2px 0; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
