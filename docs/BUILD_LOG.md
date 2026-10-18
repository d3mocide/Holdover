# Holdover build log

A dated record of what was done, how it was checked, and what was found. Oldest first; **append new entries at the
end**. [ROADMAP.md](ROADMAP.md) says what is planned and the status of each phase; this file is the evidence.

**Entry format**

```
### YYYY-MM-DD · `commit` · Phase N · Title
What changed (one or two lines).
- Verified: how it was checked (tests, browser run, live data), with numbers. Say what was NOT checked.
- Found: anything surprising, including bugs the change exposed.
```

**Rules:** one entry per meaningful commit or group of commits; be exact about what was verified; report failures and
skipped checks plainly; never edit an old entry to change history (add a correction entry instead). A commit that
finishes or changes a roadmap item also updates ROADMAP.md.

Test counts below are `pytest` totals at the time. The sandbox phases (1-5) ran with fixtures and a few live reads;
everything from the first laptop run onward ran on the owner's machine.

---

## Log

### 2026-10-17 · `5a27109` · n/a · Initial commit
Empty repository.

### 2026-10-17 · `7cb5d55` · Phase 1 · Foundation and stocking map
FastAPI, SQLite with Alembic, `raw_fetch`, Willamette seed with aliases, stocking scraper and snapshots, map with the
stocking layer, theme tokens, nav shell.
- Verified: parser and API tests against saved ODFW fixtures. Built in a cloud sandbox: **no Docker daemon**, so the
  Dockerfile was not built.
- Found: myodfw.com returned 403 to Python from the sandbox while `curl` worked (later shown to be the sandbox).

### 2026-10-17 · `df6ee47` · Phase 2 · Reports and LLM
Report scraper, schema-validated extraction, digests, review queue, `generation` cache.
- Verified: fixture replay; the `source_sentence` substring guard; the LLM-unreachable path, all with a mock client.
- Not checked: any real model.

### 2026-10-17 · `5181f48` · Phase 3 · Conditions
USGS, NWS, OHA advisories, sun and moon, waterbody sheet, day view, gauges page.
- Verified: fixtures plus live reads of USGS, NWS and the OHA layer. 16 USGS gauge coordinates checked against the
  live service. A real OHA advisory (North Fork Santiam, precaution) showed up in the first live test.
- Found: the OHA page builds its table in the browser, so the app reads the ArcGIS layer behind OHA's own map.

### 2026-10-17 · `02a6906` · Phase 4 · Journal and offline
IndexedDB journal, sync queue with backoff, offline tile cache, service worker, "Prepare for offline", export.
- Verified: `tests/e2e/offline.mjs` in headless Chromium with the network switched off (shell loads, trip logged
  offline, syncs after reconnect, duplicate push creates no duplicates).
- Not checked: iOS, Android, real storage quotas.

### 2026-10-17 · `4cc7be5` · Phase 5 · Planner
Scoring with factor breakdown, grounded explanations with template fallback, pack list, filters.
- Verified: scoring and grounding unit tests (74 total tests passing).

### 2026-10-17 · `f772a49`, `ab8eb2e` · Phases 1-5 · Accessibility pass and handoff
44 px targets, on-colour tokens, focusable scroll regions; `docs/laptop-handoff.md` checklist written; PR #1 merged.

### 2026-10-17 · `b406e07`, `d4a0246` · Phase 9 groundwork · First run on the owner's laptop
First time the Dockerfile was built. It built, then failed to start twice; both fixed.
- Found and fixed: port 8000 was taken by another project (host port is now `HOLDOVER_PORT`); the bind-mounted
  `./data` was created root-owned and the non-root container could not write it (now a named volume,
  `holdover-data`).
- Found and fixed: the stocking scrape reported failure after fetching all 500 rows. The page past the last result
  has no table and no empty marker, which the parser read as a layout change. Page 0 stays strict.
- Verified: **myodfw.com answers Python normally from a home network** (the sandbox 403 was the sandbox); stocking
  fresh in `/healthz`; 75 tests passing. Expanded `.gitignore` (`.env` was not ignored).
- Basemap installed: Protomaps build 2026-10-16, Oregon bounding box, 503 MB, extracted in about 15 s.

### 2026-10-17 · `b889d6a`, `ddccb64`, `b748d02` · Phase 6 · Design system, first passes
Fir & Steelhead refresh: glass panels over a full-bleed map, distinct freshness hues, blue gauges; two glass tiers
(light chrome, dense reading panels); collapsible Layers and Legend; branded checkboxes and radios; muted basemap.
- Found: a detail-sheet header was unreadable through thin glass (layers panel showing through) and the zoomed
  basemap was loud. Both fixed. Contrast computed from tokens: text 15.9:1, quiet text 8.3:1, map marks 4.5:1+.
