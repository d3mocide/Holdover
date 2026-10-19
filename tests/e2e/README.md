# Browser tests

Playwright scripts drive the real app in headless Chromium. They are not part of `pytest`. Run them when
sync, accounts, gear, offline or UI code changes (see AGENTS.md).

| Script | Covers | Checks |
| --- | --- | --- |
| `offline.mjs` | Airplane-mode journal: service worker, offline tiles, trip logged offline, sync after reconnect, no duplicates | 12 |
| `accounts.mjs` | Sign-in, cookie flags, invites, a second user, isolation, merging local favorites, two people on one browser | 37 |
| `pins.mjs` | An admin places a pin from the map (Settings, Place pins): signed-out users do not see it, the map switches zone and asks for a tap, the tap is saved and the item leaves the list, cancelling changes nothing. Run after `setup.sh accounts` | 10 |
| `gear.mjs` | Starter catalog, items, setups, the trip picker, stats, trip editing, your history on the sheet, the pack list, sync, offline create, cross-account isolation, axe on every gear view | 46 |
| `hardening.mjs` | Offline anonymous JSON/CSV export, shared-device draft clearing and cancellation, account-switch draft isolation, late offline arrival on a second device, exact-date day cache | 14 |
| `day-cache.mjs` | Vite modules: v2 journal upgrade preserved, separate dates and fisheries, no future-day substitution, no guessing legacy fishery, Oregon evening date, cached trip capture | 10 |
| `accessibility.mjs` | Full axe and screenshots of Settings, Reports, Gear, Map, Legend, Rivers, River history, Favorites, search, Plan, Day, Journal, Log trip and Gauges in three themes at phone, tablet and desktop widths; phone title bounds | 126 scans |
| `map-markers.mjs` | All overlapping layers reachable, reports first, gauge timestamp and offline aging, close-target bounds, waterbody action, picker/card axe and screenshots across themes and screen sizes. Browser-only synthetic responses | 102 checks, including 18 axe scans |
| `map-layout.mjs` | Shared title/icon alignment on six pages; Explore underline selectors and header; nearby creek/reservoir choices, distinct schedule weeks and correct selection. Browser-only synthetic schedules | 129 checks, including 9 axe scans |
| `rivers.mjs` | Direct river browsing and marker clicks, populated charts, measurement switching, Favorites, cross-zone search, unpinned waters, offline river reload, phone fit | 12 |

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

For the hardening suite, use a separate fresh fixture instance (never the personal dev database):

    task_e2e_dir=$(mktemp -d /tmp/holdover-hardening-XXXXXX)
    E2E_DIR="$task_e2e_dir" PORT=8031 tests/e2e/setup.sh gear
    BASE_URL=http://localhost:8031/ node tests/e2e/hardening.mjs
    BASE_URL=http://localhost:8031/ node tests/e2e/accessibility.mjs
    kill "$(cat "$task_e2e_dir/server.pid")"

`day-cache.mjs` imports the real frontend modules from Vite (`DEV_URL=http://localhost:5173` by default), in a fresh
isolated browser. Day responses are explicit test fixtures intercepted in the browser; it never changes server data.
Run `node tests/e2e/day-cache.mjs` while the dev stack is up. The new scripts save screenshots under `/tmp` by default
(`SHOTS` overrides the directory). Do not reset a fixture server while another suite is using it.

The river suite needs populated chart observations on its own disposable instance:

    task_river_dir=$(mktemp -d /tmp/holdover-rivers-XXXXXX)
    E2E_DIR="$task_river_dir" PORT=8041 tests/e2e/setup.sh gear
    .venv/bin/python tests/e2e/seed-river-history.py "$task_river_dir/data/e2e.db"
    BASE_URL=http://localhost:8041/ node tests/e2e/rivers.mjs
    BASE_URL=http://localhost:8041/ node tests/e2e/map-markers.mjs
    BASE_URL=http://localhost:8041/ node tests/e2e/map-layout.mjs
    BASE_URL=http://localhost:8041/ node tests/e2e/accessibility.mjs
    kill "$(cat "$task_river_dir/server.pid")"

`seed-river-history.py` adds explicitly synthetic observations only to a disposable `/tmp/holdover-...` database;
it refuses other locations and never overwrites rows. These are chart fixtures, not real readings. The expanded
accessibility suite covers Reports, Gear, Rivers, River history, Favorites, water search, Legend and Gauges too: 126 scans in total, with no
landmark rule disabled.

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
