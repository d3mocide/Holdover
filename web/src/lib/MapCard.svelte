<script>
  import Icon from './Icon.svelte';
  import { FISHERIES } from './api.js';
  import { clockText } from './clock.svelte.js';
  // Map: "where should I go today?" A short list of today's best bets over the map. Tap one to fly there and open it.
  import ZonePicker from './ZonePicker.svelte';
  let { spots, zones = [], zone = 'willamette', onzone = () => {}, fishery, onfishery, selectedId = null, onselect, onplan, error = '' } = $props();
  const narrow = typeof matchMedia === 'function' && matchMedia('(max-width: 899px)').matches;
  let open = $state(!narrow);  // collapsed to a bar on a phone so the map stays clear
  const top = $derived((spots?.spots ?? []).slice(0, 5));
</script>

<section class="mapcard" class:closed={!open} aria-label="Best bets today">
  <button class="head" aria-expanded={open} onclick={() => (open = !open)}>
    <span class="t"><Icon name="fish" size={16} /> <strong>Best bets today</strong></span>
    <span class="chev" class:up={open}><Icon name="trend_steady" size={16} /></span>
  </button>
  {#if open}
    <ZonePicker {zones} {zone} {onzone} />
    <div class="chips" role="group" aria-label="Fishery">
      {#each FISHERIES as [k, label]}<button class="chip" aria-pressed={fishery === k} onclick={() => onfishery(k)}>{label}</button>{/each}
    </div>
    {#if error}<p class="small notice" role="alert">Couldn't rank spots ({error}).</p>{/if}
    <ul>
      {#each top as s, i (s.waterbody.id)}
        <li><button class="row" class:sel={s.waterbody.id === selectedId} onclick={() => onselect(s.waterbody.id)}>
          <span class="mono rank">{i + 1}</span>
          <span class="body"><span class="name">{s.waterbody.name}</span><span class="why small quiet">{clockText(s.explanation.text)}</span></span>
          <span class="mono score" class:hi={s.score >= 60} class:mid={s.score >= 45 && s.score < 60}>{Math.round(s.score)}</span>
        </button></li>
      {:else}
        {#if spots}<li class="quiet small pad">Nothing ranks for this fishery today yet.</li>{:else}<li class="quiet small pad">Ranking…</li>{/if}
      {/each}
    </ul>
    <button class="plan" onclick={onplan}>Plan ahead <Icon name="trend_steady" size={14} /></button>
  {/if}
</section>

<style>
  .mapcard { position: absolute; z-index: 2; left: 112px; top: 16px; width: min(380px, calc(100% - 144px)); max-height: calc(100% - 32px); overflow-y: auto;
    border-radius: 20px; padding: 6px 10px 8px; background: var(--glass-dense); backdrop-filter: var(--glass-blur-dense); -webkit-backdrop-filter: var(--glass-blur-dense);
    border: 1px solid var(--glass-line); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06); display: flex; flex-direction: column; gap: 4px; }
  .head { width: 100%; display: flex; justify-content: space-between; align-items: center; border: 0; background: none; min-height: 44px; padding: 0 4px; height: auto; }
  .t { display: inline-flex; align-items: center; gap: 8px; } .t :global(svg) { color: var(--fresh-1); }
  .chev { display: inline-flex; color: var(--text-quiet); transform: rotate(90deg); transition: transform 0.15s; } .chev.up { transform: rotate(-90deg); }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { padding: 0 12px; min-height: 40px; font-size: 12.5px; }
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
    .mapcard { left: 16px; right: 16px; top: auto; bottom: 16px; width: auto; max-height: 52%; }
  }
</style>
