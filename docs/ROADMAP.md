# Holdover roadmap

What is planned, what is done, and why plans changed. **This file answers "what are we building and where are we".**
For "what was actually done and how it was checked", see [BUILD_LOG.md](BUILD_LOG.md). The original brief is kept
unedited in [reference/original-handoff.md](reference/original-handoff.md). Rules for working on the project are in
[AGENTS.md](../AGENTS.md).

**How to keep this honest**

- Change a phase's status or tick an item in the **same commit** as the work, and add a BUILD_LOG entry for it.
- A phase is **Done** only when its gate's evidence exists. A gate that was met only against fixtures or a mock
  says so, and the gap stays listed under "Carried forward".
- Statuses: `Done`, `In progress`, `Planned`. Do not invent others.
- `tests/test_docs.py` checks that every Done phase has a build-log entry and that this file's links resolve.

## At a glance

| Phase | Name | Status |
| --- | --- | --- |
| 1 | Foundation and stocking map | Done |
| 2 | Reports and LLM | Done |
| 3 | Conditions | Done |
| 4 | Journal and offline | Done |
| 5 | Planner | Done |
| 6 | Design system | Done |
| 7 | Accounts | Done |
| 8 | Gear | Done |
| 9 | Hardening and first deployment | In progress |
| 10 | Journal depth and journal-informed scoring | In progress |
| 11 | More sources and statewide coverage | In progress |
| 12 | Coast and marine | Planned |
| 13 | Light theme | Planned |

Phases 1-5 are the original handoff's. 6-8 were added during the build. 9-13 are the remaining work, including the
handoff's "Later" items (its phase 6), split so each can be finished and checked on its own.

---

## Phase 1: Foundation and stocking map

**Status:** Done. **Goal:** real stocking data on a map, in a container, with the plumbing everything else needs.

**Gate (from the handoff):** this week's real stocking schedule appears at correct locations, unmatched aliases show
in an admin list, parser tests pass against saved fixtures, `/healthz` reports source status.

- [x] Repo, Dockerfile, compose, FastAPI skeleton, SQLite (WAL) with Alembic
- [x] `raw_fetch` stored before parsing, hash-skip, stale on parse failure
- [x] Willamette seed (58 waterbodies) with ODFW label aliases and a matching review queue
- [x] Stocking scraper with append-only snapshots (zone value 6)
- [x] Map with the stocking layer, theme tokens, nav shell
- [x] Gate evidence: live fetch from a home network returned all 500 rows; pins cross-checked against OSM (Phase 8 data work); parser and API tests pass; `/healthz` shows per-source status

**Carried forward:** 7 waterbodies have no pin, 4 pins are "likely", 12 are still unverified
([waterbody-pins.md](waterbody-pins.md)). ODFW and the other sources' terms of use are unread (`docs/sources.md`);
only robots.txt was read.

## Phase 2: Reports and LLM

**Status:** Done (against fixtures and a mock). **Goal:** turn the weekly Recreation Report into reviewed, sourced items.

**Gate:** saved reports replay into reviewed items and digests, items cite a verbatim source sentence, and killing the
LLM host leaves the UI working with raw items.

- [x] Report scraper and parser, zone split
- [x] Schema-validated extraction; rejects items whose `source_sentence` is not in the report
- [x] Zone digests, `generation` cache, prompt versioning
- [x] Review queue (admin) and report items on the sheet
- [x] Gate evidence: fixture replay tests; grounding guards; LLM-unreachable path tested with a mock

**Carried forward:** **never run against a real model.** Choose and test one on several saved reports before
trusting it (Phase 9). ODFW currently publishes only "best bets" per zone while it revamps the report, so extraction
has little text to work with.

## Phase 3: Conditions

**Status:** Done. **Goal:** flow, weather, light and advisories next to each waterbody.

**Gate:** a sheet shows flow, weather and latest report notes together with "as of" times; a stale source shows a badge.

