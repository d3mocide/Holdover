<script>
  import { api, getToken, setToken } from './api.js';
  let { theme, onTheme, onChanged } = $props();
  const themes = [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']];
  let token = $state(getToken());
  let aliases = $state([]);
  let items = $state([]);
  let itemChoice = $state({});
  let wbs = $state([]);
  let choice = $state({});
  let msg = $state('');
  let health = $state(null);

  async function load() {
    msg = '';
    health = await api.health().catch(() => null);
    if (!getToken()) { aliases = []; return; }
    try {
      [aliases, wbs, items] = await Promise.all([api.aliases(), api.waterbodies(), api.reviewItems()]);
    } catch (e) { msg = `Review queue unavailable (${e.message}). Check the token.`; }
  }
  $effect(() => { load(); });

  function saveToken() { setToken(token.trim()); load(); }
  async function confirm(a) {
    const wb = Number(choice[a.id] ?? a.proposed_waterbody?.id);
    if (!wb) { msg = 'Pick a waterbody first.'; return; }
    try { await api.confirm(a.id, wb); await load(); onChanged?.(); } catch (e) { msg = `Couldn't confirm (${e.message}).`; }
  }
  async function decide(i, accept) {
    try {
      if (accept) await api.acceptItem(i.id, Number(itemChoice[i.id] || i.waterbody?.id) || null);
      else await api.rejectItem(i.id);
      await load(); onChanged?.();
    } catch (e) { msg = `Couldn't save (${e.message}).`; }
  }
  async function runReports() {
    msg = 'Running…';
    try { const r = await api.runReports(); msg = `Report fetch ${r.fetch.ok ? 'ok' : 'failed'}; ${r.llm.extracted ?? 0} extracted, ${r.llm.pending ?? 0} pending (LLM ${r.llm.llm ?? 'error'}).`; await load(); onChanged?.(); }
    catch (e) { msg = `Couldn't run (${e.message}).`; }
  }
  async function runNow() {
    msg = 'Running…';
    try { const r = await api.runStocking(); msg = r.ok ? `Fetched ${r.pages} page(s), ${r.rows_inserted} new rows.` : 'Fetch failed: see source status.'; await load(); onChanged?.(); }
    catch (e) { msg = `Couldn't run (${e.message}).`; }
  }
</script>

<div class="settings">
  <h1>Settings</h1>

  <fieldset>
    <legend>Theme</legend>
    {#each themes as [k, label]}
      <label class="opt"><input type="radio" name="theme" value={k} checked={theme === k} onchange={() => onTheme(k)} /> {label}</label>
    {/each}
  </fieldset>

  <section class="card">
    <h2>Source status</h2>
    {#if health}
      {#each Object.entries(health.sources) as [name, s]}
        <p class="row"><span>{name}</span>
          <span class="mono">{s.stale ? 'STALE' : 'ok'}{s.last_success ? ` · ${new Date(s.last_success).toLocaleString()}` : ' · never'}</span></p>
        {#if s.last_error}<p class="quiet small">Last error: {s.last_error}</p>{/if}
      {/each}
    {:else}<p class="quiet">Server unreachable.</p>{/if}
  </section>

  <section class="card">
    <h2>Admin</h2>
    <label for="tok">Bearer token (stored on this device)</label>
    <div class="row gap">
      <input id="tok" type="password" bind:value={token} autocomplete="off" />
      <button onclick={saveToken}>Save</button>
    </div>
    {#if getToken()}
      <div class="row gap top"><button onclick={runNow}>Fetch stocking now</button><button onclick={runReports}>Fetch report now</button></div>
      <h3>Report items to review ({items.length})</h3>
      {#if !items.length}<p class="quiet small">Nothing waiting.</p>{/if}
      {#each items as i (i.id)}
        <div class="alias">
          <p><strong>{i.waterbody_raw}</strong> <span class="quiet small">· {i.zone} · {i.species || 'species not stated'} · {i.rating}</span></p>
          <p class="quiet small">“{i.source_sentence}”</p>
          <div class="row gap">
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
          <div class="row gap">
            <select aria-label="Waterbody for {a.alias_text}" bind:value={choice[a.id]}>
              <option value="">{a.proposed_waterbody ? 'Use proposal' : 'Choose…'}</option>
              {#each wbs as w}<option value={w.id}>{w.name}</option>{/each}
            </select>
            <button onclick={() => confirm(a)}>Confirm</button>
          </div>
        </div>
      {/each}
    {/if}
    {#if msg}<p role="status" class="small">{msg}</p>{/if}
  </section>
</div>

<style>
  .settings { padding: 16px; display: flex; flex-direction: column; gap: 16px; max-width: 640px; overflow-y: auto; height: 100%; }
  fieldset { border: 1px solid var(--line); border-radius: 12px; }
  .opt { display: flex; align-items: center; gap: 10px; min-height: 44px; color: var(--text); margin: 0; }
  .opt input { width: 20px; height: 20px; accent-color: var(--accent); }
  h1 { font-size: 22px; } h2 { font-size: 16px; margin-bottom: 8px; } h3 { font-size: 14px; margin: 12px 0 4px; }
  .row { display: flex; justify-content: space-between; gap: 12px; margin: 4px 0; flex-wrap: wrap; }
  .gap { justify-content: flex-start; } .top { margin-top: 12px; }
  .small { font-size: 13px; margin: 0; }
  .alias { border-top: 1px solid var(--line); padding: 8px 0; }
  .alias p { margin: 0 0 4px; }
</style>
