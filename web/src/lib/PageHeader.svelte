<script>
  import PageIcon from './PageIcon.svelte';
  let { icon, title, accent = '', description = '', color = 'var(--fresh-1)', children } = $props();
</script>

<div class="page-header">
  <div class="title-row">
    <div class="title"><PageIcon name={icon} {color} /><h1>{title}{#if accent}{' '}<span>{accent}</span>{/if}</h1></div>
    {#if children}{@render children()}{/if}
  </div>
  {#if description}<p class="quiet">{description}</p>{/if}
</div>

<style>
  .page-header { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
  .title-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 48px; }
  .title { display: flex; align-items: center; gap: 14px; min-width: 0; }
  h1 { font-size: 24px; letter-spacing: -0.01em; line-height: 1.25; }
  h1 span { color: var(--fresh-1); }
  p { margin: 0; font-size: 13px; line-height: 1.5; }
</style>
