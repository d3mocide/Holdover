<script>
  import Icon from './Icon.svelte';
  let { label, value = null, sub = '', stale = false, asof = '', icon = '' } = $props();
</script>
<div class="tile">
  <span class="eyebrow label">{#if icon}<Icon name={icon} size={14} />{/if}{label}</span>
  <span class="val" class:mono={/^[+\-−]?\d/.test(value ?? '')} class:empty={value == null}>{value ?? 'No data'}</span>
  {#if sub}<span class="quiet sub">{sub}</span>{/if}
  <span class="quiet sub">{#if stale}<b class="stale">Stale</b>{/if} {asof}</span>
</div>
<style>
  .tile { background: var(--glass-fill); border: 1px solid var(--hair); border-radius: 14px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .label { font-size: 10.5px; display: flex; align-items: center; gap: 6px; } .label :global(svg) { color: var(--fresh-2); } .val { font-size: 18px; font-weight: 500; line-height: 1.25; } .val.empty { color: var(--text-quiet); font-size: 15px; } .sub { font-size: 12px; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 0 4px; font-weight: 500; }
</style>
