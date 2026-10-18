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

### 2026-10-18 · this commit · Phase 11 · Reservoir levels (Army Corps)
Pool elevations for nine Willamette reservoirs (Detroit, Green Peter, Dexter, Foster, Cottage Grove, Dorena, Fall Creek,
Blue River, Hills Creek) on each waterbody's sheet: elevation, change over 24 h and 7 days, and the same date in the three
previous years from the Corps' own history. New table `reservoir_reading` (migration 0004), adapter `app/sources/corps.py`,
hourly job, a `corps` entry in `/healthz` (stale after 2 h), a credit, and the terms record in `docs/sources.md`.
- Verified: 142 `pytest` (10 new: parse of a real captured response for all nine projects, wrong units and garbage
  rejected, UTC request, raw-first storage, gap-based lookback, failure keeps old data, changes and earlier years, stale,
  every project maps to a seeded waterbody). **Live**: the adapter ran against the real service from the host and from inside
  the rebuilt container (8,707 readings plus three years of history); Hills Creek 1,450.3 ft, 1.6 ft lower over 7 days,
  10 ft lower than a year ago. Browser: the card shows on desktop and phone in all three themes with zero axe violations.
- Found: the certificate problem is exactly the missing intermediate; adding that one public certificate for this host
  makes verification pass, so nothing is disabled. `timezone=GMT` works and `startdate/enddate` select history; the
  `start_date` form from the research is ignored. A phone screenshot with software GL flags showed the list bleeding
  through the sheet; without those flags it renders correctly and a DOM hit test confirmed the sheet is on top, so it was
  a headless rendering artifact, not an app bug.
- Not checked: the Corps' terms (there is no page to read), how the service behaves under its own maintenance, a
  real phone. Lookout Point, Big Cliff, Cougar and Fern Ridge exist at the Corps but have no waterbody here yet.

### 2026-10-18 · this commit · Phase 11 · Fire card (ODF fire danger and NIFC perimeters)
A "Fire" block on each waterbody's sheet: the ODF public fire danger level and area code (when the waterbody is inside a
zone ODF protects), and any active wildfire within 50 km from the NIFC perimeters, with distance, size, containment and
the perimeter's update date. Two adapters (`odf_fire.py`, `nifc.py`), a small `geo.py`, tables `fire_danger` and
`fire_nearby` (migration 0005; per-fetch snapshots like advisories), jobs every 6 h and hourly, `/healthz` entries, credits,
terms in `docs/sources.md`. The wording never states restrictions or closures and says a nearby fire is not a closure.
- Verified: 154 `pytest` (12 new: geometry incl. holes and multipolygons, both real captured responses, error objects and
  garbage rejected, overlapping zones take the more cautious level, the active-fire rules, raw-first storage, failure keeps
  the last good reading, "never fetched" differs from "no fire", the conditions bundle). 5 new frontend tests (30 total). **Live**:
  both jobs ran in the rebuilt container: 63 zones, 28 waterbodies inside one, 4 active fires, 21 waterbody-fire pairs, both
  matching an independent offline calculation. North Fork Reservoir's sheet shows "Austin fire: 25 km away; 12,888
  acres, 98% contained" and "Low (level 1 of 4), ODF area CM-1"; axe: zero violations in all three themes, desktop and phone.
- Found: ODF's `pendingchangedatetime` is not clearly a future change, so it is not shown. A perimeter's "current" date can
  be months old at 97 to 99% contained, hence the 30-day and not-100% filters. A phone screenshot taken after a reload
  (service worker controlling the page, WebGL map) drew the list through the sheet while a DOM hit test and computed
  styles showed the sheet on top and the same page without a reload rendered correctly; treated as a headless compositor
  artifact, **not verified on a real phone**.
- Not checked: ODF's and NIFC's terms beyond their metadata (no ODF text exists), behaviour when ODF changes the layer,
  fires just across the Washington border, and a real phone. FIRMS and the map layer are not built (owner undecided on FIRMS).

