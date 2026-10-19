<script>
  import Icon from './Icon.svelte';
  import PageIcon from './PageIcon.svelte';
  import { FISHERIES } from './api.js';
  import { clockText } from './clock.svelte.js';
  // Browse rivers, favorites and today's best bets. A selection focuses its stored map location and opens details.
  import ZonePicker from './ZonePicker.svelte';
  import { prefs, isFavorite } from './auth.svelte.js';
  import { findWaters, evidenceText } from './waterSearch.js';
  let { hidden = false, spots, waters = [], zones = [], zone = 'willamette', onzone = () => {}, fishery, onfishery, selectedId = null, onselect, onplan, error = '' } = $props();
  const narrow = typeof matchMedia === 'function' && matchMedia('(max-width: 899px)').matches;
  let open = $state(!narrow);  // collapsed to a bar on a phone so the map stays clear
  const top = $derived((spots?.spots ?? []).slice(0, 5));
  let mode = $state('bets'), query = $state('');
  const browsing = $derived(mode !== 'bets' || query.trim());
  const matches = $derived(findWaters(waters, { query, mode, zone, favorites: prefs.favorites }));
  const zoneName = (key) => zones.find((z) => z.key === key)?.label ?? key ?? '';
</script>

<section class="mapcard" class:closed={!open} class:hidden aria-label="Explore waters">
  <div class="heading">
  <button class="head" aria-label="Explore waters" aria-expanded={open} onclick={() => (open = !open)}>
    <span class="t"><PageIcon name="map" /> <strong>Explore waters</strong></span>
    <span class="chev" class:up={open}><Icon name="trend_steady" size={16} /></span>
  </button>
  {#if !open}<button class="quick" onclick={() => { open = true; mode = 'rivers'; query = ''; }}>Rivers</button>{/if}
  </div>
  {#if open}
    <ZonePicker {zones} {zone} {onzone} />
    <label class="sr-only" for="water-search">Search all waters</label>
    <input id="water-search" type="search" bind:value={query} placeholder="Find a river, lake or pond…" />
    <div class="selector-tabs" role="group" aria-label="Browse waters">
      {#each [['bets', 'Best bets'], ['rivers', 'Rivers'], ['favorites', 'Favorites']] as [key, label]}
        <button class="selector-tab" aria-pressed={mode === key} onclick={() => { mode = key; query = ''; }}>{label}</button>
      {/each}
    </div>
    {#if browsing}
      <p class="small quiet" role="status">{matches.length} water{matches.length === 1 ? '' : 's'} · {query.trim() || mode === 'favorites' ? 'all zones' : zoneName(zone)}</p>
      <ul class="water-results">
        {#each matches as w (w.id)}
          <li><button class="row" class:sel={w.id === selectedId} onclick={() => onselect(w.id)}>
            <Icon name={w.kind === 'river' ? 'flow' : 'map'} size={18} />
            <span class="body"><span class="name">{w.name}{#if isFavorite(w.id)} <Icon name="star_fill" size={14} />{/if}</span>
              <span class="small quiet">{w.kind} · {zoneName(w.zone)}{w.lat == null || w.lon == null ? ' · No map pin yet' : ''}</span></span>
          </button></li>
        {:else}<li class="quiet small pad">{mode === 'favorites' && !query.trim() ? 'Star a waterbody to keep it here.' : 'No waters match. Try a name or zone.'}</li>{/each}
      </ul>
    {:else}
    <div class="chips" role="group" aria-label="Fishery">
      {#each FISHERIES as [k, label]}<button class="chip" aria-pressed={fishery === k} onclick={() => onfishery(k)}>{label}</button>{/each}
    </div>
    {#if error}<p class="small notice" role="alert">Couldn't rank spots ({error}).</p>{/if}
    <ul>
      {#each top as s, i (s.waterbody.id)}
        <li><button class="row" class:sel={s.waterbody.id === selectedId} onclick={() => onselect(s.waterbody.id)}>
          <span class="mono rank">{i + 1}</span>
          <span class="body"><span class="name">{s.waterbody.name}</span><span class="why small quiet">{clockText(s.explanation.text)}</span><span class="small quiet">{evidenceText(s.coverage)}</span></span>
          <span class="mono score" class:hi={s.score >= 60} class:mid={s.score >= 45 && s.score < 60}>{Math.round(s.score)}</span>
        </button></li>
      {:else}
        {#if spots}<li class="quiet small pad">Nothing ranks for this fishery today yet.</li>{:else}<li class="quiet small pad">Ranking…</li>{/if}
      {/each}
    </ul>
    <button class="plan" onclick={onplan}>Plan ahead <Icon name="trend_steady" size={14} /></button>
    {/if}
  {/if}
</section>

<style>
  .mapcard { position: absolute; z-index: 2; left: 96px; top: 16px; width: min(380px, calc(100% - 144px)); max-height: calc(100% - 32px); overflow-y: auto;
    border-radius: 20px; padding: 16px; background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense);
    border: 1px solid var(--glass-line); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06); display: flex; flex-direction: column; gap: 10px; }
  .head { width: 100%; display: flex; justify-content: space-between; align-items: center; border: 0; background: none; min-height: 44px; padding: 0; height: auto; text-align: left; gap: 10px; }
  .mapcard.hidden { display: none; }
  .heading { display: flex; align-items: center; gap: 8px; } .quick { min-height: 44px; border: 0; background: none; color: var(--gauge); }
  .t { display: inline-flex; align-items: center; gap: 14px; min-width: 0; }
  .t strong { font-size: 20px; line-height: 1.25; }
  .mapcard.closed { padding: 8px 12px; }
  .closed .t strong { font-size: 15px; } .t :global(svg) { color: var(--fresh-1); }
  .chev { display: inline-flex; color: var(--text-quiet); transform: rotate(90deg); transition: transform 0.15s; } .chev.up { transform: rotate(-90deg); }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .selector-tabs { gap: 0; }
  .selector-tabs button { flex: 1; font-size: 13px; }
  .chip { padding: 0 12px; min-height: 44px; font-size: 12.5px; }
  input { width: 100%; min-height: 44px; }
  .water-results { max-height: 340px; overflow-y: auto; }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
  .row { width: 100%; display: flex; gap: 10px; align-items: flex-start; text-align: left; border: 0; border-top: 1px solid var(--hair); background: none; padding: 8px 4px; min-height: 52px; height: auto; justify-content: flex-start; }
  .row.sel .name { color: var(--fresh-1); }
  .rank { color: var(--text-quiet); min-width: 16px; padding-top: 2px; }
  .body { display: flex; flex-direction: column; flex: 1; min-width: 0; }
  .name { font-weight: 500; }
  .why { display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .small { font-size: 12.5px; margin: 0; } .pad { padding: 10px 4px; }
  .score { font-size: 22px; font-weight: 600; line-height: 1; color: var(--text-quiet); padding-top: 2px; }
  .score.hi { color: var(--fresh-1); } .score.mid { color: var(--fresh-2); }
  .plan { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 44px; border: 0; border-top: 1px solid var(--hair); background: none; color: var(--fresh-1); }
  .notice { border: 1px solid var(--accent); border-radius: 8px; padding: 6px 10px; }
  @media (max-width: 899px) {
    .mapcard { left: 16px; right: 16px; top: auto; bottom: 16px; width: auto; max-height: 68%; background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; }
  }
</style>
