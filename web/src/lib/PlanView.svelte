<script>
  import Icon from './Icon.svelte';
  import SpotList from './SpotList.svelte';
  import ReportCard from './ReportCard.svelte';
  import { api, dayLabel, isoDay, localDay, weekLabel, FISHERIES } from './api.js';
  import { homeForRequests } from './auth.svelte.js';
  import { hhmm } from './clock.svelte.js';
  import { monthLabel, monthShort, monthRange, weekSummary } from './scheduleText.js';
  import { weekLabelYear } from './stockingGroups.js';
  // Plan: look ahead. "Next 7 days" ranks spots day by day; "Further out" browses ODFW's published stocking schedule
  // (about a year ahead) by month. The Map tab is for "where today?"; this is for "when and where next?".
  let { data, report, fishery, onfishery, offset, onoffset, selectedId, onselect, onreview, canReview, onreports, error } = $props();
  let mode = $state('week');

  // ---- next 7 days: one ranking per day, fetched together
  let outlook = $state([]);
  let outlookError = $state('');
  $effect(() => {
    const f = fishery, home = homeForRequests();
    outlookError = '';
    Promise.all([0, 1, 2, 3, 4, 5, 6].map((o) => api.spots(isoDay(o), f, home))).then((v) => (outlook = v)).catch((e) => (outlookError = e.message));
  });
  const fresh = $derived(Object.fromEntries((data?.features ?? []).filter((f) => f.properties.layer === 'stocking').map((f) => [f.properties.id, f.properties])));
  const unlocated = $derived(data?.meta.needs_coords ?? []);

  // ---- further out: the published schedule, by month
  let months = $state([]);
  let month = $state(null);
  let sched = $state(null);
  let schedError = $state('');
  $effect(() => {
    if (mode !== 'out' || months.length) return;
    api.schedule().then((v) => { months = v.months; month = v.months[0]?.month ?? null; }).catch((e) => (schedError = e.message));
  });
  $effect(() => {
    if (mode !== 'out' || !month) return;
    const [a, b] = monthRange(month);
    schedError = '';
    api.schedule(a, b).then((v) => (sched = v)).catch((e) => (schedError = e.message));
  });
  // The schedule is for looking ahead: this week onward (a month's earlier weeks have already happened).
  const mondayIso = isoDay(-((new Date().getDay() + 6) % 7));
  const weeksAhead = $derived((sched?.weeks ?? []).filter((w) => w.week_of >= mondayIso));
  const top3 = (day) => (day?.spots ?? []).slice(0, 3);
</script>

