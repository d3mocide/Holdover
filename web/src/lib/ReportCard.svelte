<script>
  import { longDate } from './api.js';
  import { hhmm } from './clock.svelte.js';
  // The weekly ODFW report: the original wording first, with the generated summary (if any) labelled as such.
  let { report, canReview = false, onreview } = $props();
  const rep = $derived(report?.report);
</script>

{#if rep}
  <details class="report">
    <summary class="small"><strong>From the weekly report</strong> · {longDate(rep.issued_on)}</summary>
    {#if rep.digest}
      <p class="digest">{rep.digest.text}</p>
      <p class="quiet small">Summary generated {hhmm(rep.digest.as_of)} by a local model from the report text. Check the original wording.</p>
    {/if}
    <p class="small quiet">{rep.digest ? 'Original ODFW wording' : 'ODFW wording (no summary yet)'}</p>
    {#each rep.bullets as b}<p class="small bullet">{b}</p>{/each}
    <a class="small" href={rep.source_url} target="_blank" rel="noopener">Read the original report on ODFW</a>
    {#if rep.pending_review && canReview}<p class="quiet small">{rep.pending_review} item(s) awaiting your review. <button class="linkish" onclick={onreview}>Review</button></p>{/if}
  </details>
{/if}

<style>
  .small { font-size: 13px; margin: 0; }
  .report { border: 1px solid var(--hair); border-radius: 14px; padding: 4px 12px; background: var(--glass-fill); }
  .report summary { min-height: 44px; display: flex; align-items: center; cursor: pointer; }
  .digest { margin: 4px 0; } .bullet { margin: 6px 0; } .report p { margin: 4px 0; }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0 4px; }
</style>
