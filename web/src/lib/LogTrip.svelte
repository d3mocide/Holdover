<script>
  import { gpsMessage } from './gpsHelp.js';
  import { db, uuid, nowIso, metaGet, metaSet } from './db.js';
  import { captureConditions } from './conditions.js';
  import { countPending, syncNow } from './sync.svelte.js';
  import { asOf } from './clock.svelte.js';
  import Icon from './Icon.svelte';
  import { TRIP_KINDS } from './gearCatalog.js';
  import { requestPersistence } from './storage.js';

  let { wbList = [], initialWb = null, trip = null, onclose, onsaved } = $props();
  const editing = !!trip; // editing keeps the conditions captured when the trip was first saved

  const local = (d = new Date()) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  const toLocal = (iso) => (iso ? local(new Date(iso)) : '');
  const parseList = (j) => { try { const v = JSON.parse(j || '[]'); return Array.isArray(v) ? v : []; } catch { return []; } };
  let wbId = $state(trip ? (trip.waterbody_id != null ? String(trip.waterbody_id) : '') : initialWb ? String(initialWb) : '');
  let gps = $state(trip && trip.waterbody_id == null && trip.lat != null ? { lat: trip.lat, lon: trip.lon } : null);
  let gpsMsg = $state('');
  let startedAt = $state(trip ? toLocal(trip.started_at) : local());
  let endedAt = $state(trip ? toLocal(trip.ended_at) : '');
  let loadedCatches = $state([]); // the stored catch rows of the trip being edited
  let species = $state([{ name: '', count: 0, photo: null, gearUuid: '' }]);
  let setupUuid = $state(trip?.setup_uuid ?? '');
  let gearSel = $state(parseList(trip?.gear_json));
  let gearAll = $state([]), setupsAll = $state([]);
  let method = $state('');
  let notes = $state(trip?.notes ?? '');
  let saving = $state(false);
  let err = $state('');
  let online = $state(navigator.onLine);
  let cachedAt = $state(null);
  let draftLoaded = $state(false);

  $effect(() => {
    db.gear.toArray().then((v) => (gearAll = v.filter((g) => !g.deleted && g.status === 'active' && TRIP_KINDS.includes(g.kind)).sort((a, b) => a.name.localeCompare(b.name))));
    db.setups.toArray().then((v) => (setupsAll = v.filter((s) => !s.deleted).sort((a, b) => a.name.localeCompare(b.name))));
  });
  const toggleGear = (u) => (gearSel = gearSel.includes(u) ? gearSel.filter((x) => x !== u) : [...gearSel, u]);
  // lures picked for the trip come first in each "caught on" list
  const lureOptions = $derived([...gearAll.filter((g) => gearSel.includes(g.uuid)), ...gearAll.filter((g) => !gearSel.includes(g.uuid))]);

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

  $effect(() => {
    if (!trip) return;
    db.catches.where('trip_uuid').equals(trip.uuid).toArray().then((rows) => {
      loadedCatches = rows.filter((c) => !c.deleted);
      if (loadedCatches.length) species = loadedCatches.map((c) => ({ uuid: c.uuid, name: c.species ?? '', count: c.count ?? 0, photo: null, gearUuid: c.gear_uuid ?? '' }));
      method = loadedCatches.find((c) => c.method)?.method ?? '';
    });
  });

  // Draft: restored once, then kept on every edit. (Editing an existing trip never uses the new-trip draft.)
  $effect(() => {
    if (editing) return;
    metaGet('tripDraft').then((d) => {
      if (d && !initialWb) {
        wbId = d.wbId ?? wbId; startedAt = d.startedAt ?? startedAt; endedAt = d.endedAt ?? ''; method = d.method ?? '';
        notes = d.notes ?? ''; gps = d.gps ?? null; setupUuid = d.setupUuid ?? ''; gearSel = d.gearSel ?? [];
        if (d.species?.length) species = d.species.map((s) => ({ name: s.name, count: s.count, photo: null, gearUuid: s.gearUuid ?? '' }));
      }
      draftLoaded = true;
    });
  });
  $effect(() => {
    if (!draftLoaded) return;
    const snap = { wbId, startedAt, endedAt, method, notes, gps, setupUuid, gearSel, species: species.map((s) => ({ name: s.name, count: s.count, gearUuid: s.gearUuid })) };
    metaSet('tripDraft', snap);
  });

  function useGps() {
    if (!navigator.geolocation) { gpsMsg = 'This browser has no location service. Pick a waterbody instead.'; return; }
    if (!isSecureContext) { gpsMsg = gpsMessage(null, false); return; }
    gpsMsg = 'Finding you…';
    navigator.geolocation.getCurrentPosition(
      (p) => { gps = { lat: +p.coords.latitude.toFixed(5), lon: +p.coords.longitude.toFixed(5) }; gpsMsg = ''; },
      (e) => { gpsMsg = gpsMessage(e); }, { enableHighAccuracy: true, timeout: 15000 });
  }

  const step = (s, d) => (s.count = Math.max(0, s.count + d));

  async function save() {
    err = '';
    if (!wbId && !gps) { err = 'Pick a waterbody or pin your GPS location.'; return; }
    saving = true;
    try {
      const tripId = trip?.uuid ?? uuid(), now = nowIso();
      const wb = wbList.find((w) => String(w.id) === wbId);
      const iso = (v) => (v ? new Date(v).toISOString() : null);
      if (editing) {
        await db.transaction('rw', db.trips, db.catches, async () => {
          await db.trips.update(tripId, {
            started_at: iso(startedAt), ended_at: iso(endedAt), waterbody_id: wbId ? Number(wbId) : null,
            lat: gps?.lat ?? wb?.lat ?? trip.lat ?? null, lon: gps?.lon ?? wb?.lon ?? trip.lon ?? null, notes: notes || null,
            setup_uuid: setupUuid || null, gear_json: gearSel.length ? JSON.stringify(gearSel) : null, updated_at: now, dirty: 1
          });
          const rows = species.filter((s) => s.name.trim() || s.count > 0);
          if (!rows.length && method.trim()) rows.push({ name: '', count: 0, photo: null, gearUuid: '' });
          const keep = new Set();
          for (const s of rows) {
            const fields = { species: s.name.trim() || null, count: s.count, method: method.trim() || null, gear_uuid: s.gearUuid || null, updated_at: now, dirty: 1 };
            if (s.uuid) {
              keep.add(s.uuid);
              await db.catches.update(s.uuid, s.photo ? { ...fields, photo_blob: s.photo, photo_path: null } : fields); // a new photo replaces the old
            } else {
              await db.catches.add({ uuid: uuid(), trip_uuid: tripId, length_in: null, kept: null, photo_path: null, photo_blob: s.photo, deleted: 0, ...fields });
            }
          }
          for (const c of loadedCatches) if (!keep.has(c.uuid)) await db.catches.update(c.uuid, { deleted: 1, updated_at: now, dirty: 1 });
        });
        await countPending(); syncNow();
        onsaved?.(tripId);
        return;
      }
      const cond = await captureConditions(wbId ? Number(wbId) : null);
      await db.transaction('rw', db.trips, db.catches, async () => {
        await db.trips.add({
          uuid: tripId, started_at: iso(startedAt), ended_at: iso(endedAt), waterbody_id: wbId ? Number(wbId) : null,
          lat: gps?.lat ?? wb?.lat ?? null, lon: gps?.lon ?? wb?.lon ?? null, notes: notes || null,
          conditions_json: cond.json ? JSON.stringify(cond.json) : null, conditions_source: cond.source,
          setup_uuid: setupUuid || null, gear_json: gearSel.length ? JSON.stringify(gearSel) : null,
          updated_at: now, deleted: 0, dirty: 1
        });
        const rows = species.filter((s) => s.name.trim() || s.count > 0);
        if (!rows.length && method.trim()) rows.push({ name: '', count: 0, photo: null, gearUuid: '' }); // method with no catch
        for (const s of rows) {
          await db.catches.add({
            uuid: uuid(), trip_uuid: tripId, species: s.name.trim() || null, count: s.count, length_in: null,
            method: method.trim() || null, gear_uuid: s.gearUuid || null, kept: null, photo_path: null, photo_blob: s.photo, updated_at: now, deleted: 0, dirty: 1
          });
        }
      });
      requestPersistence(); // a saved trip is data worth protecting from browser cleanup
      await metaSet('tripDraft', null);
      await countPending();
      syncNow(); // no-op offline; runs when connectivity returns
      onsaved?.(tripId);
    } catch (e) { err = `Couldn't save: ${e.message}`; } finally { saving = false; }
  }
