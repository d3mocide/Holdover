<script>
  let { title, phase, blurb } = $props();
</script>
<div class="ph"><h1>{title}</h1><p class="quiet">{blurb}</p><p class="quiet mono">Planned: {phase}</p></div>
<style>.ph { padding: 24px 16px; max-width: 520px; } h1 { font-size: 22px; margin-bottom: 8px; }</style>