### 2026-10-18 · this commit · Phase 11 · Fire map layer, river flood status (NWPS), and a correction
**Fire map layer.** ODF danger zones (tint grows with level; Low is an outline only) and NIFC wildfire perimeters (dashed
outline, named from zoom 8.5) on the map, with a "Fire danger and fires" toggle in Layers and two Legend entries. Geometry is
served by `GET /api/fire/map`, parsed from the newest stored responses (the raw-first rule again), and an empty database
returns empty collections, not an error. **River flood status.** `app/sources/nwps.py` (migration 0006, table `river_status`,
hourly job, `/healthz` entry, credit): NOAA's official category, stage and forecast for 14 of the 16 USGS gauges, shown under
each flow row on the sheet and on the Gauges page, worded as "NOAA flood category: ..." and never as safe.
- Verified: 164 `pytest` (10 new: map endpoint empty and populated; NWPS real response, `-999` handling, synthetic minor and
  moderate flooding with a forecast, stale observation, undefined categories silent, failure keeps the last status, mapping
  integrity) and 33 frontend tests (3 new). **Live**: the NWPS job stored 14 gauges; `/api/fire/map` returned 63 zones and 5
  perimeters; the map shows a High-danger zone near Hood River and its fire perimeter, and the Gauges page shows the NOAA lines.
  Axe: zero violations on the map, sheet, day view, Plan, Journal, Gear, Gauges and Settings (Fir desktop) and on the Redband and
  Night Bite maps.
- Found: matching NWPS gauges to USGS ones needed a human check: two of the nearest NWPS gauges (Dexter, Cottage Grove) are
  reservoir gauges, not the river points, so they are excluded. Every defined gauge reads "no flooding" in this dry autumn, so
  flooding wording is covered only by synthetic tests, not by a real event.
- **Correction (to the Reservoir levels and Fire card entries above).** Those entries blame a "headless compositor artifact"
  for a phone screenshot in which the list showed through the sheet. That was wrong. The app reads the theme from
  `localStorage` as a plain string, and my test script stored it JSON-quoted (`"fir"`), which is not a theme, so no colour tokens
  applied: that is what made the sheet see-through, the map blank on desktop and the chrome flat grey. With a valid value the
  same flows render correctly with no special GPU flags. No app bug was found. Still not verified on a real phone.
- Not checked: NWPS's own usage policy (none found), the layer on a phone-width screen, FIRMS (not built), flood status for
  ungauged waters.

### 2026-10-18 · this commit · Phase 9 · Image publishing workflows and a separate dev stack
`.github/workflows/ci.yml` (pytest, frontend tests and build) and `docker.yml` (multi-arch amd64 and arm64 build; publishes
to `ghcr.io/d3mocide/holdover` from `main` and `v*` tags only). `docker-compose.yml` now names the published image and can still
build locally. A separate dev stack (`docker-compose.dev.yml`, `Dockerfile.dev`, `scripts/dev-fetch.sh`): API with reload,
Vite dev server proxying to it, its own volumes, scheduler off by default. Added a `.dockerignore` (there was none, so
`node_modules` and `data/` went into the build context). Vite's proxy target is now `API_URL`.
- Verified: the workflow and compose files parse as YAML; the dev stack built and ran here: API healthy on :8020, and Vite on
  :5173 answered `/healthz` through its proxy.
- Not verified: **the workflows have never run** (nothing is pushed and there are no credentials here), the arm64 image has
  not been built or run on a Pi, hot reload was not exercised by an edit, and `scripts/dev-fetch.sh` was not run (it would
  poll the agencies).

### 2026-10-18 · this commit · Phase 9 · First-run catch-up, job logging, and layout and wording fixes from the Pi
Found by running the published image on a Raspberry Pi with an empty database: **everything was stale** and the logs showed
only web requests.
- **Poller kick-off.** Scheduled jobs only fire at their next interval or cron time, so a new install had no data for up to a
  day. A catch-up job now runs 5 seconds after start and runs, one at a time and in dependency order (stocking before NWS),
  every source that has no recent success; the timers carry on from there. **Logging:** each job run logs one line
  (`job usgs ok {...}` or `FAILED`), our loggers are at INFO with timestamps, and the access log no longer lists static files,
  tiles or `/healthz`. The "frontend vs backend" log split is not needed: it is one process (the scheduler must stay in the
  single worker), so the lines you saw were just its web access log. `docker compose logs holdover | grep job` now shows the pollers.
- **Layout.** The Map tab's side panel now has the same width as Plan (520 px, so switching tabs does not jump) and the
  waterbody sheet is 420 px (was 340), the Day view 600 px, shrinking on tablets.
- **Stocking weeks.** The sheet and Day view mixed 2026 weeks with schedule weeks of 2027 under labels without a year. They
  are now "Coming up" (soonest first) and "Already stocked" (newest first), each grouped under year headings.
- **Time format setting.** Settings has 12-hour (default) or 24-hour, per device. It applies to "as of" times, the Synced time, the
  daylight tile and the times inside planner sentences (the server still sends 24-hour text; the browser rewrites it).
