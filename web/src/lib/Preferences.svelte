<script>
  import { gpsMessage } from './gpsHelp.js';
  import { auth, prefs, setHome, toggleFavorite } from './auth.svelte.js';
  import Icon from './Icon.svelte';
  let { wbList = [], picking = false, onpick } = $props();
  let msg = $state('');
  const names = $derived(Object.fromEntries(wbList.map((w) => [w.id, w.name])));
  const favs = $derived(prefs.favorites.map((id) => ({ id, name: names[id] ?? `Waterbody ${id}` })).sort((a, b) => a.name.localeCompare(b.name)));
  const IN_ZONE = (lat, lon) => lat >= 41.9 && lat <= 46.4 && lon >= -124.9 && lon <= -116.4;
  const where = $derived(auth.user ? 'Saved to your account.' : 'Saved on this device. Sign in to keep it across devices.');

  function useGps() {
    msg = '';
    if (!navigator.geolocation) { msg = 'This browser has no location service.'; return; }
    if (!isSecureContext) { msg = gpsMessage(null, false); return; }
    navigator.geolocation.getCurrentPosition(
      async (p) => {
        const { latitude: lat, longitude: lon } = p.coords;
        if (!IN_ZONE(lat, lon)) { msg = 'That location is outside Oregon, so it was not saved. Tap the map to set a home instead.'; return; }
        try { await setHome({ lat: +lat.toFixed(4), lon: +lon.toFixed(4) }); } catch (e) { msg = e.message; }
      },
      () => (msg = 'Location was blocked or unavailable. Tap the map to set a home instead.'),
      { enableHighAccuracy: false, timeout: 10000 });
  }
  async function clearHome() { msg = ''; try { await setHome(null); } catch (e) { msg = e.message; } }
  async function unfav(id) { try { await toggleFavorite(id); } catch (e) { msg = e.message; } }
</script>

<section class="card">
  <h2 class="eyebrow">Home</h2>
  <p class="line">
    {#if prefs.home}<span class="mono">{prefs.home.lat.toFixed(4)}, {prefs.home.lon.toFixed(4)}</span>
    {:else}<span class="quiet">Not set. Spots are ranked without a distance factor.</span>{/if}
  </p>
  <p class="quiet small">Used to weigh how far each spot is. {where}</p>
  <div class="row">
    <button class:primary={!prefs.home} onclick={onpick} aria-pressed={picking}><Icon name="log" size={18} /> {picking ? 'Tap the map…' : prefs.home ? 'Move on map' : 'Set on map'}</button>
    <button onclick={useGps}>Use my location</button>
    {#if prefs.home}<button onclick={clearHome}>Clear</button>{/if}
  </div>
  {#if msg}<p role="alert" class="small err">{msg}</p>{/if}
</section>

<section class="card">
  <h2 class="eyebrow">Favorites</h2>
  {#if favs.length}
    <ul>
      {#each favs as f (f.id)}
        <li><span>{f.name}</span><button class="rm" onclick={() => unfav(f.id)} aria-label="Remove {f.name} from favorites"><Icon name="close" size={18} /></button></li>
      {/each}
    </ul>
  {:else}<p class="quiet small">None yet. Use the star on a waterbody to add it.</p>{/if}
  <p class="quiet small">{auth.user ? 'Favorites also get their own weather forecast, refreshed on the server.' : 'Saved on this device. Sign in to keep them across devices.'}</p>
</section>

<style>
  h2 { margin: 0 0 8px; } .line { margin: 0 0 4px; } .small { font-size: 13px; margin: 0 0 8px; } .err { color: var(--accent); }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  ul { list-style: none; padding: 0; margin: 0 0 8px; }
  li { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 44px; border-bottom: 1px solid var(--hair); }
  li:last-child { border-bottom: 0; }
  .rm { border: 0; background: none; color: var(--text-quiet); }
</style>
