<script>
  import Icon from './Icon.svelte';
  // The rounded badge beside a page title, so every page header looks the same.
  let { name, color = 'var(--fresh-1)' } = $props();
</script>

<span class="badge" style:color aria-hidden="true"><Icon {name} size={26} /></span>

<style>
  .badge { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; background: var(--glass-fill); box-shadow: inset 0 0 0 1px var(--hair); flex: none; }
</style>