- Found: reservoir "streaks" the owner flagged are in the data (OSM draws some reservoirs and river stretches as
  rough or open polygons); fixed by drawing lakes as closed shapes and rivers from centerlines (`b748d02`).

### 2026-10-17 · `df3f551`, `468ddca`, `aeaacae`, `8423969` · Phase 6 · Icons, brand mark, markers
Custom 24 px icon set with a duotone accent, steelhead brand mark, SVG map markers, themed scrollbars and map
controls, a Legend built from the real markers.
- Found: the first gauge marker (a wave in a diamond) read as a bird, and the report chips read as a signal-strength
  icon. Replaced with a drop in a diamond and a fish-with-pips chip.

### 2026-10-17 · `4a1a4fa`, `45c0cd4`, `7325d27` · Phase 6 · Other themes, map and mobile fixes, docs
Redband and Night Bite ported onto the shared tokens; full-bleed maskable PWA icon.
- Verified: contrast of every theme's marks against its map ground 4.2:1 or better; text above 15:1.
- Found: on a 393 px phone the offline button and Layers panel were 2 px apart (zoom buttons squeezed the row); the
  phone detail sheet was see-through and slid under the nav. Both fixed (zoom buttons hidden below 900 px).

### 2026-10-17 · `ee25a5b`, `4e82794`, `498fff2` · Phase 6 · Layout, labels, tablets, accessibility
Map stays on screen for every view with a content-sized side panel; Journal, Gauges, Settings, Log trip and Day view
restyled; bundled Noto Sans glyphs for offline map labels; ocean as ground; map made truly full-bleed; tablet fixes.
- Verified: axe-core, 3 themes, desktop and phone: zero violations. Offline e2e 11 of 11. 75 tests.
- Found: the map was inset 16 px and the sheet sat 32 px from the top (absolutely positioned grid children resolve
  against the grid area); fixed with `grid-area: auto`. The Day view's footer bar floated 96 px above the bottom.