</script>

<section class="log" aria-label={editing ? 'Edit trip' : 'Log a trip'}>
  <header>
    <button onclick={onclose} aria-label="Close"><Icon name="close" /></button>
    <h1>{editing ? 'Edit trip' : 'Log a trip'}</h1>{#if !editing}<span class="badge quiet">Draft</span>{/if}
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
      {#if lureOptions.length}
        <div class="f"><label for="co{i}">Caught on (optional)</label>
          <select id="co{i}" bind:value={s.gearUuid}><option value="">Not recorded</option>{#each lureOptions as g}<option value={g.uuid}>{g.name}</option>{/each}</select></div>
      {/if}
      <div class="f"><label for="ph{i}">Photo (optional)</label>
        <input id="ph{i}" type="file" accept="image/*" onchange={(e) => (s.photo = e.currentTarget.files?.[0] ?? null)} /></div>
    {/each}
    <button onclick={() => (species = [...species, { name: '', count: 0, photo: null, gearUuid: '' }])}>Add species</button>
  </fieldset>

  {#if setupsAll.length || gearAll.length}
    <fieldset>
      <legend>Gear used (optional)</legend>
      {#if setupsAll.length}
        <div class="f"><label for="setup">Setup</label>
          <select id="setup" bind:value={setupUuid}><option value="">None</option>{#each setupsAll as st}<option value={st.uuid}>{st.name}</option>{/each}</select></div>
      {/if}
      {#if gearAll.length}
        <div class="f"><span class="lbl" id="lures-l">Lures, flies and tackle</span>
          <div class="chips" role="group" aria-labelledby="lures-l">{#each gearAll as g (g.uuid)}
            <button class="chip" aria-pressed={gearSel.includes(g.uuid)} onclick={() => toggleGear(g.uuid)}>{g.name}</button>{/each}</div></div>
      {/if}
    </fieldset>
  {:else}
    <p class="quiet small hint">Add your gear in the Gear tab to record what you used.</p>
  {/if}

  <div class="f"><label for="meth">Lure or method</label><input id="meth" type="text" bind:value={method} placeholder="e.g. 1/8 oz spinner, drift rig" /></div>
  <div class="f"><label for="nt">Notes</label><input id="nt" type="text" bind:value={notes} /></div>

  <div class="card cond">
    {#if editing}
      <strong>Conditions stay as captured</strong>
      <p class="quiet small">{trip.conditions_source === 'cached' ? 'Saved from cached values' : 'Saved from live values'} when you first logged this trip. Editing does not change them.</p>
    {:else}
    <strong>Conditions captured on save</strong>
    <p class="quiet small">
      {#if !wbId}Pick a waterbody to capture flow, weather and stocking.
      {:else if online}Live conditions if the server answers, otherwise the last cached values{cachedAt ? ` (cached ${asOf(cachedAt)})` : ''}.
      {:else if cachedAt}Offline: will use cached values, {asOf(cachedAt)}. Marked as cached.
      {:else}Offline and nothing cached for this waterbody yet: conditions will be left blank.{/if}
    </p>
    {/if}
  </div>

  {#if err}<p role="alert" class="err">{err}</p>{/if}
  <div class="bar"><button class="primary" onclick={save} disabled={saving}>{saving ? 'Saving…' : editing ? 'Save changes' : 'Save trip'}</button></div>
</section>

<style>
  .log { padding: 20px 16px 24px; display: flex; flex-direction: column; gap: 14px; max-width: 640px; margin: 0 auto; overflow-y: auto; height: 100%; }
  header { display: flex; gap: 12px; align-items: center; } h1 { font-size: 24px; letter-spacing: -0.01em; flex: 1; }
  .badge { font-size: 11px; letter-spacing: 0.09em; text-transform: uppercase; border: 1px solid var(--hair); border-radius: 999px; padding: 3px 10px; }
  .banner { margin: 0; border: 1px solid var(--accent); border-radius: 12px; padding: 10px 14px; background: color-mix(in srgb, var(--accent) 8%, transparent); }
  .f { min-width: 0; display: flex; flex-direction: column; gap: 6px; }
  .f label { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; margin: 0; }
  .two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .row, .srow { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .srow input { flex: 1; min-width: 120px; }
  .srow button { border-radius: 50%; width: 44px; padding: 0; font-size: 20px; }
  .count { min-width: 32px; text-align: center; font-size: 20px; font-weight: 600; color: var(--fresh-1); }
  fieldset { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); display: flex; flex-direction: column; gap: 12px; padding: 8px 14px 14px; }
  legend { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-quiet); padding: 0 6px; }
  .small { font-size: 13px; margin: 0; } .err { color: var(--accent); margin: 0; }
  .cond p { margin: 4px 0 0; } .chips { display: flex; gap: 6px; flex-wrap: wrap; } .chips .chip { border-radius: 999px; padding: 0 14px; font-size: 13px; }
  .lbl { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-quiet); } .hint { margin: 0; }
  .bar { position: sticky; bottom: 0; padding: 12px 0 4px; background: linear-gradient(to top, var(--bg) 60%, transparent); }
  .bar button { width: 100%; min-height: 48px; font-size: 15px; }
</style>
