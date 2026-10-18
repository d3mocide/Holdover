<script>
  import { requestPersistence, storageInfo, storageSummary } from './storage.js';
  let info = $state(null);
  let msg = $state('');
  const sum = $derived(info ? storageSummary(info) : null);
  const refresh = async () => (info = await storageInfo());
  $effect(() => { refresh(); });
  async function protect() {
    msg = '';
    const ok = await requestPersistence();
    await refresh();
    if (!ok) msg = 'The browser declined. Adding the app to your home screen and using it regularly usually helps.';
  }
</script>

<section class="card">
  <h2 class="eyebrow">Storage on this device</h2>
  {#if sum}
    <p class="line" class:warn={sum.tone === 'warn'} class:ok={sum.tone === 'ok'}><i class="stat-dot" class:ok={sum.tone === 'ok'} class:bad={sum.tone === 'warn'}></i> {sum.text}</p>
    {#if info?.supported && !info.persisted}<button onclick={protect}>Ask the browser to protect it</button>{/if}
    {#if msg}<p role="status" class="small quiet">{msg}</p>{/if}
  {/if}
</section>

<style>
  h2 { margin: 0 0 8px; } .line { margin: 0 0 10px; display: flex; gap: 10px; align-items: flex-start; font-size: 14px; } .line .stat-dot { margin-top: 6px; }
  .small { font-size: 13px; margin: 8px 0 0; }
</style>
