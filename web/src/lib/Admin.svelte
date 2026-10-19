<script>
  import { api } from './api.js';
  import { auth } from './auth.svelte.js';
  import { pin, startPin } from './pinTool.svelte.js';
  let { onChanged } = $props();

  let users = $state([]);
  let invites = $state([]);
  let newLink = $state('');
  let copied = $state(false);
  let aliases = $state([]);
  let items = $state([]);
  let itemChoice = $state({});
  let wbs = $state([]);
  let pins = $state([]);
  let pinZone = $state('all');
  const pinZones = $derived([...new Set(pins.map((p) => p.zone))]);
  const shownPins = $derived(pins.filter((p) => pinZone === 'all' || p.zone === pinZone));
  $effect(() => { pin.version; api.pinsToPlace().then((v) => (pins = v)).catch(() => {}); });
  let choice = $state({});
  let msg = $state('');

  const when = (iso) => (iso ? new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'never');

  async function load() {
    try {
      [users, invites, aliases, wbs, items] = await Promise.all([api.adminUsers(), api.adminInvites(), api.aliases(), api.waterbodies(), api.reviewItems()]);
    } catch (e) { msg = `Admin data unavailable (${e.message}).`; }
  }
  $effect(() => { load(); });

  const act = async (fn, ok) => { msg = ''; try { await fn(); if (ok) msg = ok; await load(); } catch (e) { msg = e.message; } };
  const toggleDisabled = (u) => act(() => api.adminDisable(u.id, !u.disabled));
  const toggleAdmin = (u) => act(() => api.adminSetAdmin(u.id, !u.is_admin));
  function resetPw(u) {
    const p = prompt(`New password for ${u.username} (10+ characters). They will be signed out everywhere.`);
    if (p) act(() => api.adminResetPassword(u.id, p), `Password reset for ${u.username}.`);
  }
  async function createInvite() {
    msg = ''; copied = false;
    try { const r = await api.adminCreateInvite(); newLink = `${location.origin}${r.path}`; await load(); } catch (e) { msg = e.message; }
  }
  async function copy() { try { await navigator.clipboard.writeText(newLink); copied = true; } catch { msg = 'Copy failed: select the link and copy it by hand.'; } }

  async function confirm(a) {
    const wb = Number(choice[a.id] ?? a.proposed_waterbody?.id);
    if (!wb) { msg = 'Pick a waterbody first.'; return; }
    act(async () => { await api.confirm(a.id, wb); onChanged?.(); });
  }
  const decide = (i, accept) => act(async () => {
    if (accept) await api.acceptItem(i.id, Number(itemChoice[i.id] || i.waterbody?.id) || null); else await api.rejectItem(i.id);
    onChanged?.();
  });
  const runReports = () => act(async () => {
    const r = await api.runReports();
    msg = `Report fetch ${r.fetch.ok ? 'ok' : 'failed'}; ${r.llm.extracted ?? 0} extracted, ${r.llm.pending ?? 0} pending (LLM ${r.llm.llm ?? 'error'}).`; onChanged?.();
  });
  const runNow = () => act(async () => {
    const r = await api.runStocking();
    msg = r.ok ? `Fetched ${r.pages} page(s), ${r.rows_inserted} new rows.` : 'Fetch failed: see source status.'; onChanged?.();
  });
</script>

