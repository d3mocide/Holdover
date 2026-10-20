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

### 2026-10-18 · this commit · Phase 2 · A weekly briefing written from everything we gather; the 9B on extraction
Owner idea: use the slow model for something genuinely useful, once a week. The Reports tab (ODFW's words, no AI) gained a first tab,
**This week**: a briefing whose facts are built by code and whose paragraphs a model writes from them.
- **Facts (`app/briefing.py`), no AI**: Watch-outs (OHA algae advisories, nearby wildfires; shown first, only when present), Where to fish
  (top spots per fishery that have a real signal: stocking or an accepted report item, never distance), Stocking (this week and the next
  two, "scheduled" marked), Rivers and reservoirs (each gauge against its own median, NOAA flood category when elevated, Army Corps pool and
  7-day change), and ODFW's own wording for the Willamette zone. Empty sections are dropped.
- **Paragraphs (`app/llm/briefing.py`)**: the extraction-class model (`LLM_EXTRACT_MODEL`, a long timeout) writes 3 to 5 sentences for Where, Stocking and
  Water from only that section's facts, with a one-line editorial hint ("recommend the two or three best", "say what stands out"). Each
  paragraph is checked against its facts (numbers, names, species), retried once with the offending terms named, then dropped; kept
  paragraphs are stored with the exact facts, the model and the time. A new prompt version invalidates old paragraphs. Without a model
  the page shows the facts. Job: Thursday 16:30, a manual admin job `briefing`, and a startup catch-up if the week has none.
- **9B on extraction**, real run on all five zones: 0 errors, about 7 minutes (the earlier ">400 s" was the model loading). It split "Fall Chinook fishing
  is fair to good in the Siletz, Alsea, Siuslaw..." into one item per river with species, left a retention sentence unrated, and found
  Phillips Reservoir's tiger muskie. `LLM_EXTRACT_MODEL=ornith-1.5-9b-uncensored` is now set in the owner's `.env`.
- **Iterations driven by reading the output against the facts**: past tense for scheduled stocking (now "Scheduled for the week of...");
  an unstated "above it" relationship between two gauges (the prompt now forbids describing how places relate); a steelhead list padded
  with waters that only fit the fishery (now requires a signal); a UTC date next to a local time (new `localDay`).
- Verified: 196 `pytest` (new: facts, ordering, grounded/retried/dropped paragraphs, replacement, hint, API with and without a paragraph),
  47 frontend tests; axe zero in all three themes at desktop and phone; browser suites accounts 37/37 and gear 46/46. **Live**: Ornith wrote
  three paragraphs in about 80 to 136 s, none rejected.
- Not verified: quality over several weeks; paragraphs when little data exists (a new install); whether `Where to fish` should
  remain a separate paragraph from Stocking (they overlap); the offline e2e (not re-run after the final edit, which only touched
  dates and the briefing).

### 2026-10-18 · this commit · Phase 2 · AI ratings on the map; Gauges redesign; layout fixes
- **AI-read ratings on the map and the sheet.** The fish badge with 1 to 4 pips (slow, fair, good, excellent) now also shows the model's own
  reading of ODFW's report, drawn fainter and labelled "AI-read, unreviewed" in the Legend and "AI-read, not yet reviewed" in the sheet and
  Day view, instead of only items a person accepted. **Scores still use only accepted items** (tested: an unreviewed item never moves a
  ranking), rejected items never show, and "unknown" draws nothing. **A safeguard found by checking live data:** the dev map briefly
  showed "Fall Creek Reservoir: excellent trout", a false match of the Central zone's "Fall River". An unreviewed reading now shows only
  when the report's zone is the waterbody's zone (accepted items, which a person decided, are unaffected). Tested.
- **9B extraction again** with the fixed prompt: 4 of 5 zones extracted; one zone's reply was malformed JSON (a real failure; it stays pending and retries).
  No Willamette-zone waterbody matched this time, so the map layer has no AI badge on the dev data yet (verified on a throwaway database
  with clearly fake items).
- **Gauges page.** Each card now leads with the flow (the unit no longer runs into the number), shows how it compares with the gauge's own
  median ("-21% vs median", highlighted at 20% or more; hidden when there is under two days of history), then height and
  temperature, one short NOAA line, and the as-of time with a Stale tag only when stale. The repeated "USGS site, provisional" line is
  gone (the header says it once; the site number is a tooltip). Sort chips: Name (the default, which groups the rivers), Most unusual,
  Highest flow. The "everything is stale" report was the dev stack: its scheduler was off, so data aged past 3 hours; the dev
  scheduler is now on by default (`DEV_RUN_SCHEDULER=false` to stop it).
- **Layout.** With a waterbody open, the Legend drops to the bottom-left (it collided with Layers at 1440 on Plan), and on tight windows
  the Best bets card hides while a waterbody is open. Briefing caption shortened to one line.
- Verified: 200 `pytest`, 52 frontend tests; axe zero on Gauges in all three themes at desktop and phone; Legend and Layers never overlap
  at 1920, 1440 and 1100 on Plan or Map with a sheet open (measured); browser suites offline 12/12, accounts 37/37, gear 46/46. Not verified: a
  real phone; the new AI badge on the real map with tiles (only the data and sheet were checked).

### 2026-10-18 · this commit · Phase 11 · Central zone (pilot): the first zone beyond Willamette
Owner approved Central as the pilot, ODFW polling for more zones, and OpenStreetMap-matched pins shown as unverified.
- **Waterbodies.** Central's stocking schedule lists 36 labels (122 rows, 4 pages); `app/zones/central.py` turns them into 35 waterbodies
  (LAVA LAKE B and L are one water). Pins were proposed by `scripts/propose_zone.py` (same-named OpenStreetMap features inside the basemap,
  narrowed to each label's ODFW district) and chosen by hand: 16 "osm" (unique, same name), 6 "likely" (a choice between candidates, or a
  park label standing in for a pond), and **13 left without a pin** (East Lake, Fall River, Metolius Pond, ...) rather than guessed. Every pin has a
  provenance note and `docs/waterbody-pins.md` lists them. The seed only inserts a pin, so a pin a person moves or clears is never re-applied.
- **Gauges.** Eight, chosen by asking the live USGS API which discharge gauges in the zone reported today (Deschutes at Culver, Madras and Moody;
  Crooked below Opal Springs; Metolius near Grandview; Hood River; White River; Warm Springs River); sensors whose last reading was in 1991
  (upper Deschutes) and the John Day (Northeast zone) were left out. No gauge is linked to a stocked water (none is clearly the same water), so
  they appear on the Gauges page, the map and the briefing but do not move a ranking. Gauges gained a `zone` (migration 0007).
- **Plumbing.** A zone registry (`app/zones`) and `ENABLED_ZONES` (default willamette,central); the stocking job fetches each enabled zone and a
  failing zone does not stop the others; ranking, the "typical stocking" baseline, the map layers, gauges, schedule, explanations, pack intros and
  the weekly briefing are all per zone; `/api/zones`; a **zone picker** (Map card, Plan, Gauges; the choice is remembered) and the map refits to the
  zone. The Corps reservoirs and NOAA flood status stay Willamette-only; the offline map region is still fixed.
- **A real matching bug found while checking Central.** Report items were matched to waterbodies across all zones, so a Central "Fall River" was
  ambiguous with Willamette's Fall Creek and a Northwest "Salmon River" had been matched to a Willamette creek. Matching is now inside the report's own zone;
  `rematch_items` (run with the extraction job) repairs unreviewed items and picks up items read before their water existed, and never touches accepted items;
  re-extracting a report replaces the model's unreviewed items instead of duplicating them.
- Verified: 211 `pytest` (new: seed integrity incl. no duplicate names or labels across zones and "13 unpinned, 22 provenance-recorded"; every one of the 122 real
  Central rows resolves to a waterbody with none left for review; the job with one zone failing; ranking isolation; endpoint filters; zone-scoped
  matching, rematching, and re-extraction), 52 frontend tests, axe zero on the Map card, Plan (both modes), Gauges and Reports for Central at desktop and
  phone, browser suites offline 12/12, accounts 37/37, gear 46/46. **Live in the dev stack**: Central fetched in 4 requests (122 rows), 59,474 readings
  backfilled with every gauge showing its flow against its own median, 42 forecasts, fire danger for 47 waters; Ornith wrote Central's three paragraphs
  (Willamette plus Central took about 6 minutes).
- Found: Central's October "Best bets" is thin (two waters have anything stocked right now; most of the zone stocks in spring and summer 2027): that is the data, not a bug.
- Not verified: the 22 pins on the ground (OSM matches, not a survey), whether "Metolius Pond" and the other unpinned waters can be found in OpenStreetMap by another
  name, a real phone, the second zone on the Pi.

### 2026-10-18 · this commit · Phase 11 · Zone pill on the map, one left edge, page icons
Owner feedback: the zone picker crowded the fish chips, belongs on the map, and the Legend sat far from the rail when the panel was minimized.
- **Zone pill on the map (desktop)**, top-left, with the Legend after it; the pickers inside the cards are gone on desktop. On a phone (map often
  covered, top row full) the picker stays in the Best bets card and the Plan and Gauges headers, now spaced from the chips. With a waterbody open the pill and
  Legend drop to the bottom-left (Legend icon-only); on windows under 1280 px the pill hides while a sheet is open.
- **One left edge.** Everything beside the panel (Best bets card, pill, Legend, drawers, the home-picker bar) is 16 px after the rail or after the panel, through one
  CSS variable. The card and Legend used to start 32 px from the rail, and the Legend kept the panel's gap when the panel was minimized.
- **Page icons** on Plan, Journal and Settings (a shared `PageIcon`), matching Gauges, Reports and Gear.
- Verified: rail-to-card/panel gaps measured at 16 px at 1920, 1440 and 1100 in every state (Map, Plan, panel hidden, sheet open); no overlaps between pill, Legend, Layers
  and the sheet; axe zero; 211 `pytest`, 52 frontend tests; browser suites offline 12/12, accounts 37/37, gear 46/46. Not verified: a real phone.


### 2026-10-18 · this commit · Phase 5 · Zone pill and Legend stay at the top when there is room
With a waterbody open they dropped to the bottom-left on every screen width, which looked odd on a wide screen. They now drop only when the top row would
actually collide: on the Map tab below 1600 px, on Plan below 1820 px; the Legend hides while a sheet is open below 1420 px on Plan and below 1100 px anywhere, and the zone pill hides
below 1400 px. Measured for overlaps with every other control and the sheet at 1920, 1790, 1600, 1500, 1440, 1420, 1400, 1280, 1100, 1000 and 900 px on both tabs: none.
Also in this commit series: the stocking schedule and weekly report are fetched once a week (Friday), see the previous entry's commit message and `docs/sources.md`.
Not verified: the browser suites were not re-run after this CSS-only change.

### 2026-10-18 · this commit · Phase 11 · Northwest zone; per-zone stocking aliases (and a Central bug they exposed); one weekly report per zone
- **Northwest** (ODFW zone 3): 33 waterbodies from its schedule (117 rows, 4 pages), 22 pins by the same method (13 osm, 9 likely) and 11 left unpinned, 7 live
  coastal USGS gauges (Nehalem, Wilson, Trask, Nestucca, Siletz, Alsea, Siuslaw). Its first stocking is February 2027, so it ranks nothing today; its report text is the
  coastal salmon and steelhead report. Enabled by default (`ENABLED_ZONES`); about 19 ODFW requests a week for three zones.
- **Labels repeat across zones** (LOST LAKE is in Central and the Northwest), so stocking aliases are now per zone (`odfw_stocking:<zone>`; Willamette keeps the original name),
  with migration 0008, and the fuzzy proposal only looks inside the zone. **This exposed a Central bug:** Central's CLEAR LAKE had collided with Willamette's alias,
  so its 4 snapshots hung on "Clear Lake (McKenzie)". The earlier "nothing left for review" test could not see it. A guarded repair (`repair_snapshot_aliases`) now
  re-points a snapshot whose alias is in another zone, using ODFW's own zone column on the row; verified on the dev data (Central 4 rows to Clear Lake (Wasco), Willamette 12 unchanged).
  The seed also now confirms a proposal the ingest left when the schedule arrived before its water was seeded (it never touches an alias a person confirmed).
- **Reports tab** is now one view: the selected zone's briefing ending with ODFW's own words; the per-zone tabs were redundant with the zone pill.
- Verified: 219 `pytest`, axe zero on Northwest's map, Plan (both modes), Gauges and Reports at desktop and phone, browser suites below. Not verified: the Northwest pins on the ground,
  the report page with more than one stored issue (the issue picker went with the tabs; old issues are still stored and `/api/reports/all` serves them).

### 2026-10-18 · this commit · Phase 11 · Southwest, Northeast and Southeast: all six ODFW zones
Same recipe as Central and the Northwest. Each zone is a module in `app/zones` generated from a reviewed spec; only unambiguous same-name OpenStreetMap
matches were pinned, and names with several far-apart candidates or no real match were left empty (for example "LOST CREEK RESERVOIR" proposed an unrelated Lost Lake).
| Zone | Schedule | Waterbodies | Pinned (likely) | Unpinned | Gauges |
| --- | --- | --- | --- | --- | --- |
| Southwest | 5 pages, 164 rows | 43 | 22 (7) | 21 | 9 (Rogue, Applegate, Illinois, Chetco, Umpqua) |
| Northeast | 3 pages, 98 rows | 49 | 9 (3) | 40 | 6 (Grande Ronde, Minam, John Day, Umatilla) |
| Southeast | 3 pages, 74 rows | 36 | 13 (3) | 23 | 8 (Klamath, Link, Williamson, Sprague, Wood, Owyhee, Malheur, Snake) |
The Northeast has the most unpinned waters because most of its schedule is small ponds, forest ponds and park ponds that OpenStreetMap does not name. Gauges are Oregon rivers that reported
discharge on the live USGS API on 2026-10-19. ODFW reuses names (FISH LAKE is in four zones, LOST LAKE in three, TWIN LAKE twice): the per-zone aliases keep them apart and the waterbody names carry a zone
qualifier where they would clash. The default is now all six zones, about 30 ODFW requests a week.
- Verified: 222 `pytest` (every real row of each new schedule lands only on its own zone's waterbodies with nothing left for review; pins inside their zone boxes with a provenance note; unpinned counts;
  gauges per zone), 52 frontend tests, axe zero on each new zone's map, Plan (both modes), Gauges and Reports at desktop and phone, browser suites offline 12/12, accounts 37/37, gear 46/46. **Live**: the three
  new zones were fetched automatically at startup (336 rows), 54 gauges are backfilled with a week of flow, 88 forecasts, and Ornith wrote the briefings (Southwest 3 paragraphs, Southeast 2, Northeast 1).
- Found: a manual `run_job(period='P7D')` asks for all three parameters and can overflow the 12-page cap for 54 gauges, leaving some without flow; the scheduled backfill asks for discharge only and fills every gauge.
  It was my test call, not a product bug, but it shows the cap is close: 90+ gauges would need discharge-only backfills to stay that way.
- Found: the weekly Recreation Report has no Southwest section (it covers Northwest, Willamette, Central, Northeast and Southeast), so the Southwest page has no ODFW text.
- Not verified: any pin on the ground (the 13 "likely" ones and every OSM match are suggestions), the zone picker with six entries on a real phone, the Pi.

### 2026-10-18 · this commit · Phase 11 · Place pins from the map
Most zones have unpinned waters (143 waterbodies in all need a pin or a check). Settings, for an admin, has a **Place pins** card: every waterbody with no pin and every pin that was a
guess ("likely": a same-named point of interest or a choice between candidates), each with how it was found; *Place on map* switches the map to that zone and asks for a tap, and the tap is saved
through the existing coordinate endpoint. A pin an admin has placed is no longer a guess and leaves the list; a re-seed never undoes it. New `GET /api/admin/pins`. Found and fixed on the way: fitting the map
to a zone with nothing pinned yet threw a page error (an empty bounding box).
- Verified: `pytest` (the pin list names unpinned and likely waters, drops one once moved, and a re-seed keeps a placed pin), a new browser test `tests/e2e/pins.mjs` (11 checks: hidden when signed out, listed, zone switch,
  tap saved, prompt gone, removed from the list, cancel does nothing), axe zero on Settings with the card in all three themes at desktop and phone.
- Not verified: placing a pin on a real basemap by tapping a real water body (the throwaway instance has no tiles), and on a phone.

### 2026-10-18 · this commit · Release 0.6.0
Version bumped to 0.6.0 (`pyproject.toml`, `web/package.json`, README), `CHANGELOG.md` added with upgrade notes. **Upgrade rehearsal**: a database built by the 0.5.0 code (migration 0006, 58 waterbodies, 100 stocking rows)
was migrated and seeded by this version: it ended at migration 0008 with all 100 rows kept, six zones seeded (254 waterbodies, 54 gauges), every alias confirmed, and no snapshot attached to a
waterbody in another zone. Final checks before the tag: 223 `pytest`, 52 frontend tests, browser suites offline 12/12, accounts 37/37, gear 46/46, pins 11/11.
Not verified: the GitHub Actions workflow (never run: it builds the multi-arch image and publishes on the tag), the Pi, and the real-phone checks still open in the roadmap.

### 2026-10-18 · this commit · Phase 11 · Rivers pilot: the Tualatin (gauges, water quality, flood status, fish passage)
Owner asked what we know about rivers like the Tualatin and what other sources could add. Researched live (see `docs/data-source-options.md` section 10), then built the Tualatin end to end.
- **The river**: "Tualatin River" is a waterbody (pinned at NOAA's Tualatin gauge; steelhead and warmwater fishery hints, labelled unverified like the others), linked to three live USGS gauges (Dilley, Highway 219, West Linn),
  NOAA flood status for two of them, and shown with flow against its own median. It ranks in the steelhead and warmwater lists and opens from its gauge on the map ("Open this river"). A river that has never been on ODFW's schedule shows no Stocking section.
- **Water quality**: USGS dissolved oxygen, pH, turbidity and conductance are now parameters (units checked, anything else skipped); the Dilley gauge reports all four plus temperature, shown on the flow row for readings under 36 hours old.
  No thresholds are stated: values only, with the source.
- **Fish passage (new source, DART)**: ODFW's adult counts at the Willamette Falls fishway, which fish bound for the Tualatin pass first, from Columbia River DART as CSV (`app/sources/dart.py`, table `fish_count`, migration 0009,
  one request a day). Coho 631 against a ten-year average of 1,763 for the same seven days (Oct 9 to 15; counts lag about four days), Chinook 17, steelhead 20. A revised count is a new row and the newest wins. The card says what the numbers are
  and are not: counts for the whole upper Willamette, not for the Tualatin, and nothing about when to fish. A "Fish passage" section also joins the Willamette zone's weekly briefing.
- **Found and fixed on the way**: DART pads every year to 366 rows (a "02-29" in a non-leap year) which made the whole download fail to parse; a blank cell is ambiguous (zero or not reported), so a day with nothing is dropped, not zeroed.
  DART's TLS root is not in certifi: instead of bundling a root, the DART fetch uses the **operating system's trust store** (verified in the production image; the OS store has the root). The Army Corps host still needs its bundled **intermediate**
  (DigiCert, a CA with path length 0, not a root); verified in a freshly built production image run as the server runs it (OS store and certifi both fail, the bundled intermediate gives 200), and the file now ships in the installed package too.
- Researched, not built: StreamNet (API exists, no docs or terms found), OWRD streamflow (catalog only; USGS carries the main gauges), DEQ and Clean Water Services (not examined), ODFW's own counts (monthly PDFs; DART is the machine-readable route).
- Verified: 235 `pytest` (new: real-data USGS water quality and unit rejection, DART parse of the real CSV, blanks, leap-day padding, revisions, failure, summary, system trust), 56 frontend tests, axe zero on the Tualatin sheet in all three themes at desktop and phone,
  browser suites offline 12/12, accounts 37/37, gear 46/46, pins 11/11 on a fresh instance. Live in the dev stack: the DART job added 3,444 rows, Dilley's quality readings arrived on the next poll.
- Not verified: the Tualatin's pin or fishery hints on the ground; how the fish counts relate to what anglers find on the river; DART's terms beyond the citation request; the Pi.

### 2026-10-19 · this commit · Phase 11 · Rivers mirrored: 36 popular rivers across all six zones
Owner asked to mirror the Tualatin to the rivers most people fish. **The list is my judgement** (a river many anglers fish), not data; every one was verified against live sources first:
- **Rivers**: Willamette zone: Willamette (mainstem), Clackamas, Sandy, South Santiam, Middle Fork Willamette, Molalla, Calapooia (with the existing Tualatin, McKenzie and North Santiam); Central: Deschutes, Crooked, Metolius, Hood;
  Northwest: Nehalem, Wilson, Trask, Nestucca, Siletz, Alsea, Siuslaw; Southwest: Rogue, Umpqua, North and South Umpqua, Applegate, Illinois, Chetco; Northeast: Grande Ronde, John Day, North Fork John Day, Umatilla, Minam;
  Southeast: Williamson, Sprague, Klamath, Owyhee, Malheur. Each is declared once in its zone module (`app/zones/rivers.py`): its gauges, and a fishery hint. Pins are at the first gauge, labelled "gauge".
- **Checked live before adding**: all 37 USGS gauges reported flow within hours (one candidate, Silver Creek, was stale and was dropped); NOAA flood gauges matched 33 of them within 400 m and by name (the Deschutes at Culver, Crooked, Metolius, Rogue at Agness and
  the Minam have none); NOAA is now one statewide request (about 380 KB, every 2 hours). The Wilson and Trask list water-quality sensors but their last reading is from 2014, so nothing is shown (readings older than 3 days are dropped).
- **Fish counts only where the geography justifies them**: the Willamette Falls fishway counts apply to rivers above the falls (Willamette, South Santiam, Middle Fork, Molalla, Calapooia, McKenzie, North Santiam, Tualatin, Coast Fork). **Not** to the Clackamas
  (it enters below the falls) or the Sandy (the Columbia). Those need the Columbia dams' counts, which I have not verified, so they show none rather than a wrong one.
- A real improvement: the weekly report's "Willamette River" walleye item now matches the Willamette River waterbody (before it matched nothing). **Performance**: ranking read whole ORM rows for a week of gauge history; it now reads two columns, 0.43 s to 0.15 s per ranking
  (the Plan page makes seven at once, which had grown to about 4 s).
- Verified: 235 `pytest`, 56 frontend tests, browser pass on 7 rivers in all six zones at desktop and phone (flow, NOAA where it exists, fish passage only above the falls, no stocking section, axe zero, no page errors), browser suites offline 12/12, accounts 37/37,
  gear 46/46, pins 11/11; live dev stack: 48 NOAA gauges, 4,161 backfilled readings.
- Not verified: pins on the ground (all rivers are at a gauge, not where anglers fish), the fishery hints (general knowledge), whether every popular river is on the list (the Columbia, the lower Willamette below the falls and estuaries are not covered), the Pi.

### 2026-10-19 · this commit · Phase 9 · Offline journal and shared-device hardening; local dev updated
Fixed the six issues from the initial read-only review. Sync now pulls a full owner-scoped snapshot, including tombstones, so a delayed offline create, edit or deletion cannot fall behind a clock cursor. Client timestamps still decide last-write-wins; older clients may send `since`, but it no longer filters the snapshot. This deliberately trades larger sync responses for a simple reliable protocol on small personal journals, without a database migration or new dependencies. Pull merges and device clearing use IndexedDB transactions.
- **Draft privacy:** a draft records its device-journal owner, is checked on restore, counts as unsynced work in clearing/switching prompts, and is cleared with the personal tables. Anonymous drafts are adopted with the journal on first sign-in. Existing flat drafts are preserved for their existing device journal until it is cleared.
- **Offline dates:** IndexedDB v3 adds a compound date/fishery/waterbody cache without replacing existing personal tables. Tomorrow no longer overwrites the current-conditions copy; an uncached day or fishery gets an explicit message. An older bundle with no fishery metadata is not guessed to be trout. Trip capture uses the local date, and a slow day request cannot replace a later selection.
- **Export:** JSON and CSV are built from a consistent snapshot of this device, work signed out and offline, and include unsynced entries. Deleted rows and orphaned catches are excluded. JSON includes locally stored photo bytes, gear, setups and pins; CSV includes text, quotes notes correctly and protects formula-like string cells. Photos held only on the server remain references in JSON.
- **UI:** the full-height phone Plan panel reserves space for its collapse control, keeping the title clear; the map and its controls share a labelled landmark. Updated BRAND and the roadmap; Phase 9 remains In progress with its physical-phone and deployment gates open.
- **Verified:** 236 `pytest` (new regression covers delayed creates and tombstones in all five personal tables, owner isolation and the old-client cursor); 61 frontend unit tests; production frontend build passes. Browser suites on separate disposable fixture instances: accounts **37/37**, gear **46/46**, pins **10/10**, offline **12/12**, new hardening **14/14**. Real Vite-module day-cache tests **10/10**, including a v2-to-v3 upgrade retaining an unsynced trip, date/fishery separation, legacy-cache refusal, and an Oregon evening after the UTC date changed. Full axe, including the previously excluded landmark rule: **54 scans, zero violations** (Settings, Map, Plan, Day, Journal and Log trip; all three themes at 393, 768 and 1440 px). Screenshots and phone title bounds checked. The pins script currently has ten checks; earlier documentation counted eleven (no assertion was removed).
- **Local feedback server:** rebuilt the existing `holdover-dev` API image and recreated that service with its volumes retained. Vite still runs at `http://localhost:5173`, API at `http://localhost:8020`; health reports 0.6.0, scheduler running, ten sources fresh. Confirmed Vite serves the latest cache code, and inspected the actual dev Map and Plan with real tiles, including the corrected phone title. Production and the separate local deployed container were not updated.
- **Found and fixed while testing:** draft saving raised `DataCloneError` because Svelte proxies reached IndexedDB; the form now snapshots plain values first. Initial browser attempts also hit a closed disposable server, a scan interrupted by a fixture reset, a hidden shared-device action in the test, and a receiving-device initial-sync timing race; isolated servers and explicit UI/sync waits resolved these. No failing assertion was removed. Existing build warnings (unused CSS, initial-value captures and bundle size) and one Starlette/httpx deprecation warning remain.
- **Not verified:** physical iOS/Android installation, airplane mode, GPS or storage eviction; production Secure cookies, image publishing, backup restoration or a day-long scheduler soak; new LLM output quality or pin accuracy. Full snapshots should be revisited if journal size makes transfer cost significant. No server schema or existing personal values were migrated, and no production records were changed.

### 2026-10-19 · this commit · Phase 11 · Direct river discovery, charts and visible evidence
Owner approved the proposed stream/app improvements and called out the gauge-popup detour. This first river-discovery gate makes rivers accessible as places, independent of stocking and gauges, while keeping the local Docker dev stack available for feedback.
- **Map and browsing:** a distinct wave marker opens a river immediately, taking precedence over a gauge at the same location. The dense Explore waters card offers Best bets, Rivers and Favorites, plus search across all zones, including waters without a pin. The phone's collapsed card has a direct Rivers action. Selecting a result in another zone switches zone and focuses its stored coordinate; no coordinate or access point is invented. River sheets explain that a marker may be at a gauge rather than verified fishing access.
- **Observed history:** public `/api/gauges/{id}/history?hours=24|168` reads bounded flow and water-temperature observations already stored in the database, with units and observation times. River sheets offer gauge/measurement selection, 24-hour/seven-day charts and a textual values alternative. Missing intervals break the line. Loaded histories work offline through the existing public-read cache. No new provider, scrape, dependency or schema migration was added.
- **Freshness and evidence:** each sensor has its own stale flag and timestamp; a fresh temperature cannot make old discharge look fresh. Cached sensor values are also checked by observation time in the browser, so an old cached `stale: false` is not trusted on a later offline visit. The latest available linked temperature is used for the waterbody summary. Stale discharge and forecasts do not contribute ranking evidence; future-day flow is labelled as the latest observation, not a forecast. Evidence percentages are visible on Best bets and Plan rows. Recent medians use the past seven days and are explicitly distinguished from seasonal normal and validated fishing ranges.
- **Verified:** **241 pytest**, **69 frontend unit tests**, `npm run build`, and document consistency checks pass. New regressions cover rivers without stocking, zone metadata and unpinned search, independent sensor freshness, bounded history and temperature units, stale flow/forecast exclusion, observation gaps, offline aging, favorites and evidence wording. Browser suites: accounts **37/37**, gear **46/46**, pins **10/10**, airplane-mode journal **12/12**, new rivers **12/12** (**117 checks**). The river suite clicks an actual river marker where a gauge overlaps, checks cross-zone search, Favorites, unpinned waters, temperature charts, offline reload of the list/details/history, and phone overflow. Full axe, without disabling landmarks: **108 scans, zero violations** across Settings, Map, expanded Legend, Rivers, River history, Favorites, search, Plan, Day, Journal, Log trip and Gauges in all three themes at phone/tablet/desktop widths. Screenshots inspected, including real dev-server Tualatin history and populated chart fixtures.
- **Fixture provenance:** `tests/e2e/seed-river-history.py` provides explicitly synthetic chart observations only in disposable `/tmp/holdover-...` databases, refuses other locations, and never overwrites rows; its refusal was checked against a non-temporary path. These fixtures establish chart behavior, not live measurement accuracy. The actual dev UI was separately inspected with its existing real stored readings and map tiles.
- **Found and fixed:** zone fit could override the selected search result; focusing a result now retains map focus. The phone's river browser was being unmounted when a sheet opened, losing its mode/query; it is now hidden with state retained. The new search field exposed missing shared `type=search` styling, now included. Initial test failures also identified an incorrectly linked gauge in the new test fixture, inconsistent aging of the forecast fixture's duplicated timestamp, and a chart-control label ambiguity; these were corrected. Existing gear test's substring `Back` locator also matched the new word `backed`; it now targets the exact Back control, with all assertions preserved. Existing build warnings and the Starlette/httpx deprecation warning remain.
- **Local feedback:** API/source bind mounts and Vite hot reload keep `http://localhost:5173` current; API on `:8020` is healthy at 0.6.0. Reloaded the page and checked the final direct phone Rivers action. Production was not deployed or changed. No personal rows or existing pins were edited.
- **Carried forward, already approved:** historical seasonal flow baselines, trip-area/other-zone detailed offline preparation with storage preview, photo resizing, and a fuller Favorites dashboard combining conditions and personal history. These remain unchecked in ROADMAP; this entry does not claim them complete. No physical phone, field/access verification, production rollout, or full scheduler soak was performed. Stop at the river-discovery gate for feedback before the next batch.


### 2026-10-19 · this commit · Phase 11 · Map marker and gauge-card feedback
Owner called out the cramped gauge card, oversized river waves, report badges hidden beneath other markers, and empty-looking stocking circles. This completes that bounded visual-feedback pass; Phase 11 remains In progress.
- **Marker family:** river art is reduced from 0.9 to 0.7 scale; gauge and stocking footprints are about 23 px and reports about 26 px. Stocking no longer grows with fish count: counts remain in details. A fish in a filled circle means this week, an outlined circle recent, a dotted outline older, and a calendar scheduled. Recent/older/scheduled centres have a light theme-colour tint rather than an opaque dark fill. The legend uses the identical SVG art and explains the shapes. BRAND and the regenerated icon atlas match; `scripts/render-icon-atlas.mjs` provides a repeatable renderer using existing browser-test dependencies.
- **Drawing and clicks:** reviewed and AI-read reports now draw above every other marker and the selection ring; advisories follow, then home/journal, rivers, gauges and stocking. A single priority list controls drawing and click dispatch, preventing an overlapping lower marker from opening another sheet or popup. AI-read reports retain lower opacity and the legend's unreviewed label; increasing opacity from 0.6 to 0.75 improves visibility. River clicks still open details directly, and pin-placement mode still receives the map tap first.
- **Gauge card:** long names wrap clear of a dedicated 44 px close target. Flow and trend are separated from the USGS attribution, provisional/stale labels and observation date/time (including year and timezone, respecting the device's 12/24-hour choice). Cached observations age through the existing gauge-freshness helper. The full-width action says "Open waterbody", since a gauge can also link to a reservoir, and dismisses the popup when it opens details. All source/name text is inserted as text, not HTML.
- **Verified:** 241 pytest, 71 frontend unit tests, production frontend build, and 10 document consistency tests pass. Browser regressions: rivers **12/12** (including offline reload), admin pin placement **10/10**, new marker/card suite **66/66** across phone/tablet/desktop and all three themes. The latter covers reviewed and AI-read report overlap priority, a different waterbody under the report, cached stale flags, observation timestamp, non-overlapping 44 px close targets, overflow and the waterbody action. Axe: the general **108 scans** plus **9 gauge-popup scans**, **zero violations**, with no landmark rule disabled. Screenshots of all popup sizes/themes, the refreshed atlas, and the actual dev map/legend with real tiles were inspected. The synthetic overlap/flow fixtures exist only in intercepted browser responses; the pin suite writes only to its disposable `/tmp` database.
- **Local feedback:** Vite at `http://localhost:5173` serves the changed bind-mounted source; the dev API at `:8020` is healthy at 0.6.0. No production deploy, new dependency, source, schema migration or personal-data change. An initial river-test attempt hit a fixture server that had exited (`net::ERR_CONNECTION_REFUSED`); restarting it as a persistent tool session resolved that environment failure. Existing frontend build warnings, the Starlette/httpx deprecation warning and Chromium software-renderer performance warnings remain.
- **Not checked:** physical phones, GPS, field/access accuracy or production rendering. Accounts/gear/airplane-mode journal suites were not rerun for this map-only pass; their last evidence is in the preceding entry. Low-zoom clusters can still overlap; clustering or zoom-dependent decluttering is separate future work. Stop at this feedback gate before expanding offline maps, photo handling or flow baselines.

### 2026-10-19 · this commit · Phase 11 · Reachable map overlaps, Explore selectors and aligned page headers
Owner approved the new marker art and asked how to reach overlapping items, whether the two nearby Fall Creek schedules were duplicates, and for Explore/header consistency. This is the next bounded map-feedback gate, not an expansion into other unfinished features.
- **Overlaps:** taps query a small 12 px screen-space area around the pointer. One actionable marker opens directly; multiple markers open a scrollable chooser with full names and category details. Reviewed/AI-read reports stay first, and rivers, gauges, advisories, stocking and personal markers remain individually selectable. Tile-boundary duplicates are removed by layer and identity, without merging different layers or waterbodies. Gauge cards open from the chooser, river choices open details without a gauge-card detour, and pin-placement mode still handles its tap first. Changing layers/data or entering placement mode dismisses stale popups. Stored coordinates are unchanged; there is no new source, service or dependency.
- **Fall Creek finding:** the actual dev API contains separate `Fall Creek (Willamette R)` (creek, id 19) and `Fall Creek Reservoir` (reservoir, id 20), about 0.016 degrees apart in longitude, each with its own next stocking week. They are distinct waterbodies, not duplicated rows from one schedule. The chooser shows kind, full name, and a readable scheduled week with "may change" so zoomed-out neighbors can be distinguished. No schedule or coordinate was edited.
- **Explore:** Best bets/Rivers/Favorites now use the same underline selector styling as Plan; fisheries remain filter chips. Its map badge replaces the small fish title glyph, with consistent alignment and 16 px inner gutters. The collapsed phone bar retains Rivers. The expanded phone card is opaque and can occupy up to 68% of the available map area, keeping the larger header and browsing controls usable without map symbols ghosting through text.
- **Headers:** Reports, Plan, Journal, Gear, Gauges and Settings share `PageHeader.svelte`/`PageIcon.svelte`: a fixed 48 px badge centred on the title, a 14 px gap and descriptions below. A wrapped weekly-report summary can no longer drag its icon below the Journal title row. Badge colour still follows the theme/category tokens; action buttons stay in the title row. BRAND and ROADMAP record the visual behavior.
- **Verified:** **241 pytest**, **74 frontend unit tests**, production frontend build and **10 document checks** pass. Browser suites: updated river discovery/offline reload **12/12**, pin placement **10/10**, gear **46/46**, map-marker/card suite **102/102**, and new map-layout suite **129/129**. The latter verifies title/badge geometry on six pages, three Explore selectors in one 44 px row, separate nearby Fall Creek choices and selecting the reservoir rather than the creek. Marker regressions select each report, river and gauge from the same overlap and retain the prior stale/time/close/action assertions. Full axe: **126 view scans + 18 overlap/gauge-card scans + 9 nearby-water scans = 153**, all zero violations with no landmark rule disabled. The gear suite also passes its own accessibility and offline-create/sync checks. Screenshots inspected at phone/tablet/desktop sizes and across themes, plus the actual local dev Weekly report and Explore card with real tiles/data.
- **Fixture provenance:** marker and schedule overrides are explicitly synthetic browser responses using existing stored water coordinates/ids; they never enter a database. Browser suites use a dedicated `/tmp/holdover-overlap-...` database; gear and admin-pin tests write only there. The actual local dev data and production data were not altered.
- **Found and fixed:** the shared title initially lost the space in "Weekly report" because conditional whitespace was trimmed by Svelte; the real heading assertion caught it, and an explicit space fixed it. The first general axe run therefore stopped at that heading; the complete rerun passes. An initial npm invocation used the repo root instead of `web` and was rerun from the correct directory. Existing frontend warnings and the Starlette/httpx deprecation warning remain; the temporary unused Plan row style introduced during refactoring was removed.
- **Local feedback:** the existing Docker source mounts/Vite hot reload serve the result at `http://localhost:5173`, with API `:8020`. No push or production deploy. **Not checked:** physical phones, GPS/field access, production rendering or account-registration regressions (auth/sync semantics were not changed). Pins still visually overlap at low zoom: the chooser makes them reachable; automatic clustering/spiderfying is not claimed. Stop here for feedback before the separate offline-map, photo or seasonal-flow work.

### 2026-10-19 · this commit · Phase 11 · Explore and Plan share the same expanded size
Owner asked for like-for-like Explore and Plan cards. Both now use the same desktop width variable (`min(520px, 44vw)`), full available height, 24 px title and 16 px content padding. On phones the expanded Explore fills the area above navigation with Plan's header clearance; its collapsed map bar stays compact. Zone/Legend placement uses the shared width too, avoiding a hard-coded offset for the former 380 px card. At 900–1099 px Legend becomes icon-only beside these cards after a real-browser check exposed a small Legend/Layers overlap at 900 px. BRAND and ROADMAP reflect the change.
- **Verified:** 241 pytest, 74 frontend unit tests, production frontend build and 10 document checks pass. The map-layout browser suite now asserts equal Explore/Plan width and height and the matching title size in every theme at phone/tablet/desktop widths, plus control separation at 900 px. Final suite: **153 checks**, including **12 full axe scans**, zero violations. General accessibility suite: **126 scans**, zero violations across all three themes at phone/tablet/desktop widths. Existing nearby-water chooser and exact-water selection checks remain in the layout suite. Inspected screenshots of the expanded phone card and actual local dev Explore/Plan cards at the same desktop viewport; the measured 900 px layout was also checked.
- **Local feedback:** source bind mounts keep `http://localhost:5173` current. No data, source, account/sync behavior or production deployment changed. Existing build and Starlette/httpx deprecation warnings remain. A documentation edit initially used a path relative to `web`; it was corrected to the absolute documentation path, with no file changed by the failed attempt.
- **Not checked:** physical phones, GPS, production rendering, or full accounts/gear/offline-journal regressions for this CSS-only sizing pass. Stop at this visual-feedback gate; other roadmap features remain open.

### 2026-10-19 · this commit · Additional feedback: visible Explore collapse control and stocking priority
Before the sizing feedback gate closed, the owner requested stocking above river markers (North Santiam as the example) and a collapse affordance like the other panels. Explore now has a separate 44 px edge collapse/restore button: the panel's right edge on desktop, reserved top row on phones, and a restore control when collapsed. The compact bar, direct Rivers action, query and browsing mode are retained. The title bar also continues to toggle it.
- **Stack order:** reports remain highest per the earlier request; advisory, stocking, river and gauge follow among public layers. Home/journal markers retain their existing higher personal-pin priority. The same ordered list drives drawing and chooser ordering. The real dev API confirms North Santiam id 44 has stocking, river and advisory markers at the same stored coordinate, with a gauge nearby; nothing was merged or moved. A new unit regression covers this public stack order and preserves access to all layers.
- **Final verification for the combined change:** 241 pytest from the sizing pass, 75 frontend unit tests (including the new stacking regression), production build and document checks pass. Final map-layout suite **171/171** now also clicks the separate edge control to collapse and restore Explore in all themes at phone/tablet/desktop sizes. Its **12 full axe scans** pass, including the 900 px control-spacing check. The general accessibility sweep was rerun for the added button: **126 scans, zero violations**. Inspected the actual local dev expanded/collapsed control and saved screenshots. No new data/source/account/offline behavior, physical-device qualification, push or production deployment. This supersedes the earlier entry's frontend/browser counts for the final commit.

### 2026-10-19 · this commit · Phase 11 · Separate advisory badges from waterbody artwork
Owner reported that advisory rings made otherwise readable map stacks look tangled. The ring was transparent and shared the waterbody centre, letting fish/calendar/wave strokes show through the warning. Advisories now use an opaque, approximately 20 px warning-colour badge with a dark exclamation/edge, offset about 18 px lower-left of the stored point. A short connector associates it with the waterbody; reports remain upper-right. Coordinates, source data, report/advisory priority and stocking icons are unchanged. This identifies the associated waterbody, not a surveyed advisory boundary or fishing access point. The legend and regenerated shared icon atlas use the same solid warning art.
- **Interaction:** a clear hit on the separated advisory badge opens its waterbody directly. Main-pin overlaps retain the nearby-water chooser, including the advisory. The decorative connector is excluded from hit testing and hides with the advisory layer. Map popups now draw above Layers/Legend so phone controls cannot block a popup's close button; the edge collapse button and detail sheet retain their higher priority.
- **Verified:** 241 pytest, 76 frontend unit tests, production frontend build and 10 document consistency checks pass. New browser suite **66/66** across all themes at phone/tablet/desktop sizes checks actual rendered opaque warning pixels, visible connector hue, direct badge clicks, advisory access from the centre stack, hide/show behavior without an orphan connector, and **9 full axe scans**. Existing browser suites: map layout/nearby-water selection **171/171** with **12 axe scans**, marker/gauge cards **102/102** with **18 axe scans**; general accessibility **126 scans**. All axe scans report zero violations without disabling the landmark rule. Screenshots of the four-layer synthetic stack and the actual dev overview with real tiles/data were inspected. Synthetic marker responses use an existing stored coordinate/id only in the browser; no advisory was written to a database.
- **Found and fixed:** initially applying direct-hit behavior to every marker bypassed the existing nearby Fall Creek chooser; the unchanged layout regression caught it, and direct handling was restricted to advisory badges. A new pixel assertion initially assumed a thin antialiased connector was an opaque pixel; the check now verifies warning hue plus visible brightness and verifies its disappearance when hidden, while the badge-body assertion still requires the exact opaque theme colour. The new four-item picker exposed a real close-button obstruction by Layers on phones; popup stacking was corrected and the actual close click now passes. A documentation update first used a path relative to `web` and made no change; it was rerun with absolute paths. Existing build and Starlette/httpx deprecation warnings remain.
- **Local feedback:** available through the existing Docker/Vite source mounts at `http://localhost:5173`; no push or production deployment. **Not checked:** physical phones/GPS, on-the-ground advisory/access accuracy, very dense low-zoom collisions between separate waterbodies, or full accounts/gear/airplane-mode journal suites for this map-only change. Nearby stacks still use the chooser; this does not claim automatic clustering. Stop at this visual feedback gate.
