<script>
  import { db, uuid, nowIso, metaGet, metaSet } from './db.js';
  import { captureConditions } from './conditions.js';
  import { countPending, syncNow } from './sync.svelte.js';
  import { asOf } from './api.js';
  import Icon from './Icon.svelte';

  let { wbList = [], initialWb = null, onclose, onsaved } = $props();

  const local = (d = new Date()) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  let wbId = $state(initialWb ? String(initialWb) : '');
  let gps = $state(null);
  let gpsMsg = $state('');
  let startedAt = $state(local());
  let endedAt = $state('');
  let species = $state([{ name: '', count: 0, photo: null }]);
  let method = $state('');
  let notes = $state('');
  let saving = $state(false);
  let err = $state('');
  let online = $state(navigator.onLine);
  let cachedAt = $state(null);
  let draftLoaded = $state(false);

  const COMMON = ['rainbow trout', 'cutthroat trout', 'brown trout', 'steelhead', 'coho', 'spring chinook', 'fall chinook', 'smallmouth bass', 'largemouth bass', 'bluegill', 'crappie', 'walleye', 'shad', 'kokanee'];

  $effect(() => {
    const u = () => (online = true), d = () => (online = false);
    addEventListener('online', u); addEventListener('offline', d);
    return () => { removeEventListener('online', u); removeEventListener('offline', d); };
  });
  $effect(() => { // what the cache could provide if we're offline when saving
    cachedAt = null;
    if (wbId) db.cond.get(Number(wbId)).then((c) => (cachedAt = c?.fetched_at ?? null));
  });

  // Draft: restored once, then kept on every edit.
  $effect(() => {
    metaGet('tripDraft').then((d) => {
      if (d && !initialWb) {
        wbId = d.wbId ?? wbId; startedAt = d.startedAt ?? startedAt; endedAt = d.endedAt ?? ''; method = d.method ?? '';
        notes = d.notes ?? ''; gps = d.gps ?? null;
        if (d.species?.length) species = d.species.map((s) => ({ name: s.name, count: s.count, photo: null }));
      }
      draftLoaded = true;
    });
  });
  $effect(() => {
    if (!draftLoaded) return;
    const snap = { wbId, startedAt, endedAt, method, notes, gps, species: species.map((s) => ({ name: s.name, count: s.count })) };
    metaSet('tripDraft', snap);
  });

  function useGps() {
    gpsMsg = 'Finding you…';
    navigator.geolocation.getCurrentPosition(
      (p) => { gps = { lat: +p.coords.latitude.toFixed(5), lon: +p.coords.longitude.toFixed(5) }; gpsMsg = ''; },
      (e) => { gpsMsg = `No GPS fix (${e.message}).`; }, { enableHighAccuracy: true, timeout: 15000 });
  }

  const step = (s, d) => (s.count = Math.max(0, s.count + d));

  async function save() {
    err = '';
    if (!wbId && !gps) { err = 'Pick a waterbody or pin your GPS location.'; return; }
    saving = true;
    try {
      const tripId = uuid(), now = nowIso();
      const wb = wbList.find((w) => String(w.id) === wbId);
      const cond = await captureConditions(wbId ? Number(wbId) : null);
      const iso = (v) => (v ? new Date(v).toISOString() : null);
      await db.transaction('rw', db.trips, db.catches, async () => {
        await db.trips.add({
          uuid: tripId, started_at: iso(startedAt), ended_at: iso(endedAt), waterbody_id: wbId ? Number(wbId) : null,
          lat: gps?.lat ?? wb?.lat ?? null, lon: gps?.lon ?? wb?.lon ?? null, notes: notes || null,
          conditions_json: cond.json ? JSON.stringify(cond.json) : null, conditions_source: cond.source,
          updated_at: now, deleted: 0, dirty: 1
        });
        const rows = species.filter((s) => s.name.trim() || s.count > 0);
        if (!rows.length && method.trim()) rows.push({ name: '', count: 0, photo: null }); // method with no catch
        for (const s of rows) {
          await db.catches.add({
            uuid: uuid(), trip_uuid: tripId, species: s.name.trim() || null, count: s.count, length_in: null,
            method: method.trim() || null, kept: null, photo_path: null, photo_blob: s.photo, updated_at: now, deleted: 0, dirty: 1
          });
        }
      });
      await metaSet('tripDraft', null);
      await countPending();
      syncNow(); // no-op offline; runs when connectivity returns
      onsaved?.(tripId);
    } catch (e) { err = `Couldn't save: ${e.message}`; } finally { saving = false; }
  }