- Verified: 168 `pytest` (4 new on catch-up order, skipping fresh sources, job log lines, scheduling) and 38 frontend tests (5
  new: grouping, 12-hour edge cases incl. midnight and noon, text rewriting). **Live**: from an empty database all nine sources
  ran in order in about 80 seconds, logged as above (stocking 500 rows, USGS 22,057 readings, NWS 28 forecasts). Browser: the
  setting flips, persists across a reload, and defaults to 12-hour; axe zero violations on the sheet and Day view in all three
  themes at desktop and phone width, and on Settings; panel widths 520 px (Map and Plan equal) at 1440, 451 px at 1024, 396 px at 900.
- Not checked: the tablet layouts by eye beyond the widths, a real phone, and the catch-up after a long outage (the same
  code path; only the empty-database case was run).

### 2026-10-18 · this commit · Phase 9 · Hide-panel toggle, version 0.5.0, release gating, README
- **Hide the panel.** A round tab on the side panel's edge (desktop) or above the bottom panel (phone) hides it to show the
  whole map, and brings it back. Tapping any nav tab re-opens it; the choice is remembered on the device. It reuses the arrow
  icon rotated by CSS (no new artwork). On a phone the collapsed tab sits above the map attribution, which it first covered
  (an ODbL requirement; caught in a screenshot and moved).
- **Version 0.5.0** in `pyproject.toml` and `web/package.json` (a test keeps them equal), reported by `/healthz` and shown in
  Settings. **Release flow:** `ci.yml` is now one workflow; the image is built for every pull request and push but pushed only from
  `main` (`main`, `sha-...`) and from `v*` tags (`X.Y.Z`, `X.Y`, `latest`), and **only after the backend and frontend tests pass**
  (before, the image job ran in parallel and would have published a commit whose tests failed). `docker.yml` was merged into
  it. The compose default tag is `latest`. The README, which still described phases 1 to 5, was rewritten for the published image.
- Verified: 169 `pytest`, 38 frontend tests; the toggle checked at desktop and phone in all three themes (44 px target,
  persists across reload, nav re-opens, zero axe violations); `/healthz` reports 0.5.0 on the rebuilt container; the workflow
  parses as YAML. A scan of tracked files found no secrets, keys, `.env` or databases (largest file 456 KB).
- Not verified: **the workflow has still never run** (including the tag logic and the `latest` expression), arm64, and the
  first publish needs a push. Git author emails in history include a personal address (`info@d3mo.us`); left as is.

### 2026-10-18 · this commit · Phase 9 · First real LLM run (owner's local server) and what it exposed
The owner's prod server logged `LLM unavailable: HTTP 500`. Tested from the laptop against their server
(`192.168.10.90:8080`, an OpenAI-compatible server listing `gemma4-e4b`, `mix-gemma-e4b`, `mix-ornith9b` and `ornith-1.5-9b-uncensored`).
- **Cause of the 500:** the model was set as `openai/gemma4-e4b` (a LiteLLM-style provider prefix); the server only knows
  `gemma4-e4b`. The variable `LLM_API_BASE` is also not one the app reads (`LLM_BASE_URL`), and compose passes only a fixed
  list of variables, so an unknown name is dropped silently. Both base URL forms (`http://host:8080` and `.../v1`) work.
- **Two drifts from a server that does not enforce the JSON schema**, found only by running the real pipeline on the saved
  ODFW report: the model returned a bare list instead of `{"items": [...]}` (all 5 zones rejected), then `species` as a string
  instead of a list. Fixed narrowly (wrap a bare list for one-field schemas; wrap a lone species string) while keeping strict
  validation of everything else and the grounding checks unchanged; each has a test, including that an invalid rating is
  still rejected after wrapping.
- **Result with the fixes:** `gemma4-e4b` extracted and summarised all 5 zones, 0 errors, about 2 minutes for the lot (a
  scheduled job, so latency does not matter). Items land as `review`, per the design. Example: "Coho salmon are moving into
  the lower parts of the North Santiam" tied to the verbatim source sentence. A Willamette main-stem walleye item matched no
  waterbody (the seed has none), which is correct behaviour.
