<script>
  import { db, uuid, nowIso } from './db.js';
  import { KINDS, KIND_ONE, FISHERY_LABEL, suggest } from './gearCatalog.js';
  import { countPending, syncNow } from './sync.svelte.js';
  import Icon from './Icon.svelte';
  let { item = null, browse = false, onclose, onsaved } = $props();

  const init = item ?? {};
  let kind = $state(init.kind ?? 'lure');
  let name = $state(init.name ?? '');
  let brand = $state(init.brand ?? '');
  let model = $state(init.model ?? '');
  let size = $state(init.size ?? '');
  let color = $state(init.color ?? '');
  let quantity = $state(init.quantity ?? 1);
  let fisheries = $state(init.fisheries_json ? JSON.parse(init.fisheries_json) : []);
  let status = $state(init.status ?? 'active');
  let notes = $state(init.notes ?? '');
  let photoFile = $state(null);
  let sizeHint = $state('');
  let pickedName = $state(null); // the suggestion list stays quiet until the name is edited again
  let showList = $state(browse);
  let err = $state('');
  let saving = $state(false);

  const matches = $derived(item || name === pickedName ? [] : showList || name.trim().length >= 1 ? suggest(name, showList && !name.trim() ? kind : null, showList ? 60 : 6) : []);
  const preview = $derived(photoFile ? URL.createObjectURL(photoFile) : item?.photo_blob ? URL.createObjectURL(item.photo_blob) : item?.photo_path ? `/api/journal/photo/${item.photo_path}` : null);

  function pick(c) {
    kind = c.kind; name = c.name; pickedName = c.name; brand = c.brand ?? brand; fisheries = [...c.fisheries]; sizeHint = c.size ?? ''; showList = false;
  }
  const toggleFishery = (f) => (fisheries = fisheries.includes(f) ? fisheries.filter((x) => x !== f) : [...fisheries, f]);

  async function save() {
    err = '';
    if (!name.trim()) { err = 'Give it a name.'; return; }
    const qty = Math.max(0, Math.min(9999, Math.round(Number(quantity) || 0)));
    saving = true;
    try {
      const row = {
        uuid: item?.uuid ?? uuid(), kind, name: name.trim().slice(0, 120), brand: brand.trim() || null, model: model.trim() || null,
        size: size.trim() || null, color: color.trim() || null, quantity: qty, fisheries_json: fisheries.length ? JSON.stringify(fisheries) : null,
        status, notes: notes.trim() || null, photo_path: item?.photo_path ?? null, photo_blob: item?.photo_blob ?? null,
        updated_at: nowIso(), deleted: 0, dirty: 1
      };
      if (photoFile) { row.photo_blob = photoFile; row.photo_path = null; } // a new photo uploads on the next sync
      await db.gear.put(row);
      await countPending(); syncNow();
      onsaved?.(row);
    } catch (e) { err = `Couldn't save: ${e.message}`; } finally { saving = false; }
  }
  async function remove() {
    if (!confirm(`Delete ${item.name}? It stays in past trips' history as a blank, and is removed from your synced gear.`)) return;
    await db.gear.put({ ...item, deleted: 1, updated_at: nowIso(), dirty: 1 });
    await countPending(); syncNow();
    onsaved?.(null);
  }
</script>

