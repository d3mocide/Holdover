# Accounts

Accounts are **optional**. Anyone who can reach the server can browse the map, stocking, conditions, planner and
reports without signing in. Signing in adds sync across devices and per-person data. There is no shared secret.

## What is per person, and what is not

| Data | Signed out | Signed in |
| --- | --- | --- |
| Map, stocking, conditions, planner, reports | public | public |
| Journal (trips, catches, pins, photos) | on this device only | synced to your account; only you can read it |
| Home location | on this device | your account |
| Favorites | on this device | your account (also get their own forecast refresh) |
| Gear and setups, and what you used on each trip | on this device only | synced to your account; private to you |
| Waterbody pins, ODFW label matching, report review | n/a | admins only |

Signing in merges what the device had: favorites are unioned in, and a home location is adopted only if the
account has none. A journal logged while signed out is adopted by whoever signs in first on that device.

## Setting it up

There is no self-registration and no default password. The first account is created on the server:

    docker compose exec holdover python -m app.cli create-user will       # prompts for a password; the first user is an admin
    docker compose exec holdover python -m app.cli list-users
    docker compose exec holdover python -m app.cli reset-password will    # if someone is locked out

Creating the first user also adopts anything that existed before accounts: journal rows, and the old global
"starred" waterbodies become that user's favorites.

Everyone else joins by invite: **Settings > Invites > Create invite link** (admins only). The link is
`https://your-host/?invite=CODE`, works once, and expires after `INVITE_DAYS` (7). The code is shown only when it
is created; the database keeps only a hash. Admins can also reset passwords, disable people (which signs them out
everywhere), and promote or demote other admins. The last active admin cannot be removed.

## How sign-in works

- Username and password (3-32 letters, digits, `.`, `-`, `_`; password 10+ characters). Passwords are hashed with
  scrypt and a per-user salt.
- A successful sign-in creates a **server-side session**. The browser holds a random token in an `HttpOnly`,
  `SameSite=Lax` cookie (`Secure` automatically over HTTPS, including behind a proxy that sends
  `X-Forwarded-Proto`; force with `COOKIE_SECURE`). The database stores only a hash of the token. Page scripts
  cannot read it. Sessions last `SESSION_DAYS` (90) and slide forward while you use the app.
- Wrong passwords and unknown usernames look identical and take the same time. Five failures for one username, or
  thirty from one address, lock further attempts for 15 minutes (in memory, so a restart clears it). Behind a
  reverse proxy set `TRUSTED_PROXY_HOPS` so "address" means the real caller ([operations.md](operations.md)).
- Every state-changing call must carry an `X-Holdover: 1` header, which a cross-site page cannot send. That, plus
  `SameSite=Lax`, is the CSRF defence.
- Changing your password signs out your other devices.

## Sharing a device

The journal copy on a device belongs to whoever last signed in there. Switching accounts on the same browser
clears the previous person's copy, and if it holds entries that never synced it asks first. They are never
pushed into the next account. Unfinished trip drafts belong to the same device journal, count as unsynced work in
the warning, and are removed with it. On a shared device use **Sign out and clear this device**.

Offline, the app remembers who was signed in so logging keeps working, and confirms with the server when the
connection returns. Favorites and home changes need a connection and say so if you are offline.

## Not included

Password reset by email (an admin resets it), two-factor sign-in, OAuth, or per-account storage quotas. For a
public server, put it behind HTTPS and ideally behind your reverse proxy's own access control as well.

## Favorites dashboard and new photos

Explore's Favorites cards combine public conditions with recent trips from the existing device journal. They use the same favorites preferences and device-owner clearing as Journal; no shared personal endpoint or new table is introduced. Public details use a network-first read with the existing API cache as an offline fallback. Refresh and reconnect reload the dashboard; freshness labels age while it is open. Anonymous favorites and trips remain on the device until adopted at sign-in.

[Journal recommendations](journal-recommendations.md) also use the existing device journal, including unsynced
entries. Computation stays in the browser; personal results are never returned by or stored in the public API
cache. An in-memory snapshot from a different signed-in owner is hidden during account switching. No new personal
table, account preference or sync payload is introduced; adoption and shared-device clearing stay the same.

New journal/gear photos are decoded and resized on-device (maximum edge 1600 pixels) before entering IndexedDB or sync. JPEG orientation is applied to the exported pixels; transparent PNG/WebP inputs retain alpha. Unreadable/unsupported photos produce a form error without saving a partial entry. Existing stored photos are not rewritten. The existing owner-prefixed upload/read/reference checks still apply.