<section class="panel" aria-label="Plan ahead">
  <header>
    <div class="row">
      <h1>Plan <span class="ov">ahead</span></h1>
      <span class="quiet mono small">{data?.meta.as_of ? `Synced ${hhmm(data.meta.as_of)}` : 'Not synced'}</span>
    </div>
    <p class="quiet small">Willamette zone</p>
    <div class="tabs" role="group" aria-label="Planning range">
      <button class="tab" aria-pressed={mode === 'week'} onclick={() => (mode = 'week')}>Next 7 days</button>
      <button class="tab" aria-pressed={mode === 'out'} onclick={() => (mode = 'out')}>Further out</button>
    </div>
  </header>

  {#if error}<p class="notice" role="alert">Couldn't load map data ({error}).</p>{/if}

  {#if mode === 'week'}
    <div class="chips first" role="group" aria-label="Fishery">
      {#each FISHERIES as [k, label]}<button class="chip" aria-pressed={fishery === k} onclick={() => onfishery(k)}>{label}</button>{/each}
    </div>
    <ReportCard {report} {canReview} {onreview} onopen={onreports} />
    {#if outlookError}<p class="notice" role="alert">Couldn't rank spots ({outlookError}).</p>{/if}
    <ul class="days">
      {#each [0, 1, 2, 3, 4, 5, 6] as o (o)}
        {@const day = outlook[o]}
        <li class="day" class:open={offset === o}>
          <button class="dayhead" aria-expanded={offset === o} onclick={() => onoffset(o)}>
            <span class="dl"><strong>{dayLabel(o)}</strong></span>
            <span class="tops small quiet">
              {#if day}{#each top3(day) as s, i}{i ? ' · ' : ''}{s.waterbody.name} <span class="mono">{Math.round(s.score)}</span>{:else}Nothing ranked{/each}{:else}Ranking…{/if}
            </span>
            <span class="chev" class:up={offset === o}><Icon name="trend_steady" size={16} /></span>
          </button>
          {#if offset === o && day}
            <div class="daybody">
              <SpotList spots={day.spots} {fresh} {selectedId} {onselect} />
              {#if !day.spots.length}<p class="quiet small">Nothing matches this fishery and day yet. Stocking is the main trout signal; steelhead and warmwater lists grow as you accept report items.</p>{/if}
            </div>
          {/if}
        </li>
      {/each}
    </ul>
    {#if unlocated.length}
      <details>
        <summary class="small">{unlocated.length} stocked, no map location yet</summary>
        <ul class="plain small">
          {#each unlocated as u (u.id)}<li>{u.name} <span class="quiet">· {weekLabel(u.last_week ?? u.next_week)}</span></li>{/each}
        </ul>
      </details>
    {/if}
    {#if data?.meta.unconfirmed_aliases}
      <p class="notice small">
        {data.meta.unconfirmed_aliases} stocking label(s) need review and are not shown.
        {#if canReview}<button class="linkish" onclick={onreview}>Review</button>{/if}
      </p>
    {/if}
    <footer class="quiet small">Scores are starting points, not validated. Forecasts reach about a week out. Check ODFW for regulations.</footer>
  {:else}
    <p class="small quiet intro">ODFW's published stocking schedule for stocked trout, by week. It runs about a year ahead and can change without notice.</p>
    {#if schedError}<p class="notice" role="alert">Couldn't load the schedule ({schedError}).</p>{/if}
    {#if months.length}
      <div class="chips months" role="group" aria-label="Month">
        {#each months as m (m.month)}
          <button class="chip" aria-pressed={month === m.month} onclick={() => (month = m.month)} title={`${m.waterbodies} waterbodies, ${m.fish.toLocaleString('en-US')} fish`}>{monthShort(m.month)}</button>
        {/each}
      </div>
    {/if}
    {#if sched && month}
      <h2 class="small quiet">{monthLabel(month)}: {weeksAhead.length ? `${weeksAhead.length} scheduled week${weeksAhead.length === 1 ? '' : 's'}` : 'nothing scheduled yet'}</h2>
      <ul class="weeks">
        {#each weeksAhead as w, i (w.week_of)}
          <li class="wk">
            <details open={i === 0}>
              <summary><strong>{weekLabelYear(w.week_of)}</strong> <span class="quiet small">· {weekSummary(w)}</span></summary>
              <ul class="wbs">
                {#each w.waterbodies as r (r.id)}
                  <li><button class="wbrow" class:sel={r.id === selectedId} onclick={() => onselect(r.id)}>
                    <span class="grow">{r.name}</span>
                    <span class="mono small quiet">{[r.legals && `${r.legals.toLocaleString('en-US')} legals`, r.trophy && `${r.trophy.toLocaleString('en-US')} trophy`].filter(Boolean).join(' + ') || `${r.total.toLocaleString('en-US')} fish`}</span>
                  </button></li>
                {/each}
              </ul>
            </details>
          </li>
        {/each}
      </ul>
      <footer class="quiet small">Weeks, not days. {sched.as_of ? `Schedule fetched ${localDay(sched.as_of)}. ` : ''}Check ODFW for regulations.</footer>
    {:else if !schedError}<p class="quiet small">Loading the schedule…</p>{/if}
  {/if}
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; }
  .row { display: flex; justify-content: space-between; align-items: baseline; }
  h1 { font-size: 24px; letter-spacing: -0.02em; } .ov { color: var(--fresh-1); } h2 { font-weight: 500; margin: 4px 0 0; }
  .small { font-size: 13px; margin: 0; } .intro { margin: 0; }
  .tabs { display: flex; gap: 22px; border-bottom: 1px solid var(--hair); margin-top: 8px; }
  .tab { border: 0; border-bottom: 2px solid transparent; border-radius: 0; background: none; min-height: 44px; padding: 0 2px; margin-bottom: -1px; color: var(--text-quiet); font-weight: 500; }
  .tab[aria-pressed='true'] { color: var(--text); border-bottom-color: var(--accent); }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; } .chips.first { margin-top: 2px; }
  .chip { padding: 0 12px; min-height: 44px; font-size: 13px; flex: none; }
  .months { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 6px; scroll-snap-type: x proximity; } .months .chip { scroll-snap-align: start; }
  ul { list-style: none; margin: 0; padding: 0; }
  ul.plain { list-style: disc; padding: 8px 0 0 16px; }
  .days { display: flex; flex-direction: column; gap: 6px; }
  .day { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); }
  .day.open { border-color: var(--fresh-1); }
  .dayhead { width: 100%; display: grid; grid-template-columns: 96px 1fr 24px; gap: 8px; align-items: center; text-align: left; border: 0; background: none; padding: 8px 12px; min-height: 52px; height: auto; justify-content: stretch; }
  .tops { min-width: 0; }
  .chev { display: inline-flex; color: var(--text-quiet); transform: rotate(90deg); transition: transform 0.15s; } .chev.up { transform: rotate(-90deg); }
  .daybody { padding: 0 8px 8px; }
  .weeks { display: flex; flex-direction: column; gap: 6px; }
  .wk { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); padding: 0 12px; }
  .wk summary { min-height: 48px; display: flex; align-items: center; gap: 6px; cursor: pointer; flex-wrap: wrap; }
  .wbs { padding-bottom: 6px; }
  .wbrow { width: 100%; display: flex; gap: 8px; align-items: center; justify-content: space-between; text-align: left; border: 0; background: none; border-top: 1px solid var(--hair); min-height: 44px; padding: 0 2px; height: auto; }
  .wbrow.sel { color: var(--fresh-1); } .grow { flex: 1; min-width: 0; }
  .notice { background: var(--glass-fill); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; margin: 0; }
  summary { cursor: pointer; }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0 4px; }
  footer { margin-top: auto; padding-top: 8px; }
</style>
