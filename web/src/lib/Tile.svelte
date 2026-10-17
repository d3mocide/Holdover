<script>
  let { label, value = null, sub = '', stale = false, asof = '' } = $props();
</script>
<div class="tile">
  <span class="quiet label">{label}</span>
  <span class="mono val">{value ?? 'No data'}</span>
  {#if sub}<span class="quiet sub">{sub}</span>{/if}
  <span class="quiet sub">{#if stale}<b class="stale">Stale</b>{/if} {asof}</span>
</div>
<style>
  .tile { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .label { font-size: 12px; } .val { font-size: 18px; font-weight: 500; } .sub { font-size: 12px; }
  .stale { color: var(--accent); border: 1px solid var(--accent); border-radius: 4px; padding: 0 4px; font-weight: 500; }
</style>
