<script>
  import { liveQuery } from 'dexie';
  import { db, uuid, nowIso } from './db.js';
  import { KINDS, KIND_LABEL } from './gearCatalog.js';
  import { countPending, syncNow } from './sync.svelte.js';
  import Icon from './Icon.svelte';
  let { setup = null, onclose, onsaved } = $props();

  const init = setup ?? {};
  let name = $state(init.name ?? '');
  let notes = $state(init.notes ?? '');
  let picked = $state((() => { try { return JSON.parse(init.item_uuids_json || '[]'); } catch { return []; } })());
  let gear = $state([]);
  let err = $state('');
  $effect(() => {
    const sub = liveQuery(() => db.gear.toArray()).subscribe((v) => (gear = v.filter((g) => !g.deleted && g.status === 'active')));
    return () => sub.unsubscribe();
  });
  const groups = $derived(KINDS.map(([k]) => [k, gear.filter((g) => g.kind === k).sort((a, b) => a.name.localeCompare(b.name))]).filter(([, l]) => l.length));
  const toggle = (u) => (picked = picked.includes(u) ? picked.filter((x) => x !== u) : [...picked, u]);

  async function save() {
    err = '';
    if (!name.trim()) { err = 'Give the setup a name, like "6wt dry fly".'; return; }
    const row = { uuid: setup?.uuid ?? uuid(), name: name.trim().slice(0, 120), notes: notes.trim() || null, item_uuids_json: JSON.stringify(picked), updated_at: nowIso(), deleted: 0, dirty: 1 };
    await db.setups.put(row);
    await countPending(); syncNow();
    onsaved?.(row);
  }
  async function remove() {
    if (!confirm(`Delete the setup "${setup.name}"? Trips that used it keep their other gear.`)) return;
    await db.setups.put({ ...setup, deleted: 1, updated_at: nowIso(), dirty: 1 });
    await countPending(); syncNow();
    onsaved?.(null);
  }
</script>

<section class="form" aria-label={setup ? 'Edit setup' : 'New setup'}>
  <header><button onclick={onclose} aria-label="Close"><Icon name="close" /></button><h1>{setup ? 'Edit setup' : 'New setup'}</h1></header>
  <div class="f"><label for="s-name">Name</label><input id="s-name" type="text" placeholder="e.g. 6wt dry fly" bind:value={name} /></div>
  <fieldset>
    <legend>What is in it</legend>
    {#each groups as [kind, list] (kind)}
      <p class="eyebrow">{KIND_LABEL[kind]}</p>
      {#each list as g (g.uuid)}
        <label class="ck"><input type="checkbox" checked={picked.includes(g.uuid)} onchange={() => toggle(g.uuid)} /> <span>{g.name}{#if g.size} <span class="quiet small">{g.size}</span>{/if}</span></label>
      {/each}
    {:else}<p class="quiet">Add some gear first, then come back to build a setup.</p>{/each}
  </fieldset>
  <div class="f"><label for="s-notes">Notes</label><input id="s-notes" type="text" bind:value={notes} placeholder="When you reach for it" /></div>
  {#if err}<p role="alert" class="err">{err}</p>{/if}
  <div class="bar">
    {#if setup}<button class="danger" onclick={remove}>Delete</button>{/if}
    <button class="primary" onclick={save}>{setup ? 'Save changes' : 'Create setup'}</button>
  </div>
</section>

<style>
  .form { padding: 20px 16px 24px; display: flex; flex-direction: column; gap: 14px; max-width: 640px; margin: 0 auto; overflow-y: auto; height: 100%; }
  header { display: flex; gap: 12px; align-items: center; } h1 { font-size: 24px; letter-spacing: -0.01em; }
  .f { display: flex; flex-direction: column; gap: 6px; } .f label, legend { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; margin: 0; color: var(--text-quiet); }
  fieldset { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); padding: 8px 14px 12px; min-width: 0; }
  .eyebrow { margin: 10px 0 0; } .ck { display: flex; align-items: center; gap: 12px; min-height: 44px; color: var(--text); margin: 0; font-size: 14px; } .small { font-size: 12.5px; }
  .err { color: var(--accent); margin: 0; }
  .bar { position: sticky; bottom: 0; display: flex; gap: 8px; padding: 12px 0 4px; background: linear-gradient(to top, var(--bg) 60%, transparent); }
  .bar .primary { flex: 1; min-height: 48px; } .danger { color: var(--accent); }
</style>
