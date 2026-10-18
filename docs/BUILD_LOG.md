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
