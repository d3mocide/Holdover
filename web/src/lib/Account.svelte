<script>
  import { api } from './api.js';
  import { auth, register, signIn, signOut } from './auth.svelte.js';
  import Icon from './Icon.svelte';
  let { invite = null, oninvitedone } = $props();

  let mode = $state(invite ? 'register' : 'signin');
  let username = $state('');
  let password = $state('');
  let again = $state('');
  let busy = $state(false);
  let msg = $state('');
  let inviteOk = $state(null); // null: checking, true/false once known
  let pw = $state({ open: false, current: '', next: '', msg: '' });

  $effect(() => {
    if (invite) api.inviteValid(invite).then((r) => (inviteOk = r.valid)).catch(() => (inviteOk = false));
  });

  async function submit(e) {
    e.preventDefault();
    msg = ''; busy = true;
    try {
      if (mode === 'register') {
        if (password !== again) { msg = 'The two passwords differ.'; return; }
        await register(invite, username, password);
        oninvitedone?.();
      } else {
        await signIn(username, password);
      }
      password = again = '';
    } catch (err) { msg = err.message; } finally { busy = false; }
  }
  async function changePw(e) {
    e.preventDefault();
    pw.msg = '';
    try { await api.changePassword(pw.current, pw.next); pw = { open: false, current: '', next: '', msg: '' }; msg = 'Password changed. Other devices were signed out.'; }
    catch (err) { pw.msg = err.message; }
  }
</script>

<section class="card acct">
  <h2 class="eyebrow">Account</h2>
  {#if auth.user}
    <p class="who"><span class="avatar" aria-hidden="true">{auth.user.username[0].toUpperCase()}</span>
      <span><strong>{auth.user.username}</strong>{#if auth.user.is_admin} <span class="chip-sm">admin</span>{/if}
        <span class="quiet small block">Your journal, home and favorites sync to this account.</span></span></p>
    <div class="row">
      <button onclick={() => signOut()}>Sign out</button>
      <button onclick={() => (pw.open = !pw.open)} aria-expanded={pw.open}>Change password</button>
    </div>
    {#if pw.open}
      <form class="f" onsubmit={changePw}>
        <label for="pw-cur">Current password</label><input id="pw-cur" type="password" autocomplete="current-password" bind:value={pw.current} />
        <label for="pw-new">New password (10+ characters)</label><input id="pw-new" type="password" autocomplete="new-password" bind:value={pw.next} />
        {#if pw.msg}<p role="alert" class="err small">{pw.msg}</p>{/if}
        <button class="primary" type="submit">Save new password</button>
      </form>
    {/if}
    <details class="shared"><summary class="small quiet">On a shared device?</summary>
      <p class="small quiet">Signing out leaves this account's journal on the device. To remove it as well (it stays safe on the server):</p>
      <button onclick={() => signOut({ clearDevice: true })}>Sign out and clear this device</button>
    </details>
  {:else}
    {#if invite && inviteOk === false}
      <p role="alert" class="err">This invite link is invalid, already used, or expired. Ask for a new one.</p>
    {/if}
    <p class="quiet small intro">
      {#if mode === 'register'}You were invited to Holdover. Pick a username and password to create your account.
      {:else}Signing in is optional. Without an account you can browse everything and keep a journal on this device.
        An account adds sync across your devices and your own home, favorites and journal. Accounts are by invitation.{/if}
    </p>
    {#if mode === 'signin' || inviteOk !== false}
      <form class="f" onsubmit={submit}>
        <label for="u">Username</label>
        <input id="u" type="text" autocomplete="username" autocapitalize="none" spellcheck="false" bind:value={username} required />
        <label for="p">Password{mode === 'register' ? ' (10+ characters)' : ''}</label>
        <input id="p" type="password" autocomplete={mode === 'register' ? 'new-password' : 'current-password'} bind:value={password} required />
        {#if mode === 'register'}
          <label for="p2">Repeat password</label>
          <input id="p2" type="password" autocomplete="new-password" bind:value={again} required />
        {/if}
        {#if msg}<p role="alert" class="err small">{msg}</p>{/if}
        <button class="primary" type="submit" disabled={busy}>{mode === 'register' ? 'Create account' : 'Sign in'}</button>
      </form>
    {/if}
    {#if invite && inviteOk !== false}
      <button class="linkish" onclick={() => (mode = mode === 'register' ? 'signin' : 'register')}>{mode === 'register' ? 'I already have an account' : 'Use my invite'}</button>
    {/if}
  {/if}
  {#if auth.notice}<p role="status" class="small notice-s">{auth.notice}</p>{/if}
  {#if auth.user && msg}<p role="status" class="small">{msg}</p>{/if}
</section>

<style>
  .acct { display: flex; flex-direction: column; gap: 10px; }
  h2 { margin: 0; }
  .who { display: flex; gap: 12px; align-items: center; margin: 0; }
  .avatar { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-weight: 600; font-size: 17px; color: var(--on-accent); background: linear-gradient(135deg, var(--fresh-1), var(--fresh-2)); flex: none; }
  .chip-sm { font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--fresh-1); border: 1px solid color-mix(in srgb, var(--fresh-1) 45%, transparent); border-radius: 999px; padding: 1px 8px; vertical-align: middle; }
  .block { display: block; } .small { font-size: 13px; margin: 0; } .intro { margin: 0; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  .f { display: flex; flex-direction: column; gap: 6px; }
  .f label { font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; margin: 6px 0 0; }
  .f button { margin-top: 10px; }
  .err { color: var(--accent); margin: 4px 0 0; }
  .notice-s { margin: 0; border: 1px solid var(--accent); border-radius: 12px; padding: 8px 12px; background: color-mix(in srgb, var(--accent) 8%, transparent); }
  .linkish { background: none; border: 0; color: var(--fresh-1); text-decoration: underline; min-height: 44px; padding: 0; justify-content: flex-start; }
  .shared p { margin: 6px 0 8px; } .shared summary { cursor: pointer; min-height: 32px; display: flex; align-items: center; }
</style>
