<script>
  import Icon from './Icon.svelte';
  import { api, longDate } from './api.js';
  // The weekly ODFW Recreation Report, reposted as ODFW wrote it (nothing generated), one zone at a time.
  let { onselect = null } = $props();
  let data = $state(null);
  let error = $state('');
  let zone = $state('willamette');
  let issue = $state(null);
  $effect(() => {
    const d = issue;
    error = '';
    api.reportsAll(d).then((v) => { data = v; if (!v.zones.some((z) => z.zone === zone)) zone = v.zones[0]?.zone ?? 'willamette'; }).catch((e) => (error = e.message));
  });
  const current = $derived(data?.zones.find((z) => z.zone === zone));
</script>

<section class="panel" aria-label="Weekly reports">
  <header>
    <div class="row"><span class="ico"><Icon name="reports" size={26} /></span>
      <div><h1>Weekly <span class="ov">reports</span></h1>
        <p class="quiet small">ODFW's Recreation Report, in ODFW's own words.{data?.issued_on ? ` Issued ${longDate(data.issued_on)}.` : ''}</p></div>
    </div>
    {#if data && data.available.length > 1}
      <label class="small" for="issue">Issue</label>
      <select id="issue" value={data.issued_on} onchange={(e) => (issue = e.currentTarget.value)}>
        {#each data.available as d}<option value={d}>{longDate(d)}</option>{/each}
      </select>
    {/if}
  </header>

  {#if error}<p class="notice" role="alert">Couldn't load the reports ({error}).</p>{/if}

  {#if data && data.zones.length}
    <div class="tabs" role="group" aria-label="Zone">
      {#each data.zones as z (z.zone)}
        <button class="tab" aria-pressed={zone === z.zone} onclick={() => (zone = z.zone)}>{z.label}</button>
      {/each}
    </div>
    {#if current}
      <article>
        <h2 class="eyebrow">{current.label} zone</h2>
        {#each current.bullets as b}<p class="bullet">{b}</p>{:else}<p class="quiet">ODFW listed nothing for this zone this week.</p>{/each}
      </article>
    {/if}
    <footer class="quiet small">
      Source: Oregon Department of Fish &amp; Wildlife{data.fetched_at ? `, fetched ${longDate(data.fetched_at.slice(0, 10))}` : ''}.
      <a href={data.source_url} target="_blank" rel="noopener">Read the original report on ODFW <Icon name="external" size={14} /></a><br />
      Conditions change. This page does not state regulations: check ODFW's e-regulations before you fish.
    </footer>
  {:else if data}
    <p class="quiet">No report has been fetched yet. It is checked a few times on Wednesday to Friday, when ODFW publishes it.</p>
  {:else if !error}<p class="quiet">Loading…</p>{/if}
</section>

<style>
  .panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; height: 100%; }
  header { display: flex; flex-direction: column; gap: 6px; }
  .row { display: flex; gap: 14px; align-items: center; }
  .ico { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; color: var(--fresh-1); background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } .ov { color: var(--fresh-1); }
  .small { font-size: 13px; margin: 2px 0 0; }
  .tabs { display: flex; gap: 20px; border-bottom: 1px solid var(--hair); overflow-x: auto; flex: none; }
  .tab { flex: none; border: 0; border-bottom: 2px solid transparent; border-radius: 0; background: none; min-height: 44px; padding: 0 2px; margin-bottom: -1px; color: var(--text-quiet); font-weight: 500; }
  .tab[aria-pressed='true'] { color: var(--text); border-bottom-color: var(--accent); }
  article { display: flex; flex-direction: column; gap: 4px; }
  article h2 { margin: 6px 0 2px; }
  .bullet { margin: 0; padding: 12px 14px; background: var(--glass-fill); border: 1px solid var(--hair); border-radius: 14px; line-height: 1.5; }
  .notice { background: var(--glass-fill); border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; margin: 0; }
  footer { margin-top: auto; padding-top: 8px; line-height: 1.6; }
</style>
