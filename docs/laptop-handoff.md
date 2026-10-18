# Moving to your laptop: first-run checklist

> Partly superseded: the open items below are tracked in [ROADMAP.md](ROADMAP.md) (Phase 9) and what was done in
> [BUILD_LOG.md](BUILD_LOG.md). Kept for the per-item commands.

**Update 2026-10-17 (first laptop run):** the Dockerfile builds and runs; myodfw.com returns 200 to Python from a home network (item 1 below is cleared, but re-check from the server); 75 tests and the offline e2e pass; the Oregon basemap is installed (`docs/basemap.md`). Still open: items 2 to 5, HTTPS/phone testing (waiting on the server move), and the data review.

Everything below was built and tested in a cloud sandbox with fixtures and a few live reads. These are the
things that could **not** be proven there. Work down the list; each has the command that checks it.

## 0. Get it running

    git clone https://github.com/d3mocide/Holdover && cd Holdover
    cp .env.example .env            # set USER_AGENT (with a contact address); HOME_LAT/HOME_LON are only the server default now
    docker compose exec holdover python -m app.cli create-user YOURNAME   # first user is the admin (docs/accounts.md)
    docker compose up --build       # built and run on the laptop 2026-10-17; host port is HOLDOVER_PORT (default 8000)

Or without Docker: `pip install -e '.[dev]'`, `pytest` (75 tests), `cd web && npm ci && npm run build`, then
`python -m app.cli migrate && python -m app.cli seed && uvicorn app.main:app`.

## 1. Must check from your own network

| # | Check | How | If it fails |
| --- | --- | --- | --- |
| 1 | **myodfw.com returns 403 to Python** (curl worked in the sandbox) | `python -m app.cli stocking` then open `/healthz` | See `docs/sources.md`. Ask ODFW for a feed, or swap `app/http.py` for a curl-based fetcher. The weekly report and stocking schedule are both on this host. |
| 2 | Read myodfw.com terms of use (only robots.txt was read) | by hand | Record the outcome in `docs/sources.md` before enabling the scheduler |
| 3 | Scheduler timing and the `America/Los_Angeles` crons | `docker compose logs`, `/healthz` over a day | Cron times are in `app/scheduler.py` |

## 2. Data that is a best guess: review it

- **Waterbody coordinates** (`app/seed.py`): cross-checked 2026-10-18 against OSM names in the basemap. 51 of 58 are pinned
  (35 verified or snapped), 7 still have no pin. Per-row status and how to fix any pin: `docs/waterbody-pins.md`.
  Gauge coordinates, by contrast, were verified against live USGS.
- **Gauge-to-waterbody links** (`GAUGE_LINKS`; Leaburg, Cottage Grove and Estacada tailwater gauges added 2026-10-18) and **fishery hints** (`FISHERY_HINTS`): my judgement. Steelhead
  and warmwater lists are short until you accept report items.
- **Favorites**: per account now (star on a waterbody). They get their own NWS forecast, which also
  auto-refreshes one stocked waterbody per ~0.25 degree cell.
- **Scoring weights and curves** (`app/scoring.py`, `.env` `W_*`): starting points, not validated. Use the
  "Why this score" breakdown to tune them against your own experience.

## 3. Needs your LLM

Nothing has run against a real model; tests use a mock and `scripts/fake_llm.py`.

    LLM_BASE_URL=http://localhost:11434/v1 LLM_MODEL=<model>
    python -m app.cli reports        # fetch report, extract items, write digests
    python -m app.cli explain        # planner explanations and pack intros

Run extraction on several saved reports and read the review queue (Settings, with the token set) before
trusting a model. Grounding guards reject invented sentences, numbers, places and species, but they are a
safety net, not a quality measure. Tune prompts in `app/llm/prompts/__init__.py` (bump the version string
and old generations are ignored, not overwritten).

## 4. Needs a real phone and real map data

- **Basemap**: none installed. `docs/basemap.md` has the extract command. The map expects Protomaps v4 layer
  names (`water`, `roads`). `scripts/make_test_pmtiles.py` makes toy tiles for testing only.
- **Offline**: proven in headless Chromium with the network switched off (`tests/e2e/`). Not proven on iOS or
  Android: storage quotas, service-worker eviction, GPS, and "Add to Home Screen" are all untested. HTTPS (via
  your reverse proxy) is required for service workers off localhost.
- **Prepare for offline** downloads tiles into IndexedDB; real Oregon tiles are much larger than the toy
  file, so check the tile-count estimate in the dialog and your device's free space.

## 5. Not built

- ODF wildfire / fire-restriction feed (no source inspected).
- OWRD gauges (access method unverified).
- Coast and marine, light theme, statewide coverage, PostGIS migration, journal-informed scoring (phase 6).
- Editing an existing trip (create and delete only). Per-waterbody journal stats are minimal.
- Zone polygons from the ODFW ArcGIS fish-district layer.

## Things I learned that you may care about

- The OHA web page renders its table in the browser; the app reads the public ArcGIS layer behind OHA's own
  advisory map instead. It is not a documented API and may change. A real advisory (North Fork Santiam
  precaution) showed up in the first live test.
- USGS's legacy `waterservices` endpoint was live and returned provisional data on 2026-10-17.
- The Recreation Report currently publishes only "best bets" per zone; ODFW says other parts are paused
  while it is revamped, so extraction has little text to work with.
