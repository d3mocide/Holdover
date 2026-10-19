<script>
  // Which ODFW zone every view follows. Shown only when more than one zone is available.
  let { zones, zone, onzone } = $props();
</script>

{#if zones.length > 1}
  <label class="zp"><span class="sr-only">Zone</span>
    <select value={zone} onchange={(e) => onzone(e.currentTarget.value)}>
      {#each zones as z (z.key)}<option value={z.key}>{z.label} zone</option>{/each}
    </select>
  </label>
{/if}

<style>
  .zp { margin: 0; display: inline-block; }
  select { min-height: 44px; width: auto; padding: 0 28px 0 12px; font-size: 13px; }
</style>
