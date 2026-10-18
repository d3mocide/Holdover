<script>
  import { icons } from './icons.js';
  let { name, label = '', size = 22 } = $props();
</script>

<svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden={label ? undefined : 'true'}
  aria-label={label || undefined} role={label ? 'img' : undefined}>
  {@html icons[name] ?? ''}
</svg>

<style>
  svg :global(.a) { fill: currentColor; opacity: 0.28; stroke: none; }
</style>
