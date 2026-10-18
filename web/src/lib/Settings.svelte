<script>
  import { clock, setClock } from './clock.svelte.js';
  import { api } from './api.js';
  import { auth } from './auth.svelte.js';
  import Account from './Account.svelte';
  import Admin from './Admin.svelte';
  import Preferences from './Preferences.svelte';
  import Storage from './Storage.svelte';
  import Credits from './Credits.svelte';
  let { theme, onTheme, onChanged, wbList = [], invite = null, picking = false, onpick, oninvitedone } = $props();
  const themes = [['fir', 'Fir & Steelhead'], ['redband', 'Redband'], ['nightbite', 'Night Bite']];
  let health = $state(null);
  $effect(() => { api.health().then((h) => (health = h)).catch(() => (health = null)); });
</script>

<div class="settings">
  <h1>Settings</h1>

  <Account {invite} {oninvitedone} />
  <Preferences {wbList} {picking} {onpick} />
  <Storage />

  <fieldset>
    <legend>Theme</legend>
    {#each themes as [k, label]}
      <label class="opt"><input type="radio" name="theme" value={k} checked={theme === k} onchange={() => onTheme(k)} /> {label}</label>
    {/each}
  </fieldset>

  <fieldset>
    <legend>Time format</legend>
    <label class="opt"><input type="radio" name="clock" value="12" checked={clock.mode === '12'} onchange={() => setClock('12')} /> 12-hour (7:29 AM)</label>
    <label class="opt"><input type="radio" name="clock" value="24" checked={clock.mode === '24'} onchange={() => setClock('24')} /> 24-hour (07:29)</label>
    <p class="quiet small">Saved on this device.</p>
  </fieldset>

  {#if auth.user?.is_admin}<Admin {onChanged} />{/if}

  <Credits />

  <p class="quiet small ver">Holdover {__APP_VERSION__}</p>

  <section class="card">
    <h2 class="eyebrow">Source status</h2>
    {#if health}
      {#each Object.entries(health.sources) as [name, s]}
        <div class="src">
          <i class="stat-dot" class:ok={!s.stale} class:bad={s.stale}></i>
          <span class="nm">{name}</span>
          <span class="when quiet">{s.last_success ? new Date(s.last_success).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'never run'}{s.stale && s.last_success ? ' · stale' : ''}</span>
        </div>
        {#if s.last_error}<p class="quiet small err">Last error: {s.last_error}</p>{/if}
      {/each}
    {:else}<p class="quiet">Server unreachable.</p>{/if}
  </section>
</div>

<style>
  .settings { padding: 16px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; height: 100%; }
  fieldset { border: 1px solid var(--hair); border-radius: 14px; background: var(--glass-fill); padding: 8px 16px 12px; }
  legend { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--text-quiet); padding: 0 6px; }
  .opt { display: flex; align-items: center; gap: 10px; min-height: 44px; color: var(--text); margin: 0; }
  h1 { font-size: 24px; letter-spacing: -0.01em; } h2 { margin: 0 0 8px; }
  .src { display: grid; grid-template-columns: 9px 1fr auto; gap: 12px; align-items: center; min-height: 36px; border-bottom: 1px solid var(--hair); }
  .src:last-of-type { border-bottom: 0; } .nm { font-size: 14px; } .when { font-size: 13px; font-variant-numeric: tabular-nums; }
  .small { font-size: 13px; margin: 0; } .err { padding-left: 21px; }
</style>