- **Startup log** now says what is wrong with the LLM settings (not configured, not answering, or "the server does not list
  model X; it has A, B, C").
- Also from the prod log, not a bug: the stocking job's `pages: 12, rows_seen: 0` means every page was unchanged since the
  last fetch (hash match), so nothing was parsed; catch-up skipped stocking and reports because that volume already had fresh data.
- Verified: 172 `pytest` (3 new). Not verified: summary and extraction quality beyond one report (reviewed by eye on this one
  only); explanations (`run_explain`) and pack intros with this model were not run; behaviour under load or while the model
  is busy with other work.

### 2026-10-18 · this commit · Phase 9 · LLM in the dev stack; explanations and pack intros run for real
The dev compose file now passes `LLM_BASE_URL`, `LLM_MODEL` and `LLM_API_KEY`. With the owner's server (`gemma4-e4b`):
the report job extracted and summarised all 5 zones (0 errors, about 125 s) and `run_explain` generated planner
explanations and pack intros for trout, steelhead and warmwater.
- Verified: the guard worked on live output: 3 trout explanations were rejected for terms not in the facts ("October",
  "September") and fall back to the template; the rest were accepted (trout 8 of 11, steelhead 3, warmwater 5; pack intros 10, 3
  and 3, none rejected). A sample accepted explanation: "The forecast calls for 63F with no rain and a light 2 mph wind.
  Daylight lasts from 07:33 to 18:21, and the spot is 99 mi straight-line." (the 12/24-hour setting rewrites such times when shown).
- Not verified: wording quality beyond a handful of samples read by eye, how the 3 rejections vary run to run, and the
  review flow in the UI with these items (needs a signed-in admin in the dev stack).
- Dev notes: the Vite dev server serves the map through its `/tiles` proxy (range requests checked); the dev volume has no tiles
  until `scripts/install-basemap.sh` is run against it (`COMPOSE="docker compose -f docker-compose.dev.yml" SERVICE=api`).

### 2026-10-18 · this commit · Phase 9 · Map tab is the map, form drawers, plain-HTTP fix, wider inspector, 9B model trial
Found by using the dev stack from a second PC over plain HTTP.
- **Bug: "crypto.randomUUID is not a function" when saving a trip.** `randomUUID` exists only on secure origins (HTTPS or
  localhost); opening the app by a LAN address broke saving a trip and any gear or setup. New `uuid.js` falls back to
  `getRandomValues` (tested with `randomUUID` removed). The GPS buttons now explain "Location only works on a secure (HTTPS)
  address" instead of showing the browser's raw error. Reproduced and re-tested in a real browser over `http://<lan-ip>:5173`.
- **Map tab is now the map alone**; the ranked spot list lives in Plan (they were identical). Choosing a spot from Plan on a wide
  screen opens the sheet beside the list; on a phone it switches to the map. The hide-panel toggle only applies to other tabs.
- **Log a trip, Add gear and setups open as a drawer** next to the panel they came from (full screen on a phone). While one is
  open, Legend slides clear of it (and above the map credit) and Prepare for offline is now an icon under the zoom control (under
  Layers at tablet widths where zoom is hidden). Drawer, panel and the top controls line up to the pixel at 1440, 1024 and 900 px (the
  drawer was 16 px low: an absolutely positioned grid child needs `grid-area: auto`).
- **Inspector width.** The sheet scales 440 to 700 px with the screen (Day view 560 to 860), and the Plan list narrows to 380 px
  while a sheet is open so the sheet can be wide even at 900 to 1100 px.
- **Browser suites updated** (spot lists now in Plan) and re-run: offline 12/12, accounts 37/37, gear 46/46. The offline banner check
  needed the browser's `offline` event fired after the form mounts: Chromium 152 reports `navigator.onLine` as true after a reload
  under offline emulation (same on the old build and on a page without the app, so not a regression).
- **9B model trial** (`ornith-1.5-9b-uncensored` vs `gemma4-e4b`, identical copies of the same data): the 9B answered with text that
  is not JSON for **every** request (all 5 report zones, all 19 explanations and all 18 pack intros rejected), and was 2.7x to 6x
  slower (344 s vs 127 s for reports). `gemma4-e4b` extracted 13 items from 5 zones with 0 errors and 16 of 19 explanations accepted.
  Not usable as configured; the cause (a reasoning model's preamble, or no JSON mode) was not investigated.
- Verified: 172 `pytest`, 42 frontend tests, axe zero on every view touched (desktop, tablet, phone). Not verified: a real phone, the
  Plan list with a sheet open at exactly 900 px (24 px of map shows), and iOS.

### 2026-10-18 · this commit · Phase 5 · Map answers "where today?", Plan looks ahead; sheet and chrome cleanup
Owner feedback after using the dev stack. The Map tab and the Plan tab had become the same list; they are now different jobs.
- **Map: a "Best bets today" card** (`MapCard.svelte`) where the side panel used to sit: the day's top five for the chosen fishery with
  a short reason, tap to open the waterbody, "Plan ahead" link; collapsible (collapsed by default on a phone). Legend sits to its right.
- **Plan: look ahead** (`PlanView.svelte`). "Next 7 days": one ranking per day (seven requests in parallel), each day a row showing its
  top three, tap to open the full ranked list with "why this score" (`SpotList.svelte`); the weekly-report card moved to `ReportCard.svelte`.
  "Further out": ODFW's published stocking schedule by month (about a year ahead), weeks from this week onward, each expandable to the
  waterbodies and fish counts; new endpoint `GET /api/schedule` (weeks in a range, newest snapshot wins, confirmed waterbodies only, plus a
  forward-looking month summary). It is the trout schedule only, and says weeks, not days. Header is now a light underlined tab bar
  over the fishery chips (the two identical chip rows felt heavy); the Plan list no longer narrows when a sheet opens unless the window is
  under 1280 px.
- **The sheet shows only alerts**: no "no algae advisory" or "no wildfire" sentences; the Fire block appears only with a wildfire within
  50 km or ODF danger of Moderate or higher. **Stocking is its own section** (`StockingList.svelte`): coming up first, a year on a week only
  when it is not the current year, four rows then "Show N more weeks", same in the Day view.
- **Chrome**: Layers and Legend use the clear glass until opened (dense when their lists show); Legend is top-left; Prepare for offline is
  an icon under the zoom control; trip and gear forms open as a drawer beside the panel; native select lists use theme colours.
  **All glows removed** (nav, chips, scores, icons, the logo, the favourite star, primary buttons): outlines and fills only; the map's own
  marker halos stay. BRAND.md updated.
- Verified: 177 `pytest` (4 new on the schedule endpoint), 47 frontend tests (3 new), axe zero on the Map card, Plan (both modes), sheets
  and the drawers at desktop, tablet and phone widths; browser suites offline 12/12, accounts 37/37, gear 46/46 (selectors now target
  `.spot` rows because the day headers repeat spot names; Legend gained an accessible name and a group role after axe flagged its
  icon-only state). Not verified: a real phone; the Further out view with the LLM-era report data; months with no schedule.
- Open, in this order: the AI/LLM review (traces from b50 show the 9B is a reasoning model whose answer arrives in a `reasoning` field, now
  handled; prompts re-run), then a dedicated Reports page (owner approved reposting ODFW's wording), then "what's biting where" from our
  own report data.

### 2026-10-18 · this commit · Phase 2 · Reports tab; AI digest removed; first real look at the LLM
Read the owner's b50 traces (an LLM request log, `GET /api/traces`, bodies base64) to find why the AI "seemed broken".
- **Cause 1 (the 9B model):** `ornith-1.5-9b-uncensored` is a reasoning model; the server returns the JSON answer in `message.reasoning`
  and leaves `content` empty. The client read only `content`, so every reply looked empty. It now falls back to `reasoning_content` or
  `reasoning` (tested; `content` wins when present).
- **Cause 2 (prompts and tolerance):** the extraction prompt never showed the JSON shape (a model answered with a bare list); it now states
  the exact object and an example, and the version is `extract-v2` so reports are re-extracted. An unknown rating word now becomes
  `unknown` instead of rejecting a whole report; a lone species string is accepted as a list; a bare list is wrapped. Everything else
  is still validated strictly and every source sentence is still checked against the real text. `LLM_TIMEOUT` (default 180 s) is configurable.
- **Measured on identical copies of the data** (explanations and pack intros, 19 and 18 items): `gemma4-e4b` accepts 17 of 19
  explanations (the guard rejected "October" and "September" it invented), 33 s for the lot; the 9B accepts 19 of 19 with better prose, but
  takes 300 s, and report extraction exceeded 400 s per report (it thinks at length). So: gemma for extraction, either for explanations.
  Not yet done: a per-job model setting, and re-running the 9B extraction with a longer timeout.
- **The AI digest is gone**, per the owner ("not really needed"). `summarize.py`, the digest prompt and schema and the Plan card's
  summary are removed; the grounding guard moved to `app/llm/grounding.py` because the explanations still use it. The LLM now only
  extracts items (for ratings on the map) and rewords the plan and pack text.
- **New Reports tab** (`ReportsView.svelte`, `GET /api/reports/all`): every zone of the weekly ODFW report in ODFW's own wording (re-derived from the
  stored page, so it works with the LLM off), an issue picker when several weeks are stored, a link to the original and the source credit.
  The owner approved reposting (a private, household app); the page still states no regulations. Plan's old report card is now a
  one-line link to it. Nav is seven tabs (a new `reports` icon; the icon atlas image was not regenerated).
- Verified: 180 `pytest`, 47 frontend tests; Reports page axe zero on all three themes at desktop and phone; browser suites offline 12/12, accounts
  37/37, gear 46/46 (the nav-width check now expects seven tabs). Not verified: the Reports page with several stored issues (only one exists
  here), the icon atlas, a real phone.

