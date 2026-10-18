<script>
  import { api, FRESH_LABEL, weekLabel, hhmm, longDate } from './api.js';
  import Conditions from './Conditions.svelte';
  import { db } from './db.js';
  import Icon from './Icon.svelte';
  let { id, onclose, onday, onlog } = $props();
  let mine = $state([]);
  let mineCatch = $state([]);
  let wb = $state(null);
  let error = $state('');

  // Scheduled weeks first (soonest first), then past weeks (newest first).
  const ordered = $derived(
    wb ? [...wb.stocking.filter((s) => s.freshness === 'upcoming').reverse(), ...wb.stocking.filter((s) => s.freshness !== 'upcoming')] : []
  );
  const fish = (s) => [s.legals && `${s.legals.toLocaleString()} legals`, s.trophy && `${s.trophy.toLocaleString()} trophy`].filter(Boolean).join(' + ') || `${s.total.toLocaleString()} fish`;

  $effect(() => {
    db.trips.where('waterbody_id').equals(id).filter((t) => !t.deleted).toArray().then(async (t) => {
      mine = t.sort((a, b) => (b.started_at ?? '').localeCompare(a.started_at ?? ''));
      mineCatch = (await db.catches.filter((c) => !c.deleted && mine.some((x) => x.uuid === c.trip_uuid)).toArray());
    });
  });
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

    <Conditions c={{ ...wb.conditions, waterbody_kind: wb.kind }} />

    <h3 class="eyebrow">Stocking</h3>
    <ul>
      {#each ordered as s (s.week_of)}
        <li class="srow">
          <span class="dot {s.freshness}" title={FRESH_LABEL[s.freshness]}></span>
          <span class="grow wk">{weekLabel(s.week_of)}</span>
          {#if s.freshness === 'upcoming'}<span class="tag">scheduled</span>{/if}
          <span class="fish">{fish(s)}</span>
        </li>
      {/each}
    </ul>
    <p class="quiet small">Weeks, not days. The schedule can change without notice. As of {hhmm(wb.stocking[0]?.scraped_at)}.</p>

    {#if wb.report_items?.length}
      <h3 class="eyebrow">From the weekly report</h3>
      {#each wb.report_items as r}
        <blockquote>
          <p class="small">{r.note}{r.rating !== 'unknown' ? ` (${r.rating})` : ''}</p>
          <p class="quiet small">ODFW, {longDate(r.issued_on)}: “{r.source_sentence}”</p>
        </blockquote>
      {/each}
    {/if}

    {#if mine.length}
      <h3 class="eyebrow">Your trips here</h3>
      <p class="small">{mine.length} trip{mine.length === 1 ? '' : 's'}, last {longDate(mine[0].started_at?.slice(0, 10))}.
        {Object.entries(mineCatch.reduce((a, c) => ({ ...a, [c.species ?? 'unspecified']: (a[c.species ?? 'unspecified'] ?? 0) + (c.count || 0) }), {})).map(([k, v]) => `${v} ${k}`).join(', ')}</p>
    {/if}

    <div class="actions">
      <button class="primary" onclick={() => onday(wb.id)}>Plan the day</button>
      <button onclick={() => onlog(wb.id)}>Log a trip here</button>
      {#if wb.regs_url}
        <a class="btn" href={wb.regs_url} target="_blank" rel="noopener">Official regulations on ODFW <Icon name="external" /></a>
      {/if}
    </div>
  {/if}
</aside>

<style>
  .sheet { position: relative; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; height: 100%; }
  h2 { font-size: 22px; letter-spacing: -0.01em; padding-right: 48px; }
  h3 { margin-top: 10px; }
  .close { position: absolute; top: 8px; right: 8px; padding: 0; }
  .small { font-size: 13px; margin: 0; }
  ul { list-style: none; margin: 0; padding: 0; }
  .srow { display: flex; gap: 10px; align-items: center; min-height: 40px; border-bottom: 1px solid var(--hair); }
  .wk { white-space: nowrap; }
  .tag { font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fresh-1); border: 1px solid color-mix(in srgb, var(--fresh-1) 45%, transparent); border-radius: 999px; padding: 1px 8px; }
  .fish { min-width: 96px; font-size: 13px; color: var(--text-quiet); text-align: right; font-variant-numeric: tabular-nums; }
  .grow { flex: 1; }
  blockquote { margin: 0; padding: 4px 0 4px 12px; border-left: 2px solid var(--fresh-2); background: linear-gradient(90deg, var(--glow-1), transparent 70%); border-radius: 2px; }
  blockquote p { margin: 2px 0; }
  .actions { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
</style>
