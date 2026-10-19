<script>
  // Which ODFW zone every view follows. Shown only when more than one zone is available.
  //   variant "map":   the pill on the map (desktop; the shell positions it)
  //   variant "panel": inside a panel, for a phone where the map is covered (hidden on wider screens, where the map pill is)
  let { zones, zone, onzone, variant = 'panel' } = $props();
</script>

{#if zones.length > 1}
  <label class="zp {variant}"><span class="sr-only">Zone</span>
    <select value={zone} onchange={(e) => onzone(e.currentTarget.value)}>
      {#each zones as z (z.key)}<option value={z.key}>{z.label} zone</option>{/each}
    </select>
  </label>
{/if}

<style>
  .zp { margin: 0; display: block; }
  select { min-height: 44px; font-size: 13px; }
  .map select { width: 100%; border: 0; background: transparent; padding: 0 28px 0 14px; font-weight: 500; }
  .panel { display: none; }
  .panel select { width: auto; padding: 0 28px 0 12px; }
  @media (max-width: 899px) { .panel { display: inline-block; margin: 2px 0 12px; } }
</style>
