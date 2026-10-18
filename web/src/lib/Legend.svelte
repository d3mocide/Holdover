<script>
  import { markers } from './icons.js';
  let { theme } = $props();
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  let c = $state(null);
  $effect(() => {
    theme; // re-read the palette when the theme changes
    queueMicrotask(() => {
      c = { f1: css('--fresh-1'), f2: css('--fresh-2'), f3: css('--fresh-3'), gauge: css('--gauge'), accent: css('--accent'),
        warn: css('--warn'), text: css('--text'), bg: css('--bg'), ring: 'rgba(255,255,255,0.18)' };
    });
  });
  const mk = (name, main, extra) => markers[name]({ main, ring: c.ring, bg: c.bg, accent: c.accent }, extra);
  const items = $derived(c ? [
    ['stocking', c.f1, 'Stocked this week'], ['stocking', c.f2, 'Last 2 weeks'], ['stocking', c.f3, 'Older'],
    ['stocking_scheduled', c.f1, 'Scheduled'], ['gauge', c.gauge, 'Stream gauge'], ['advisory', c.accent, 'Algae advisory'],
    ['report', c.f1, 'Report rating', 4], ['journal', c.text, 'My trips & pins']
  ] : []);
</script>

<div class="legend-body">
  {#each items as [name, col, label, extra]}
    <span class="item"><svg width="24" height="24" viewBox="0 0 40 40" aria-hidden="true">{@html mk(name, col, extra)}</svg>{label}</span>
  {/each}
  <span class="note quiet">Larger pin, more fish stocked. Report chips show fish pips: more is better.</span>
</div>

<style>
  .legend-body { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px; padding: 8px 14px 12px; font-size: 12.5px; }
  .item { display: inline-flex; align-items: center; gap: 10px; white-space: nowrap; }
  .note { grid-column: 1 / -1; font-size: 11.5px; white-space: normal; max-width: 320px; }
</style>
