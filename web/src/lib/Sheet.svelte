<script>
  import { api, FRESH_LABEL, weekLabel, hhmm } from './api.js';
  import Icon from './Icon.svelte';
  let { id, onclose } = $props();
  let wb = $state(null);
  let error = $state('');

  // Scheduled weeks first (soonest first), then past weeks (newest first).
  const ordered = $derived(
    wb ? [...wb.stocking.filter((s) => s.freshness === 'upcoming').reverse(), ...wb.stocking.filter((s) => s.freshness !== 'upcoming')] : []
  );
  const fish = (s) => [s.legals && `${s.legals.toLocaleString()} legals`, s.trophy && `${s.trophy.toLocaleString()} trophy`].filter(Boolean).join(' + ') || `${s.total.toLocaleString()} fish`;

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
    <p class="quiet small">{wb.stocking[0]?.zone_office ?? wb.zone}</p>

    <h3 class="quiet small">Stocking</h3>
    <ul>
      {#each ordered as s (s.week_of)}
        <li class="srow">
          <span class="dot {s.freshness}" title={FRESH_LABEL[s.freshness]}></span>
          <span class="grow">{weekLabel(s.week_of)}
            <span class="quiet small">{s.freshness === 'upcoming' ? 'scheduled' : ''}</span></span>
          <span class="mono">{fish(s)}</span>
        </li>
      {/each}
    </ul>
    <p class="quiet small">Weeks, not days. The schedule can change without notice. As of {hhmm(wb.stocking[0]?.scraped_at)}.</p>

    <div class="actions">
      <button class="primary" disabled title="Journal arrives in a later phase">Log a trip here</button>
      {#if wb.regs_url}
        <a class="btn" href={wb.regs_url} target="_blank" rel="noopener">Official regulations on ODFW <Icon name="external" /></a>
      {/if}
    </div>
  {/if}
</aside>

<style>
  .sheet { position: relative; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; height: 100%; }
  h2 { font-size: 20px; padding-right: 48px; }
  .close { position: absolute; top: 8px; right: 8px; padding: 0; }
  .small { font-size: 13px; margin: 0; }
  ul { list-style: none; margin: 0; padding: 0; }
  .srow { display: flex; gap: 10px; align-items: center; min-height: 40px; border-bottom: 1px solid var(--line); }
  .grow { flex: 1; }
  .actions { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
</style>