</script>

<section class="log" aria-label="Log a trip">
  <header>
    <button onclick={onclose} aria-label="Close"><Icon name="close" /></button>
    <h1>Log a trip</h1><span class="badge quiet">Draft</span>
  </header>

  {#if !online}<p class="banner" role="status">Saved on this phone, syncs when you have signal.</p>{/if}

  <div class="f">
    <label for="where">Where</label>
    <select id="where" bind:value={wbId}>
      <option value="">Choose a waterbody…</option>
      {#each wbList as w (w.id)}<option value={String(w.id)}>{w.name}</option>{/each}
    </select>
    <div class="row">
      <button onclick={useGps}>Use GPS location</button>
      {#if gps}<span class="mono small">GPS pinned · {gps.lat}, {gps.lon}</span>{/if}
    </div>
    {#if gpsMsg}<p class="quiet small" role="status">{gpsMsg}</p>{/if}
  </div>

  <div class="two">
    <div class="f"><label for="st">Start</label><input id="st" type="datetime-local" bind:value={startedAt} /></div>
    <div class="f"><label for="en">End</label><input id="en" type="datetime-local" bind:value={endedAt} /></div>
  </div>

  <fieldset>
    <legend>Catch</legend>
    <datalist id="species-list">{#each COMMON as c}<option value={c}></option>{/each}</datalist>
    {#each species as s, i}
      <div class="srow">
        <input type="text" list="species-list" placeholder="Species" aria-label="Species {i + 1}" bind:value={s.name} />
        <button onclick={() => step(s, -1)} aria-label="Fewer {s.name || 'fish'}">−</button>
        <span class="mono count" aria-live="polite">{s.count}</span>
        <button onclick={() => step(s, 1)} aria-label="More {s.name || 'fish'}">+</button>
      </div>
      <div class="f"><label for="ph{i}">Photo (optional)</label>
        <input id="ph{i}" type="file" accept="image/*" onchange={(e) => (s.photo = e.currentTarget.files?.[0] ?? null)} /></div>
    {/each}
    <button onclick={() => (species = [...species, { name: '', count: 0, photo: null }])}>Add species</button>
  </fieldset>

  <div class="f"><label for="meth">Lure or method</label><input id="meth" type="text" bind:value={method} placeholder="e.g. 1/8 oz spinner, drift rig" /></div>
  <div class="f"><label for="nt">Notes</label><input id="nt" type="text" bind:value={notes} /></div>

  <div class="card cond">
    <strong>Conditions captured on save</strong>
    <p class="quiet small">
      {#if !wbId}Pick a waterbody to capture flow, weather and stocking.
      {:else if online}Live conditions if the server answers, otherwise the last cached values{cachedAt ? ` (cached ${asOf(cachedAt)})` : ''}.
      {:else if cachedAt}Offline: will use cached values, {asOf(cachedAt)}. Marked as cached.
      {:else}Offline and nothing cached for this waterbody yet: conditions will be left blank.{/if}
    </p>
  </div>

  {#if err}<p role="alert" class="err">{err}</p>{/if}
  <div class="bar"><button class="primary" onclick={save} disabled={saving}>{saving ? 'Saving…' : 'Save trip'}</button></div>
</section>

<style>
  .log { padding: 16px 16px 24px; display: flex; flex-direction: column; gap: 12px; max-width: 640px; overflow-y: auto; height: 100%; }
  header { display: flex; gap: 12px; align-items: center; } h1 { font-size: 20px; flex: 1; }
  .banner { margin: 0; border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .row, .srow { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .srow input { flex: 1; min-width: 120px; } .count { min-width: 28px; text-align: center; font-size: 18px; }
  fieldset { border: 1px solid var(--line); border-radius: 12px; display: flex; flex-direction: column; gap: 8px; }
  .small { font-size: 13px; margin: 0; } .err { color: var(--accent); margin: 0; }
  .cond p { margin: 4px 0 0; } .bar { position: sticky; bottom: 0; padding: 8px 0; background: var(--bg); }
  .bar button { width: 100%; }
  input[type='file'] { min-height: 44px; padding-top: 10px; }
</style>
