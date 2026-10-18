# Browser tests

Three Playwright scripts drive the real app in headless Chromium. They are not part of `pytest`. Run them when
sync, accounts, gear, offline or UI code changes (see AGENTS.md).

| Script | Covers | Checks |
| --- | --- | --- |
| `offline.mjs` | Airplane-mode journal: service worker, offline tiles, trip logged offline, sync after reconnect, no duplicates | 11 |
| `accounts.mjs` | Sign-in, cookie flags, invites, a second user, isolation, merging local favorites, two people on one browser | 37 |
| `gear.mjs` | Starter catalog, items, setups, the trip picker, stats, trip editing, your history on the sheet, sync, offline create, cross-account isolation, axe on every gear view | 43 |

## One-time setup

    pip install -e '.[dev]' pmtiles mapbox-vector-tile
    (cd web && npm ci && npm run build)
    npm i --no-save playwright-core axe-core        # at the repo root; node_modules is ignored by git
    export CHROMIUM=/path/to/chrome                 # any Chromium or Chrome binary

## accounts.mjs and gear.mjs

They use a **throwaway instance** with its own database in `/tmp/holdover-e2e`, never your real data:

    tests/e2e/setup.sh gear         # admin "boss" and a second user "sam"; use "accounts" for the accounts test
    node tests/e2e/gear.mjs         # BASE_URL defaults to http://localhost:8011/; SHOTS=dir saves screenshots
    kill $(cat /tmp/holdover-e2e/server.pid)

`setup.sh` refuses to start if the port is busy, so a stale server can never answer for the new one (`PORT=...` to
change it). The accounts test registers "sam" itself, so run `setup.sh accounts` (not `gear`) before it. Each run
needs a fresh `setup.sh`: the tests create data.

## offline.mjs

    python scripts/make_test_pmtiles.py data/tiles/oregon.pmtiles        # toy tiles, not real map data
    export DATABASE_URL=sqlite:///./data/e2e.db RUN_SCHEDULER=false DATA_DIR=./data WEB_DIR=web/dist
    python -m app.cli migrate && python -m app.cli seed
    python -m app.cli ingest-fixtures tests/fixtures/odfw_stocking
    echo e2e-long-password | python -m app.cli create-user e2e --password-stdin   # the test signs in as this user
    uvicorn app.main:app --port 8012 &
    E2E_DB=./data/e2e.db BASE_URL=http://localhost:8012/ node tests/e2e/offline.mjs

It checks: service worker control, "Prepare for offline" saving tiles to IndexedDB, the shell and cached list loading
with the network off, a trip logged offline with cached conditions, syncing after reconnect, and a forced duplicate
push creating no duplicate rows. Restart the server after deleting the DB file.

Verified in headless Chromium only. iOS and Android (storage quotas, service-worker eviction, GPS, Add to Home
Screen) are untested; see ROADMAP Phase 9.
