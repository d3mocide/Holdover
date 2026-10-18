<script>
  import { longDate } from './api.js';
  // A pointer to the weekly ODFW report; the report itself, in ODFW's words, is on the Reports tab.
  let { report, canReview = false, onreview, onopen } = $props();
  const rep = $derived(report?.report);
</script>

{#if rep}
  <div class="report">
    <button class="open" onclick={onopen}><span><strong>Weekly report</strong> · {longDate(rep.issued_on)}</span><span class="quiet small">Read it →</span></button>
    {#if rep.pending_review && canReview}<p class="quiet small">{rep.pending_review} item(s) awaiting your review. <button class="linkish" onclick={onreview}>Review</button></p>{/if}
  </div>
{/if}

<style>
  .small { font-size: 13px; margin: 0; }
  .report { border: 1px solid var(--hair); border-radius: 14px; padding: 0 12px; background: var(--glass-fill); }
  .open { width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px; border: 0; background: none; min-height: 48px; padding: 0; height: auto; text-align: left; }
  .report p { margin: 0 0 8px; }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0 4px; }
</style>
