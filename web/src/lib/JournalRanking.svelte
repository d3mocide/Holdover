<script>
  import { adviceState } from './journalAdvice.svelte.js';
</script>
<div class="ranking">
  <label><input type="checkbox" bind:checked={adviceState.enabled} /> Use my journal in rankings</label>
  <p class="quiet">Optional · all species · at least 3 comparable trips · up to ±5 points. Public data scores stay available. Your journal stays on this device for this comparison.</p>
  {#if adviceState.error}<p role="status">{adviceState.error} Public scores are shown.</p>{/if}
</div>
<style>
  .ranking{border:1px solid var(--hair);border-radius:14px;padding:8px 12px;background:var(--glass-fill);}
  label{display:flex;align-items:center;gap:10px;min-height:44px;font-size:13px;margin:0;}
  input{width:22px;height:22px;flex:none;accent-color:var(--primary);}
  p{font-size:12.5px;margin:0 0 4px;}
</style>