### 2026-10-17 · `caa9cf5` · Phase 9 groundwork · Waterbody pin cross-check
`scripts/check_coords.py` compares the seed with named features in the basemap. 35 coordinates corrected or snapped
(26 same-name lakes and reservoirs, 9 rivers snapped to their channel), with an overwrite guard so deliberately set
values are never replaced; admin endpoint to set a pin; review list in `docs/waterbody-pins.md`.
- Verified: 80 tests. 51 of 58 waterbodies pinned (was 43). Fall Creek Reservoir had been about 9 km off.
- Not checked: the remaining 7 unpinned, 4 "likely" and 12 unverified waterbodies (owner's call).

### 2026-10-17 · `27d02c6`, `37216dd` · Phase 7 · Accounts
Optional accounts (invite links, username and password); `HOLDOVER_TOKEN` removed; per-user home, favorites and
journal; admin people and invites; owner-scoped sync.
- Verified: 100 tests (20 on accounts, covering isolation, invites, throttling, CSRF); a 37-check browser run on a
  throwaway instance, including two people on one browser; offline e2e 11 of 11.
- Found: signing in while offline made the app think you were signed out and it never synced after reconnecting
  (fixed: remember the last known user and re-confirm when online). Tests were reading the developer's `.env`
  (fixed: tests ignore it).
- Not checked: HTTPS cookie behaviour behind a real proxy.

### 2026-10-17 · `c08e7ee`, `5bb247b` · Phase 8 · Gear (in progress)
Server side: `gear_item` and `gear_setup`, trip and catch gear references, owner-scoped sync with reference checks,
export. Local side: IndexedDB schema v2 and sync for the new tables.
- Verified: 106 tests (6 on gear, including cross-account reference checks). Frontend builds.
- Remaining: catalog, stats, screens, log-trip picker, browser test (see ROADMAP).

### 2026-10-17 · this commit · Phases 6-9 · Roadmap, build log, agent rules, brand guide
Saved the original handoff verbatim, audited it against the code, and wrote ROADMAP, BUILD_LOG, AGENTS, CLAUDE and
BRAND, plus a test that keeps them from drifting.
- Verified: 113 `pytest` tests (7 are new document checks); 5 frontend unit tests (`npm test`). The document checks
  were shown to fail when a brand colour, the `@AGENTS.md` import or a phase status was deliberately broken.
- Found by the audit: IBM Plex is correctly self-hosted via `@fontsource` (shipped and precached); the handoff's
  persistent-storage request is not implemented; the phone search pill and sheet handle from the original mockup
  were never built; the original handoff's open items 1, 5 and 6 are still open or have changed (see ROADMAP).

### 2026-10-17 · this commit · Phase 8 · Gear complete, browser tests committed
Starter catalog, stats functions, the Gear tab (items, setups, "What works"), forms, the log-trip picker, gear on
journal cards, a fish-hook nav icon; the account and gear browser scripts and a safe `setup.sh` now live in `tests/e2e`.
- Verified: 113 `pytest`; 13 frontend unit tests; `gear.mjs` 22 of 22 and `accounts.mjs` 37 of 37 from the committed
  scripts; offline e2e 11 of 11; axe clean on every gear view (desktop and phone); the phone nav fits six tabs with
  64 px targets. A second account cannot see, reference or attach to another's gear.
- Found: axe caught `aria-pressed` on `role="tab"` in my first gear tabs (now plain toggle buttons); a missing
  space in the stats line; my own "hide the suggestion after picking" tweak briefly hid the starter list (caught by the
  browser test). Running the scripts from the repo exposed that a stale server on the same port made tests pass or fail
  against the wrong instance, so `setup.sh` now refuses a busy port.
- Not checked: gear on a real phone or over HTTPS; photo upload size on a slow connection.

### 2026-10-18 · this commit · Phase 9 · Hardening that does not need a phone
Persistent-storage request and a Storage card in Settings; login throttle aware of reverse proxies; backup tests;
`docs/operations.md`; the Docker image can run on Postgres.
- Verified: **restore drill**: a backup from the live container restored into a brand-new container with an empty
  volume served identical results (51 pins, 58 waterbodies, 16 gauges, source status). **Postgres 16**: all 115
  tests pass (2 SQLite-only skip), and the 37-check accounts and 22-check gear browser tests pass with the app
  running on it (22 tables, migration 0003). New tests: throttle with spoofed and proxied headers, backup integrity
  and 7-file rotation, the Postgres no-op; 15 frontend unit tests.
- Found: the schema needed no changes for Postgres. The backup tests initially assumed SQLite (now marked).
- Not checked: any of it behind a real reverse proxy over HTTPS, the storage request on a real phone (Safari may
  decline silently), moving existing SQLite data to Postgres (no tool).

### 2026-10-18 · this commit · Phase 10 · Edit a trip, history per waterbody
Existing trips can be edited in place (pre-filled form, original conditions kept, removed catches soft-deleted,
no duplicate on the server); the waterbody sheet now shows your history there: trips, fish, catches by species, the
best day with the conditions captured that day, and the most productive lure.
- Verified: 117 `pytest`; 20 frontend unit tests (the history and conditions logic, including ties, deleted rows,
  junk values, and "a skunk has no best day"); `gear.mjs` 43 of 43 (now covers editing, removal, one-trip-on-the-server
  and the history panel, axe on both new views); `accounts.mjs` 37 of 37; offline e2e clean.
- Found: nothing broke; the only test change was a stale server on the e2e port in an earlier run (guarded since).
- Not checked: editing on a phone; "best day" is by fish count only (no weighting by effort or hours).

### 2026-10-18 · this commit · Phase 9 · Source terms review, attribution fix
Fetched the policy pages for ODFW, the State of Oregon, NWS, USGS and Protomaps, and the OHA layer's metadata; wrote
the findings into `docs/sources.md`; added "Data sources and credits" to Settings.
- Verified: **negative control**: the new offline-e2e check ("map attribution credits OpenStreetMap") fails with the
  fix removed and passes with it; offline e2e 12 of 12.
- Found: **the map's attribution control was empty**, so the ODbL requirement for visible OpenStreetMap credit was
  unmet since the basemap was installed (fixed). USGS's credit request had no home in the app (fixed). **ODFW publishes
  no terms of use that I could find**, so there is nothing to confirm or object to: the decision is whether to ask
  them (owner). The state's site terms do not address scraping. The OHA layer has no licence text.
- Not checked: whether the state terms govern myodfw.com; ODF's terms (feed not built); any answer from ODFW or OHA.

### 2026-10-18 · this commit · Phase 10 · Pack list knows your gear
The day view's pack list shows "You have: ..." under template items your gear covers (matching by gear type, fishery
tag and name hints; retired, lost and deleted gear ignored; it never claims anything is missing).
- Verified: 25 frontend unit tests (5 new for the matcher); `pytest` 118, including a test that fails if a gear rule
  names a pack item id the Python pack list can no longer produce; `gear.mjs` 46 checks; accounts and offline e2e clean.
- Found: **axe had never scanned the Day view**, and it skips a heading level (an h3 straight after the h1). Fixed with a
  heading-level prop on the shared conditions block. My first "never claims anything missing" assertion matched hidden
  text in the planner's collapsed "Why this score" note ("missing inputs count as neutral"), a false positive; it now
  checks rendered text.
- Not checked: matching quality for gear named unusually (hints are English words; unmatched gear just shows nothing).

