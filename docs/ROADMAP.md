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
| 8 | Gear | In progress |
| 9 | Hardening and first deployment | Planned |
| 10 | Journal depth and journal-informed scoring | Planned |
| 11 | More sources and statewide coverage | Planned |
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

**Status:** In progress. **Goal:** a per-person tackle database that feeds the journal and, later, the planner.

Decisions (owner, 2026-10-17): optional "gear used" picker on trips; items, setups, trip link and basic stats in
v1; a small Oregon starter catalog.

**Gate:** gear created offline syncs to the account; a trip can record a setup and the lures used; stats show fish by
lure and setup; no other account can read or reference it; tests, e2e and axe pass.

- [x] Server: `gear_item`, `gear_setup`, trip/catch references, owner-scoped sync, reference checks, export (6 tests)
- [x] Local: IndexedDB schema v2, gear and setups in the sync queue and device-ownership logic
- [ ] Starter catalog (about 60 common Oregon lures, flies, tackle) and pure stats functions with unit tests
- [ ] Gear tab: items (with photos), setups, stats
- [ ] Log-trip picker (setup, lures, "caught on") and gear shown on journal cards
- [ ] Browser test: offline create and sync, two-account isolation
- [ ] Docs: `accounts.md` data table, BRAND icon additions

## Phase 9: Hardening and first deployment

**Status:** Planned. **Goal:** the things the sandbox and the laptop could not prove. Best done when the app moves to
its server.

**Gate:** installed on a real phone over HTTPS and used offline; a real LLM tried; a backup restored.

- [ ] HTTPS via reverse proxy; verify the Secure cookie and forwarded headers; per-address login throttle
- [ ] iOS and Android: install, offline reload, GPS, storage quota and eviction; request persistent storage
- [ ] Read myodfw.com, OHA, ODF and NWS terms of use; record in `docs/sources.md` before enabling the scheduler
- [ ] Watch the scheduler for a day (timings, `/healthz`)
- [ ] Choose a local model; run extraction and explanations on saved reports and review the output
- [ ] Restore a nightly backup into a fresh container (the backup job exists, restore is untested)
- [ ] Data review: 7 unpinned waterbodies, 4 likely and 12 unverified pins, fishery hints, gauge links
- [ ] Confirm the schema runs on Postgres (kept portable, never tested)

## Phase 10: Journal depth and journal-informed scoring

**Status:** Planned. **Goal:** use what people log. Needs Phase 8's gear data.

- [ ] Edit an existing trip
- [ ] Per-waterbody history: catches by species, conditions of the best days
- [ ] Journal-informed scoring factor (for example, waters and lures that worked under similar flows)
- [ ] Gear in the pack list ("you already own this")

## Phase 11: More sources and statewide coverage

**Status:** Planned.

- [ ] ODF wildfire and fire-restriction feed (no source inspected yet)
- [ ] OWRD gauges (access method unverified)
- [ ] Zone polygons from the ODFW fish-district ArcGIS layer
- [ ] Statewide coverage (more zones, bigger seed) and, if SQLite stops being enough, PostGIS

## Phase 12: Coast and marine

**Status:** Planned. Tides, coastal and marine layers. Out of v1 scope by decision.

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
