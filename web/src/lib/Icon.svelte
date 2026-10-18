<script>
  let { name, label = '' } = $props();
  const paths = {
    map: 'M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14',
    plan: 'M4 6h16M4 12h16M4 18h10',
    journal: 'M6 3h12v18H6zM9 8h6M9 12h6',
    gauge: 'M12 3l7 9-7 9-7-9z',
    settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2',
    close: 'M6 6l12 12M18 6 6 18',
    layers: 'M12 3 3 8l9 5 9-5zM3 13l9 5 9-5',
    external: 'M14 4h6v6M20 4l-9 9M18 14v6H4V6h6'
  };
</script>

<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden={label ? undefined : 'true'}
  aria-label={label || undefined} role={label ? 'img' : undefined}>
  <path d={paths[name]} />
</svg>