- [x] USGS gauges (16, coordinates verified live), linked to waterbodies; values labelled provisional
- [x] NWS forecast (hourly for favorites plus one stocked waterbody per ~0.25 degree cell)
- [x] Sun and moon computed locally
- [x] OHA algae advisories (read from the public ArcGIS layer behind OHA's map)
- [x] Waterbody sheet, day-of view, gauges page, stale badges

**Carried forward:** ODF wildfire / fire restrictions and OWRD gauges are not built (Phase 11).

## Phase 4: Journal and offline

**Status:** Done (headless Chromium only). **Goal:** log trips with no signal and lose nothing.

**Gate:** a trip logged in airplane mode syncs afterwards, the shell and cached map load with no network, a duplicate
push creates no duplicates.

- [x] Trips, catches, pins, photos; auto-captured conditions (live or cached, marked)
- [x] IndexedDB (Dexie) write-first, sync queue with backoff, soft delete, last-write-wins
- [x] Service worker, installable PWA, offline map tiles ("Prepare for offline"), JSON and CSV export
- [x] Gate evidence: `tests/e2e/offline.mjs` (11 checks) passes with the network switched off

**Carried forward:** **not proven on iOS or Android** (storage quotas, service-worker eviction, GPS, Add to Home
Screen). Tiles are stored in IndexedDB, not the Cache API as the handoff said (works the same, easier to count and
clear). The handoff asked to request persistent storage: not done. Trip editing is create and delete only (Phase 10).

## Phase 5: Planner

**Status:** Done (against a mock LLM). **Goal:** an explainable ranking and a pack list.

**Gate:** the ranking is explainable from the factor breakdown, and generated text never contains a number or species
not in its input.

- [x] Scoring with per-factor breakdown (stocking, report, flow, forecast, distance), weights in config
- [x] Grounded explanations (numbers, places, species checked against the input), template fallback
- [x] Pack list (template-first), date and fishery filters, "Why this score"
- [x] Gate evidence: scoring and grounding tests

**Carried forward:** weights are untested starting points; tune against real experience. Real-LLM wording unchecked.

## Phase 6: Design system

**Status:** Done. **Goal:** a premium, consistent look across three themes. Added after the handoff; see
[BRAND.md](BRAND.md), which is now the authority for visuals.

- [x] Glass system (two tiers), 16 px gutters, content-sized side panel, full-bleed map under floating panels
- [x] Custom icon set and brand mark, favicon and PWA icons (incl. maskable), SVG map markers
- [x] Redesigned basemap: ocean as ground, muted roads, forest and water tints, lakes as closed shapes, rivers as
      centerlines, bundled Noto Sans labels that work offline
- [x] Fir & Steelhead refresh; Redband and Night Bite ported (a theme is a palette; components use no literal colours)
- [x] Views restyled: Journal, Gauges, Settings, Log trip, Day view; tablet and phone layouts fixed
- [x] Accessibility: axe-core reports zero violations across 3 themes, desktop and phone
- [x] Brand guide, agent rules, roadmap and build log (this document set)

**Carried forward / backlog:** pulse on "this week" pins; labels sometimes sit under pins; the original phone mockup's
search pill, layer chips and bottom-sheet handle were not built (a Layers pill and Legend pill took their place);
pack chips on the waterbody sheet (pack lives in the day view).

## Phase 7: Accounts

**Status:** Done. **Goal:** let more than one person use it, without losing the open, no-login experience.
Replaces the handoff's single user and static bearer token.

Decisions (owner, 2026-10-17): optional accounts; invite-link sign-up; username and password; token removed.

- [x] Users, server-side sessions (hashed token in an HttpOnly cookie), scrypt passwords, login throttle, CSRF header
- [x] Per-user home, favorites (favorites get their own forecast refresh) and journal; owner-scoped sync, photos
- [x] Admin: people, invites, disable, reset, last-admin guard; first admin created from the CLI
- [x] Signed-out mode stays fully usable (local journal, home, favorites); sign-in merges them
- [x] Shared-device safety (switching accounts never leaks unsynced entries) and offline-aware sign-in state
- [x] Gate evidence: 20 account tests plus a 37-check browser run; see [accounts.md](accounts.md)

**Carried forward:** password reset is by an admin (no email); no two-factor or OAuth. Behind a reverse proxy,
the login throttle sees the proxy's address, so configure forwarded headers or rely on the per-username limit (Phase 9).

## Phase 8: Gear

**Status:** Done. **Goal:** a per-person tackle database that feeds the journal and, later, the planner.

Decisions (owner, 2026-10-17): optional "gear used" picker on trips; items, setups, trip link and basic stats in
v1; a small Oregon starter catalog.

**Gate:** gear created offline syncs to the account; a trip can record a setup and the lures used; stats show fish by
lure and setup; no other account can read or reference it; tests, e2e and axe pass.

- [x] Server: `gear_item`, `gear_setup`, trip/catch references, owner-scoped sync, reference checks, export (6 tests)
- [x] Local: IndexedDB schema v2, gear and setups in the sync queue and the device-ownership logic
- [x] Starter catalog (77 common Oregon lures, flies and tackle; brands only where certain) and pure stats functions (8 unit tests)
- [x] Gear tab: items with photos, search and filters; setups; "What works" stats; add/edit/retire/delete
- [x] Log-trip picker (setup, lures, "caught on") and gear on journal cards
- [x] Gate evidence: `tests/e2e/gear.mjs` (a second account that cannot see or reference the gear, an item
      created offline syncing after reconnect, axe clean on every gear view); backend and unit tests

**Carried forward:** stats are computed on this device from the local journal (so they work offline) and show shared
credit for "on trips"; gear is not yet used by the planner or the pack list (Phase 10); gear photos are uploaded at
full size (no resizing yet); gear is not shown on the waterbody sheet.

## Phase 9: Hardening and first deployment

**Status:** In progress. **Goal:** the things the sandbox and the laptop could not prove. Best done when the app moves to
its server.

**Gate:** installed on a real phone over HTTPS and used offline; a real LLM tried; a backup restored; and the USGS data source migrated before the legacy API is retired.

- [x] **USGS migrated to the Water Data API** (done 2026-10-18, ahead of the early-2027 retirement of `waterservices.usgs.gov`): all 16 gauges, same values, no key; routine polls use latest values, with gap-fill and a first-run backfill ([data-source-options.md](data-source-options.md))
- [ ] Delete the legacy USGS fallback (`USGS_API=legacy`) once USGS retires the old endpoint
- [x] Per-address login throttle that works behind a proxy (`TRUSTED_PROXY_HOPS`; tested with spoofed headers)
- [ ] **Publish the image** (`.github/workflows/`, amd64 + arm64 to ghcr.io) and run it on the owner's Raspberry Pi: workflows written 2026-10-18, **never run**; needs a push to `main`, then a pull on the Pi
- [x] Separate dev stack (`docker-compose.dev.yml`: reload, Vite, own volumes), built and run 2026-10-18
- [x] Journal hardening: late offline arrivals reach other devices; drafts are owner-checked and cleared on shared-device removal;
      offline day bundles match the date and fishery; JSON/CSV export includes the device's unsynced entries
- [x] Phone Plan title clear of the collapse control; map controls inside a labelled landmark
- Production observed on 2026-10-19: `holdover.int.d3mo.us` serves 0.6.0 with its scheduler running and ten sources fresh.
  This does not establish the Pi, image-publishing workflow, Secure-cookie, phone, or day-long scheduler gates below.
- [ ] HTTPS via reverse proxy: verify the Secure cookie and forwarded headers on the real server
- [x] Request persistent storage (when a trip is saved or offline data is prepared) and show storage status in Settings
- [ ] iOS and Android: install, offline reload, GPS, storage quota and eviction
- [x] Read the published terms for ODFW, OHA, NWS, USGS and Protomaps/OSM and record them (`docs/sources.md`); found and fixed missing OpenStreetMap attribution and added data credits
- [ ] **Owner:** decide whether to email ODFW (and OHA) about using their public data; ODF terms still unread (feed not built)
- [ ] Watch the scheduler for a day (timings, `/healthz`)
- [ ] Choose a local model; run extraction and explanations on saved reports and review the output. **Partly done 2026-10-18:** `gemma4-e4b` on the owner's server extracted and summarised the saved report (see the build log); explanations and pack intros not yet run, quality reviewed on one report only
- [x] Restore a backup into a fresh container (drill done 2026-10-18; see [operations.md](operations.md)). Still to do: copy backups and photos off the machine
- [ ] Data review: 7 unpinned waterbodies, 4 likely and 12 unverified pins, fishery hints, gauge links
- [x] Schema runs on Postgres 16: 115 tests plus the browser tests pass on it (SQLite-to-Postgres data copy not built)

## Phase 10: Journal depth and journal-informed scoring

**Status:** In progress. **Goal:** use what people log. Needs Phase 8's gear data.

- [x] Edit an existing trip (in place; keeps the conditions captured at the time; removed catches are soft-deleted)
- [x] Per-waterbody history on the sheet: trips, fish, catches by species, best day with its conditions, most productive lure
- [ ] Journal-informed scoring factor (for example, waters and lures that worked under similar flows)
- [x] Gear in the pack list: the day view shows "You have: ..." under template items you own (never says anything is missing)

## Phase 11: More sources and statewide coverage

**Status:** In progress (reservoir levels done). APIs researched and probed on 2026-10-18: see [data-source-options.md](data-source-options.md) for
endpoints, what was verified, terms, effort and the recommended order. The owner approved building from government sources (2026-10-18). Each source still needs its
terms recorded in `docs/sources.md`, fixtures, tests, a stale badge and a credit.

- [x] **Reservoir levels** from the Army Corps (9 Willamette reservoirs that have a waterbody here; JSON, undocumented service with a certificate
      quirk): elevation, 24 h / 7 d change, and the same date in the three previous years. Built 2026-10-18
- [x] **Fire card**: ODF fire danger by regulated-use area (the level and area code for the 28 of 58 waterbodies inside an ODF zone) and NIFC active wildfire perimeters within 50 km ("active fire near here", never a closure claim). Built 2026-10-18
- [x] **Fire map layer**: ODF danger zones and NIFC perimeters drawn on the map (Layers toggle, Legend entries), served from the stored responses by `/api/fire/map`. Built 2026-10-18
- [ ] NASA FIRMS hotspots: the owner is not sure FIRMS is wanted (it needs a free key)
- [x] **River flood status** from NOAA NWPS: NOAA's official flood category, stage and forecast on 14 of the 16 USGS gauges (the other two have only reservoir gauges at NWPS), on the sheet's flow rows and the Gauges page. Built 2026-10-18
- [ ] **Rivers**: the Tualatin River is the pilot (three gauges, water quality, NOAA flood status, Willamette Falls fish counts from DART). Mirror to the Clackamas, Sandy, Santiam, McKenzie and others once the owner is happy with the Tualatin; StreamNet and OWRD are researched (docs/data-source-options.md section 10) and not built
- [ ] OWRD gauges: station list is public but readings have no documented API; probably skip (USGS covers the main rivers)
- [ ] ODFW fish-district polygons: available on ArcGIS Online (the handoff's URL is blocked), but they are not the six stocking zones; low value. **New (2026-10-18):** the *Angling Zones* (Sport Fishing Regulations zones) are the useful layer, free to use with an ODFW credit, but the server is firewalled from here: see data-source-options 6b
- [x] Statewide coverage: all six ODFW zones. Central, Northwest, Southwest, Northeast and Southeast were added 2026-10-18 (see the build log), each a module in `app/zones`, pins from OpenStreetMap (many left unpinned for you to place), live USGS gauges, a zone pill on the map. Still Willamette-only: Corps reservoirs, NOAA flood status, the offline map region.

## Phase 12: Coast and marine

**Status:** Planned. Tides, coastal and marine layers. Out of v1 scope by decision. NOAA CO-OPS has a documented, free tides API (verified with South Beach); see [data-source-options.md](data-source-options.md).

## Phase 13: Light theme

**Status:** Planned. The token system supports it; the palette, map and icon treatment need designing and a
[BRAND.md](BRAND.md) section first.

---

## Where the build departs from the original handoff

| Handoff said | Now | Why |
| --- | --- | --- |
| Single user, one static bearer token | Optional accounts, invite sign-up, per-user data | A second person may use it (handoff §13.6 asked to confirm this) |
| "No shadows or gradients", 8/12/16 px radii | Glass surfaces, soft shadows, a glow gradient behind pages, 10/14/20 px radii | Owner asked for a more premium, modern feel; [BRAND.md](BRAND.md) is the authority |
| Freshness ramp is three teals | Lime, teal, slate in Fir (other themes have their own); gauges blue | Colour-blind-safe hue separation reads better than lightness alone |
| Offline tiles in the Cache API | In IndexedDB | Simpler to count, cap and clear |
| `starred` waterbody flag | Per-account favorites | Follows from accounts |
| `HOLDOVER_TOKEN` | Removed | Follows from accounts |

## Handoff section 13: open items

| # | Item | Status |
| --- | --- | --- |
| 1 | Terms of use and robots for myodfw.com, OHA, ODF, NWS | **Open.** Robots read for some; terms unread. Phase 9 |
| 2 | USGS endpoint and OWRD access | USGS legacy endpoint confirmed live 2026-10-17. OWRD open (Phase 11) |
| 3 | Inspect OHA, ODF and Recreation Report structure | Report and OHA done (OHA via ArcGIS). ODF open (Phase 11) |
| 4 | Willamette zone filter value | Done: `stocking_zone_value = 6` |
| 5 | Owner's starred waterbodies, gauges, LLM model and hardware | Test favorites only; 16 gauges chosen; **model unknown** (Phase 9) |
| 6 | Will anyone besides the owner use it | **Yes, probably: accounts built** (Phase 7) |
| 7 | Source and document an Oregon PMTiles extract | Done: Protomaps build 2026-10-16, Oregon bbox, ODbL ([basemap.md](basemap.md)) |

## Backlog (unscheduled)

- Pulse on "this week" pins; avoid labels under pins
- Admin screen for editing pins (today: an API call, see [waterbody-pins.md](waterbody-pins.md))
- Password reset by email, two-factor sign-in (deliberately out of scope for now)
- More glyph ranges for map labels if non-Latin names matter