<section class="card">
  <h2 class="eyebrow">People</h2>
  <ul class="users">
    {#each users as u (u.id)}
      <li class:off={u.disabled}>
        <div class="top"><strong>{u.username}</strong>
          {#if u.is_admin}<span class="chip-sm">admin</span>{/if}{#if u.disabled}<span class="chip-sm bad">disabled</span>{/if}
          {#if u.id === auth.user?.id}<span class="quiet small">you</span>{/if}</div>
        <p class="quiet small">{u.trips} trip{u.trips === 1 ? '' : 's'} · {u.favorites} favorite{u.favorites === 1 ? '' : 's'} · last seen {when(u.last_seen)}</p>
        {#if u.id !== auth.user?.id}
          <div class="row">
            <button onclick={() => toggleAdmin(u)}>{u.is_admin ? 'Remove admin' : 'Make admin'}</button>
            <button onclick={() => resetPw(u)}>Reset password</button>
            <button onclick={() => toggleDisabled(u)}>{u.disabled ? 'Enable' : 'Disable'}</button>
          </div>
        {/if}
      </li>
    {/each}
  </ul>
</section>

<section class="card">
  <h2 class="eyebrow">Invites</h2>
  <p class="quiet small">An invite link lets one person create an account. It works once and expires in a week. It is shown only here, now.</p>
  <button class="primary" onclick={createInvite}>Create invite link</button>
  {#if newLink}
    <div class="link"><input type="text" readonly value={newLink} aria-label="Invite link" onfocus={(e) => e.currentTarget.select()} />
      <button onclick={copy}>{copied ? 'Copied' : 'Copy'}</button></div>
  {/if}
  {#if invites.length}
    <ul class="inv">
      {#each invites as i (i.id)}
        <li><span class="small">{when(i.created_at)} · <span class:ok={i.state === 'open'}>{i.state}</span></span>
          {#if i.state === 'open'}<button class="rm" onclick={() => act(() => api.adminRevokeInvite(i.id))}>Revoke</button>{/if}</li>
      {/each}
    </ul>
  {/if}
</section>

<section class="card">
  <h2 class="eyebrow">Place pins ({pins.length})</h2>
  <p class="quiet small">Waterbodies with no map pin, and pins placed from a same-named point that deserve a check. Choose one, then tap its spot on the map.</p>
  {#if pinZones.length > 1}
    <select aria-label="Zone" bind:value={pinZone}><option value="all">All zones</option>{#each pinZones as z}<option value={z}>{z}</option>{/each}</select>
  {/if}
  <ul class="pins">
    {#each shownPins as p (p.id)}
      <li><div><strong>{p.name}</strong> <span class="quiet small">· {p.zone} · {p.status === 'none' ? 'no pin' : 'check this pin'}</span>
        {#if p.status === 'likely'}<p class="quiet small">{p.note}</p>{/if}</div>
        <button onclick={() => startPin(p)}>{p.status === 'none' ? 'Place on map' : 'Move on map'}</button></li>
    {:else}<li class="quiet small">Every waterbody has a pin you have not been asked to check.</li>{/each}
  </ul>
</section>

<section class="card">
  <h2 class="eyebrow">Data</h2>
  <div class="row"><button onclick={runNow}>Fetch stocking now</button><button onclick={runReports}>Fetch report now</button></div>

  <h3>Report items to review ({items.length})</h3>
  {#if !items.length}<p class="quiet small">Nothing waiting.</p>{/if}
  {#each items as i (i.id)}
    <div class="alias">
      <p><strong>{i.waterbody_raw}</strong> <span class="quiet small">· {i.zone} · {i.species || 'species not stated'} · {i.rating}</span></p>
      <p class="quiet small">“{i.source_sentence}”</p>
      <div class="row">
        <select aria-label="Waterbody for {i.waterbody_raw}" bind:value={itemChoice[i.id]}>
          <option value="">{i.waterbody ? `Matched: ${i.waterbody.name}` : 'No waterbody (statewide note)'}</option>
          {#each wbs as w}<option value={w.id}>{w.name}</option>{/each}
        </select>
        <button onclick={() => decide(i, true)}>Accept</button>
        <button onclick={() => decide(i, false)}>Reject</button>
      </div>
    </div>
  {/each}

  <h3>Waterbody labels to review ({aliases.length})</h3>
  {#if !aliases.length}<p class="quiet small">Every stocking label is matched.</p>{/if}
  {#each aliases as a (a.id)}
    <div class="alias">
      <p class="mono">{a.alias_text}</p>
      <p class="quiet small">{a.proposed_waterbody ? `Proposed: ${a.proposed_waterbody.name} (${Math.round(a.proposed_confidence * 100)}%)` : 'No proposal'}</p>
      <div class="row">
        <select aria-label="Waterbody for {a.alias_text}" bind:value={choice[a.id]}>
          <option value="">{a.proposed_waterbody ? 'Use proposal' : 'Choose…'}</option>
          {#each wbs as w}<option value={w.id}>{w.name}</option>{/each}
        </select>
        <button onclick={() => confirm(a)}>Confirm</button>
      </div>
    </div>
  {/each}
  {#if msg}<p role="status" class="small">{msg}</p>{/if}
</section>

<style>
  h2 { margin: 0 0 8px; } h3 { font-size: 14px; margin: 14px 0 4px; } .small { font-size: 13px; margin: 2px 0; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0; }
  ul { list-style: none; padding: 0; margin: 0; }
  .pins li { display: flex; justify-content: space-between; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--hair); } .pins li:last-child { border-bottom: 0; } .pins p { margin: 2px 0 0; }
  .users li { padding: 10px 0; border-bottom: 1px solid var(--hair); } .users li:last-child { border-bottom: 0; } .users li.off { opacity: 0.6; }
  .top { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .chip-sm { font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--fresh-1); border: 1px solid color-mix(in srgb, var(--fresh-1) 45%, transparent); border-radius: 999px; padding: 1px 8px; }
  .chip-sm.bad { color: var(--accent); border-color: var(--accent); }
  .link { display: flex; gap: 8px; margin: 10px 0; } .link input { flex: 1; font: 13px 'IBM Plex Mono', monospace; }
  .inv li { display: flex; justify-content: space-between; align-items: center; min-height: 44px; border-bottom: 1px solid var(--hair); } .ok { color: var(--fresh-2); }
  .rm { border: 0; background: none; color: var(--accent); }
  .alias { border-top: 1px solid var(--hair); padding: 8px 0; } .alias p { margin: 0 0 4px; }
</style>