### 2026-10-18 · this commit · Phases 9, 11, 12 · Data source research
Searched for APIs behind every unbuilt data item and probed each endpoint directly; wrote
[data-source-options.md](data-source-options.md) and re-planned Phase 11.
- Verified (live requests): **USGS's new Water Data API** serves all 16 gauges in one request with the same values as
  the legacy endpoint; **Army Corps** reservoir elevations for 10 Willamette projects via an undocumented JSON service;
  **NIFC** current wildfire perimeters (16 for Oregon); ODF regulated-use polygons (72, codes only); ODFW fish districts
  (18, on ArcGIS Online); OWRD's station list (662 active); NOAA tides.
- Found: **USGS is retiring the legacy `waterservices` endpoint the app depends on, in early 2027** (their own notice).
  The handoff's ODFW district URL now returns 503, but the layer is live elsewhere. The district polygons are not the
  stocking zones. OWRD has no documented readings API and its station pages redirect to USGS. The Corps' server sends an
  incomplete certificate chain.
- Corrected before publishing: I first labelled the Corps' `CGR` as Cottage Grove; its own metadata says Cougar Dam
  (Cottage Grove is `COT`). Labels in the doc now come from the service's metadata.
- Not checked: the Corps' and NIFC's terms (to read before building), ODF's code meanings, how long a history the Corps
  service returns, USGS rate limits (their pages did not state them).

### 2026-10-18 · this commit · n/a · License: GPL-3.0, matching Vertex
Added `LICENSE` (the unmodified GPL-3.0 text, byte-identical to Vertex's), declared it in `pyproject.toml`,
`web/package.json`, the README and `AGENTS.md` (new dependencies and bundled assets must be GPL-3.0 compatible), and a
test that keeps them consistent. Reason: owner's request, so code can move freely between the two projects.
- Verified: `pytest` document checks pass; package metadata reports the license.
- Not checked: a formal audit of every dependency's license (the main ones, such as Svelte, MapLibre, FastAPI, SQLAlchemy and
  Dexie, are MIT, BSD or Apache-2.0, which are GPL-3.0 compatible).

### 2026-10-18 · this commit · Phase 9 · USGS moved to the Water Data API
The adapter now reads `api.waterdata.usgs.gov/ogcapi/v1` (GeoJSON, cursor pagination). Routine polls fetch the latest
value of each series (about 34 KB); a gap fill fetches a bounded window if a gauge has gone stale; a first run or a
new gauge backfills a week of discharge only. The legacy endpoint stays behind `USGS_API=legacy` until USGS retires it.
- Verified: 131 `pytest` (17 new on the adapter: real captured pages, pagination, unit and qualifier handling, job
  selection, failure and stale behaviour, the legacy fallback). **Against the live API**: a week-long backfill loaded
  22,066 discharge readings in 11 s over 3 pages; **all 16 gauges' latest discharge matched the legacy endpoint
  exactly**; on the running instance the job continued from its legacy-era history (39 new readings, `/healthz` fresh,
  Dexter 1,240 cfs steady).
- Found: the new bodies are about ten times bulkier than legacy, which would have grown the database by tens of MB a
  day if polled as a window, hence latest-mode and gap fill. `latest-continuous` returns every series' newest value even
  from a sensor that died in 2009 (a stored 2009 water temperature turned up in the live check): latest polls now drop
  values older than 3 days. A gauge that cannot reach two days of history would have re-triggered a week-long download
  on every poll: backfills are now limited to once per 6 hours.
- Not checked: USGS rate limits (their pages did not state them; usage is one small request per 30 minutes); behaviour
  when the legacy endpoint is finally switched off (that path is simply unused).

### 2026-10-18 · this commit · Phase 11 · Findings from Vertex
Read the owner's sibling project Vertex (GPL-3.0, `~/Projects/vertex`) for existing stream and fire code, and recorded
the reusable findings in `docs/data-source-options.md` after verifying each endpoint live.
- Verified: ODF **Fire Danger Level** service (63 zones, levels 1-4; its area codes match the regulated-use layer, so the
  codes are decoded); **NOAA NWPS** (165 gauges in the Willamette area, official flood categories; agrees with USGS at
  Albany); NIFC's year-to-date service with an Oregon and not-contained filter (14 active). NASA FIRMS needs a free key
  (not probed).
- Found: Vertex's own note says the USGS legacy feed was already returning 503s and timeouts for it, which supports the
  migration. Its NIFC poller shows useful patterns: server-side geometry simplification, a recent-date filter, and treating
  ArcGIS's "HTTP 200 with an error object" as a failure. Vertex is the owner's own work, so code can move between the
  projects (same license); the plan is to reuse endpoints and patterns, adapted to Holdover's raw-first, pure-parser design.