<section class="form" aria-label={item ? 'Edit gear' : 'Add gear'}>
  <header>
    <button onclick={onclose} aria-label="Close"><Icon name="close" /></button>
    <h1>{item ? 'Edit gear' : 'Add gear'}</h1>
  </header>

  <div class="f">
    <label for="g-kind">Type</label>
    <select id="g-kind" bind:value={kind}>{#each KINDS as [k, , one]}<option value={k}>{one}</option>{/each}</select>
  </div>

  <div class="f">
    <label for="g-name">Name</label>
    <input id="g-name" type="text" autocomplete="off" placeholder={`e.g. ${KIND_ONE[kind] === 'Lure' ? 'Panther Martin spinner' : KIND_ONE[kind]}`} bind:value={name} onfocus={() => { if (!item) showList = false; }} />
    {#if !item}
      <button class="link" onclick={() => (showList = !showList)} aria-expanded={showList}>{showList ? 'Hide starter list' : 'Browse the starter list'}</button>
      {#if matches.length}
        <ul class="sugg" aria-label="Suggestions">
          {#each matches as c (c.kind + c.name)}
            <li><button onclick={() => pick(c)}><span>{c.name}</span><span class="quiet small">{[c.brand, c.size].filter(Boolean).join(' · ')}</span></button></li>
          {/each}
        </ul>
      {/if}
    {/if}
  </div>

  <div class="two">
    <div class="f"><label for="g-brand">Brand</label><input id="g-brand" type="text" bind:value={brand} /></div>
    <div class="f"><label for="g-model">Model</label><input id="g-model" type="text" bind:value={model} /></div>
  </div>
  <div class="two">
    <div class="f"><label for="g-size">Size</label><input id="g-size" type="text" placeholder={sizeHint || (kind === 'fly' ? '#12' : kind === 'rod' ? '6wt 9 ft' : '1/8 oz')} bind:value={size} /></div>
    <div class="f"><label for="g-color">Color</label><input id="g-color" type="text" bind:value={color} /></div>
  </div>

  <div class="f">
    <label for="g-qty">Quantity</label>
    <div class="qty">
      <button onclick={() => (quantity = Math.max(0, (Number(quantity) || 0) - 1))} aria-label="Fewer">−</button>
      <input id="g-qty" type="text" inputmode="numeric" class="mono" bind:value={quantity} />
      <button onclick={() => (quantity = (Number(quantity) || 0) + 1)} aria-label="More">+</button>
    </div>
  </div>

  <fieldset>
    <legend>Good for</legend>
    <div class="chips">{#each Object.entries(FISHERY_LABEL) as [f, label]}
      <button class="chip" aria-pressed={fisheries.includes(f)} onclick={() => toggleFishery(f)}>{label}</button>{/each}</div>
  </fieldset>

  {#if item}
    <div class="f"><label for="g-status">Status</label>
      <select id="g-status" bind:value={status}><option value="active">In use</option><option value="retired">Retired</option><option value="lost">Lost</option></select></div>
  {/if}

  <div class="f"><label for="g-notes">Notes</label><input id="g-notes" type="text" bind:value={notes} placeholder="Where you got it, what it is good for" /></div>

  <div class="f">
    <label for="g-photo">Photo (optional)</label>
    {#if preview}<img src={preview} alt="" class="prev" />{/if}
    <input id="g-photo" type="file" accept="image/*" onchange={(e) => (photoFile = e.currentTarget.files?.[0] ?? null)} />
  </div>

  {#if err}<p role="alert" class="err">{err}</p>{/if}
  <div class="bar">
    {#if item}<button class="danger" onclick={remove}>Delete</button>{/if}
    <button class="primary" onclick={save} disabled={saving}>{saving ? 'Saving…' : item ? 'Save changes' : 'Add to my gear'}</button>
  </div>
</section>

<style>
  .form { padding: 20px 16px 24px; display: flex; flex-direction: column; gap: 14px; max-width: 640px; margin: 0 auto; overflow-y: auto; height: 100%; }
  header { display: flex; gap: 12px; align-items: center; } h1 { font-size: 24px; letter-spacing: -0.01em; }
  .f { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
  .f label, legend { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; margin: 0; color: var(--text-quiet); }
  .two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .link { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; justify-content: flex-start; padding: 0; min-height: 36px; }
  .sugg { list-style: none; margin: 0; padding: 4px; border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); max-height: 300px; overflow-y: auto; }
  .sugg button { width: 100%; justify-content: space-between; border: 0; background: none; text-align: left; border-radius: 10px; gap: 8px; }
  .small { font-size: 12.5px; }
  .qty { display: flex; gap: 8px; align-items: center; } .qty input { width: 90px; text-align: center; } .qty button { border-radius: 50%; width: 44px; padding: 0; font-size: 20px; }
  fieldset { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); padding: 8px 14px 12px; min-width: 0; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; } .chip { border-radius: 999px; padding: 0 14px; font-size: 13px; }
  .prev { width: 120px; height: 120px; object-fit: cover; border-radius: 14px; }
  .err { color: var(--accent); margin: 0; }
  .bar { position: sticky; bottom: 0; display: flex; gap: 8px; padding: 12px 0 4px; background: linear-gradient(to top, var(--bg) 60%, transparent); }
  .bar .primary { flex: 1; min-height: 48px; } .danger { color: var(--accent); }
</style>
