> **Historical record. Do not edit.** This is the original coding-agent handoff, kept verbatim so the build can be
> checked against it. Where it disagrees with the code, [ROADMAP.md](../ROADMAP.md) (what is planned and why it
> changed) and [BUILD_LOG.md](../BUILD_LOG.md) (what was actually done) are authoritative. The main deliberate
> departures: accounts replaced the single user and bearer token, and the UI moved from flat "no shadows or
> gradients" to the glass system in [BRAND.md](../BRAND.md).

# Holdover: Coding Agent Handoff

A self-hosted PWA for Oregon fishing: one pane of glass for "where should I fish, when, and what do I bring," plus a technical angler's journal. Single user, one container, one SQLite file, local LLM.

**Status:** design locked by the owner (Will). Mockups approved. Fir & Steelhead is the default theme. Build in the phase order in section 13 and stop at each acceptance gate.

---

## 0. Locked decisions

| Area | Decision |
| --- | --- |
| Name | **Holdover** (ODFW's term for stocked fish that survive to the next season) |
| Home zone | Willamette Valley and nearby Cascades. Statewide data is stored but secondary. |
| v1 fisheries | Stocked trout, steelhead and salmon, warmwater (bass, panfish, walleye, shad). Coast and marine are out of v1. |
| Deployment | **One Docker container** plus a mounted volume. No separate worker, queue or database server. |
| Database | **SQLite (WAL)** via SQLAlchemy 2 and Alembic. Must stay Postgres-ready: no SQLite-only SQL in application code, geometry as lat/lon and GeoJSON. |
| Backend | Python 3.12, FastAPI, APScheduler in-process, httpx, selectolax or BeautifulSoup. **Single uvicorn worker** (the scheduler lives in-process). |
| Frontend | Svelte (or React, agent's choice, but pick one and keep it small), Vite, MapLibre GL, Workbox via `vite-plugin-pwa`, Dexie for IndexedDB. |
| Basemap | Oregon **PMTiles** file served from the container with HTTP range requests. |
| LLM | Local server, OpenAI-compatible endpoint (`LLM_BASE_URL`, `LLM_MODEL`). Probably Ollama. Model and hardware are not yet known, so the model is configuration. |
| Offline | **Must work offline**: app shell, journal writes, cached conditions, cached map tiles. |
| Access | Single user, behind the owner's reverse proxy or VPN. Static bearer token for write endpoints. HTTPS is required for service workers, so TLS terminates at the proxy. |
| Theme | Three themes, switchable in Settings: **Fir & Steelhead (default)**, Redband, Night Bite. Dark-first, with a real light theme still to be designed later. |
| Regulations | The app links to official ODFW regulation pages. It **never** restates rules, closures or limits as authoritative. |

## 1. Architecture

```
Browser (PWA)  ──HTTPS──▶  reverse proxy  ──▶  holdover container
 service worker                                  ├─ FastAPI (REST + static PWA + PMTiles)
 IndexedDB (journal queue)                       ├─ APScheduler jobs (scrapers, pollers, LLM jobs)
                                                 └─ SQLite file on /data
                                   LLM_BASE_URL ──▶ Ollama on the local server (outside the container)
```

Principles:

1. Scrapers and pollers run on a schedule, never per user request.
2. Every raw upstream response is stored before parsing, so parser bugs become re-runs instead of lost data.
3. Scraped data is append-only. Journal data is client-created with UUIDs and kept separate so re-scraping can never touch it.
4. The LLM reads and writes text. It never decides facts. Numbers, dates and rankings come from the database.
5. If the LLM host is down, the UI still works from cached generations and shows raw extracted items.

### Repo layout (suggested)

```
holdover/
  Dockerfile                # multi-stage: node build of web/ then python:3.12-slim
  docker-compose.yml
  pyproject.toml
  app/
    main.py                 # FastAPI app, mounts /api, static PWA, /tiles
    config.py               # pydantic-settings, env vars below
    db.py, models.py, migrations/ (alembic)
    scheduler.py            # APScheduler job registration
    sources/                # one module per source, each with fetch() and parse()
      odfw_stocking.py  odfw_report.py  usgs.py  nws.py  arcgis.py  oha.py
    llm/                    # client.py, extract.py, summarize.py, explain.py, schemas.py, prompts/
    scoring.py
    api/                    # routers: map, spots, waterbodies, reports, journal, sync, admin
  web/                      # PWA source (src/, public/, vite.config)
  tests/
    fixtures/               # saved HTML and JSON from every source
  data/                     # gitignored; mounted at /data in the container
```

### Container and volume

- `/data/holdover.db` (SQLite, WAL), `/data/raw/` (optional file store for large raw bodies), `/data/photos/`, `/data/tiles/oregon.pmtiles`.
- Nightly job: `VACUUM INTO /data/backup/holdover-YYYYMMDD.db`, keep the last 7.
- `GET /healthz` returns scheduler status and last successful run per source.
- Run as a non-root user.

### Environment variables

| Var | Purpose | Default |
| --- | --- | --- |
| `HOLDOVER_TOKEN` | Bearer token for write endpoints | required |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:////data/holdover.db` |
| `LLM_BASE_URL` | OpenAI-compatible base URL | required for LLM jobs |
| `LLM_MODEL` | Model name | required for LLM jobs |
| `LLM_API_KEY` | Optional | empty |
| `HOME_LAT`, `HOME_LON` | Distance origin for the planner | owner sets |
| `USER_AGENT` | Identifying UA for all outbound requests, include contact | required |
| `TZ` | `America/Los_Angeles` | set |

## 2. Data sources and ingestion

Poll rates are deliberately low. Send `USER_AGENT` on every request. **Before the first scrape, read each site's terms and robots rules** and record the outcome in `docs/sources.md`. Nobody has done this yet.

| Source | URL or endpoint | Cadence | Notes |
| --- | --- | --- | --- |
| ODFW trout stocking schedule | `https://myodfw.com/fishing/species/trout/stocking-schedule` | Daily | HTML table: Week of (Monday start), Waterbody, Zone/Office, Legals, Trophy, Brood, Fingerling, Total. Filterable by query params such as `field_zone_value`, `field_waterbody_name_value_1`, `field_planned_stocking_date_value[date]`, `field_planned_stocking_date_end_value[date]`. Discover the Willamette zone value from the page's zone selector (one example URL used `field_zone_value=2` for a different zone). The page says the schedule shows the **week**, not the day, and can change without notice. |
| ODFW weekly Recreation Report | `https://myodfw.com/index.php/taxonomy/term/1` (index page titled "Recreation Report") | Twice daily Wed to Fri, hash compare | Published weekly, typically Thursday (the July 9, 2026 issue was a Thursday). Contains a statewide "best bets" block plus per-zone and per-waterbody notes. Discover zone and waterbody sub-pages by following links from the index. |
| USGS streamflow | `https://waterservices.usgs.gov/nwis/iv/?format=json&sites=<ids>&parameterCd=00060,00065,00010&period=P1D` | 30 to 60 min, starred gauges only | 00060 discharge (cfs), 00065 gage height (ft), 00010 water temp where the site has it. Keyless, public domain, **provisional**. USGS is modernizing its Water Data APIs, so put this behind an adapter interface and verify the endpoint is still current before building. |
| OWRD gages | Oregon Water Resources Department | later | Appears alongside USGS on the USGS Oregon pages. Access method not yet verified. |
| ODFW ArcGIS | `https://nrimp.dfw.state.or.us/arcgis/rest/services/ODFW_Admin/FishBioDistricts/FeatureServer/0` and `https://services.arcgis.com/uUvqNMGPm7axC2dD/ArcGIS/rest/services/FishBioDistrictst/FeatureServer` (WGS84 variant, note the trailing `t` in the service name) | Monthly | Fish biologist district boundaries, GeoJSON via `query?f=geojson&where=1=1`. Use for zone polygons. Stocking locations are **not** in this layer. |
| NWS forecast | `https://api.weather.gov/points/{lat},{lon}` then the returned forecast URLs | Hourly for starred waterbodies | Free, requires the identifying User-Agent. Not yet verified in this project, confirm the current response shape. |
| OHA harmful algae advisories | linked from the ODFW report (Oregon Health Authority) | Daily | HTML, format not yet inspected. |
| ODF wildfire page | linked from the ODFW report | Daily | HTML, format not yet inspected. |
| Sun and moon | computed locally (e.g. `astral`) | none | No feed. |

### Ingestion rules

1. Fetch, then insert a `raw_fetch` row (source, url, fetched_at, status, content_hash, body) **before** parsing.
2. If the content hash equals the previous fetch for that URL, skip parsing.
3. Parsers are pure functions of the stored body. Test them against `tests/fixtures/`.
4. On parse failure: keep the last good data, mark the source **stale** in `/healthz` and in the UI, log the error with the `raw_fetch` id.
5. Stocking rows are snapshotted, never overwritten. A planned stocking that later moves or disappears stays visible in history.
6. Respect HTTP caching headers. Back off on 429 and 5xx.

### Waterbody matching

ODFW labels waterbodies in shorthand (e.g. `SANTIAM R, N FK-2`, `DEXTER RES`, `LAKE IN THE WOODS`, `ROW R NATURE PK-Fmr Cott.`). Matching is the biggest manual-ish piece:

1. Seed `waterbody` for the Willamette zone with canonical names, kind, lat/lon, zone, species, regs URL.
2. Normalize alias text (uppercase, strip punctuation and suffixes like `-2`, expand `R`, `RES`, `LK`, `PD`, `CR`, `FK`) and match to `waterbody_alias`.
3. Unmatched aliases go to the admin review queue. The LLM may **propose** a match with a confidence, but only a human-confirmed alias is used on the map. Unconfirmed items appear in a "needs review" list, not as pins.
4. Coordinates come from the seed. Do not geocode silently.

## 3. Data model (SQLite DDL, keep portable)

```sql
CREATE TABLE waterbody (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,          -- lake|pond|river|reservoir|creek
  lat REAL, lon REAL, zone TEXT, species_json TEXT, regs_url TEXT,
  starred INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE waterbody_alias (
  id INTEGER PRIMARY KEY, alias_text TEXT NOT NULL, source TEXT NOT NULL,
  waterbody_id INTEGER REFERENCES waterbody(id), confirmed INTEGER NOT NULL DEFAULT 0,
  proposed_confidence REAL, UNIQUE(alias_text, source)
);
CREATE TABLE raw_fetch (
  id INTEGER PRIMARY KEY, source TEXT NOT NULL, url TEXT NOT NULL, fetched_at TEXT NOT NULL,
  status INTEGER, content_hash TEXT, body BLOB, parse_ok INTEGER
);
CREATE TABLE stocking_snapshot (
  id INTEGER PRIMARY KEY, raw_fetch_id INTEGER REFERENCES raw_fetch(id), scraped_at TEXT NOT NULL,
  week_of TEXT NOT NULL, alias_id INTEGER REFERENCES waterbody_alias(id),
  zone_office TEXT, legals INTEGER, trophy INTEGER, brood INTEGER, fingerling INTEGER, total INTEGER
);
CREATE TABLE report (
  id INTEGER PRIMARY KEY, raw_fetch_id INTEGER REFERENCES raw_fetch(id), zone TEXT, issued_on TEXT,
  summary_text TEXT, model TEXT, prompt_version TEXT, generated_at TEXT
);
CREATE TABLE report_item (
  id INTEGER PRIMARY KEY, report_id INTEGER REFERENCES report(id), waterbody_id INTEGER REFERENCES waterbody(id),
  waterbody_raw TEXT, species TEXT, rating TEXT,                           -- excellent|good|fair|slow|unknown
  note TEXT, source_sentence TEXT, status TEXT NOT NULL DEFAULT 'review'   -- review|accepted|rejected
);
CREATE TABLE gauge (
  id INTEGER PRIMARY KEY, site_no TEXT NOT NULL, agency TEXT NOT NULL, name TEXT, lat REAL, lon REAL
);
CREATE TABLE waterbody_gauge (waterbody_id INTEGER, gauge_id INTEGER, PRIMARY KEY(waterbody_id, gauge_id));
CREATE TABLE gauge_reading (
  gauge_id INTEGER, parameter TEXT, value REAL, observed_at TEXT, provisional INTEGER DEFAULT 1,
  PRIMARY KEY(gauge_id, parameter, observed_at)
);
CREATE TABLE forecast_cache (waterbody_id INTEGER, fetched_at TEXT, payload_json TEXT, PRIMARY KEY(waterbody_id, fetched_at));
CREATE TABLE advisory (id INTEGER PRIMARY KEY, kind TEXT, waterbody_id INTEGER, text TEXT, observed_at TEXT, raw_fetch_id INTEGER);
CREATE TABLE generation (                                                  -- cached LLM outputs
  id INTEGER PRIMARY KEY, kind TEXT, key TEXT, text TEXT, model TEXT, prompt_version TEXT, generated_at TEXT,
  UNIQUE(kind, key, prompt_version)
);

-- Journal: client-generated UUIDs, never touched by scrapers
CREATE TABLE trip (
  uuid TEXT PRIMARY KEY, started_at TEXT, ended_at TEXT, waterbody_id INTEGER, lat REAL, lon REAL,
  notes TEXT, conditions_json TEXT, conditions_source TEXT,                -- live|cached
  updated_at TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE catch (
  uuid TEXT PRIMARY KEY, trip_uuid TEXT REFERENCES trip(uuid), species TEXT, count INTEGER,
  length_in REAL, method TEXT, kept INTEGER, photo_path TEXT, updated_at TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE pin (
  uuid TEXT PRIMARY KEY, lat REAL, lon REAL, label TEXT, notes TEXT, updated_at TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
);
```

`conditions_json` (captured automatically on save) holds: weather (observed or forecast), water temp, flow and gage height with timestamps, moon phase, daylight window, and stocking in the previous two weeks for that waterbody. When offline it is filled from the last cached values and `conditions_source` is `cached` with the cache timestamp inside the JSON.

## 4. API surface

Reads are open behind the proxy. All `/api/journal/*`, `/api/sync/*` and `/api/admin/*` require `Authorization: Bearer $HOLDOVER_TOKEN`.

| Method and path | Purpose |
| --- | --- |
| `GET /api/map?zone=willamette&layers=stocking,reports,gauges,advisories` | GeoJSON features for the map layers with freshness and rating properties |
| `GET /api/spots?date=YYYY-MM-DD&fishery=trout|steelhead|warmwater` | Ranked spots with score, factor breakdown, and cached explanation text |
| `GET /api/waterbodies/{id}` | Sheet data: stocking history, latest report items, gauge series, forecast, regs link, your trips there |
| `GET /api/reports?zone=...` | Latest report digests and extracted items |
| `GET /api/day/{waterbody_id}?date=...` | Day-of bundle: conditions, expectations text, packing list |
| `POST /api/sync/push` | Body: arrays of `trip`, `catch`, `pin` with UUIDs. Idempotent upsert, last-write-wins on `updated_at`. |
| `GET /api/sync/pull?since=ISO` | Journal rows changed since a timestamp |
| `GET /api/journal/export?format=json|csv` | Full export |
| `POST /api/journal/photo` | Photo upload, returns path |
| `GET /api/admin/aliases?status=unconfirmed` and `POST /api/admin/aliases/{id}/confirm` | Matching review queue |
| `GET /api/admin/review/items` and accept/reject | Extracted report items needing review |
| `GET /healthz` | Per-source last success, stale flags, LLM reachability |
| `GET /tiles/oregon.pmtiles` | Range-request static file |

## 5. LLM pipeline

Client: OpenAI-compatible chat completions. Use structured output (`response_format` with a JSON schema, or the endpoint's equivalent), then **validate with pydantic regardless**. All jobs are idempotent and write to `generation` or `report_item` with `model` and `prompt_version`. Prompts live in `app/llm/prompts/` with a version string.

Jobs:

1. **Extract** (on new report): split the report by zone, then output items matching:

```json
{
  "items": [{
    "waterbody_raw": "string, as written in the report",
    "species": ["string"],
    "rating": "excellent|good|fair|slow|unknown",
    "note": "string, one sentence, no new facts",
    "source_sentence": "exact sentence from the report"
  }]
}
```

   Reject any item whose `source_sentence` is not a substring of the report text. Items that fail validation or match no confirmed waterbody go to the review queue.
2. **Summarize**: one digest per zone per report, about 120 words. Every sentence must trace to extracted items. Cached.
3. **Explain**: for each ranked spot, a two-line "why this spot, what to expect" written from the scored facts only (stocking recency and count, report rating, flow vs its history, forecast, daylight). Never invent numbers, species, access details or regulations.
4. **Pack list**: template-driven by season, target species, and forecast, with the LLM only polishing phrasing. A template-only version must exist as the fallback.

Fallbacks: if the LLM is unreachable, show raw extracted items and the template pack list, queue the missing generations, and retry on the next run. The UI shows an "as of" time on all generated text and a one-tap link to the original report wording.

Model note: a 7B to 8B instruct model should handle extraction with schema-constrained output. Before committing to a model, run extraction on a handful of saved real reports and review the results.

## 6. Scoring (no LLM)

`score = 100 × Σ(weight × factor)` with factors in `[0,1]`. Defaults below are **tunable starting points, not validated**. Keep weights in config and return the per-factor breakdown from `/api/spots` so the UI can show why.

| Factor | Default weight | Definition |
| --- | --- | --- |
| Stocking recency and size | 0.30 | Higher for stocked this week or last, scaled by count relative to the zone's recent range. Applies to trout. |
| Report rating | 0.25 | Latest accepted report item for the waterbody, mapped from rating |
| Flow suitability | 0.20 | For rivers: current flow relative to that gauge's own recent history. Neutral for lakes. |
| Forecast | 0.15 | Temperature comfort, precipitation, wind |
| Distance | 0.10 | Drive distance or straight-line from `HOME_LAT/LON` |

Later: your own journal results become another factor (for example, weight waterbodies where past trips under similar flows caught fish).

## 7. Frontend

### Design tokens (Fir & Steelhead, default)

Set on `:root[data-theme="fir"]`, with `redband` and `nightbite` as alternates.

```css
:root[data-theme="fir"] {
  --bg:#0F1A17; --surface:#17261F; --line:#25382F;
  --primary:#2F6B52; --accent:#E8735A;
  --text:#E8F0EC; --text-quiet:#9DB3A9;
  --fresh-1:#3DD6B5; --fresh-2:#2A9D8F; --fresh-3:#46635D;   /* stocked this week / last 2 weeks / older */
  --land:#12201B; --water:#0C1613; --river:#2F7C86;
}
:root[data-theme="redband"] {
  --bg:#14202B; --surface:#1B2B3A; --line:#2A3E50; --primary:#1F4E6B; --accent:#E4572E;
  --text:#F2E9DC; --text-quiet:#9FB0BE; --fresh-1:#3DD6B5; --fresh-2:#2A9D8F; --fresh-3:#4A6578;
  --land:#162532; --water:#101A24; --river:#2A9D8F;
}
:root[data-theme="nightbite"] {
  --bg:#0B1014; --surface:#141C22; --line:#22303A; --primary:#3FA7D6; --accent:#F2A541;
  --text:#E6EDF2; --text-quiet:#8FA1AD; --fresh-1:#5CC8F0; --fresh-2:#3FA7D6; --fresh-3:#3A5566;
  --land:#0E151A; --water:#080C0F; --river:#3FA7D6;
}
```

Rules:

- **Accent (coral) is the action colour** (primary buttons, selected day, selected map pin ring) and also the colour for advisories and closures. Do not use red and green to mean good and bad. Stocking freshness is the teal ramp only, so it reads for colour-blind users and in sun.
- Text on accent fills uses `--bg`. Body text is `--text`, secondary is `--text-quiet`. Keep contrast at least 4.5:1 for text.
- Type: **IBM Plex Sans** for UI, **IBM Plex Mono** for numbers (flows, counts, coordinates, times, scores). **Self-host the font files** in the PWA and precache them. Do not load Google Fonts at runtime, it breaks offline.
- Radius 8 px for chips and cards on desktop, 12 px for phone cards, 16 px top corners for the bottom sheet. 1 px `--line` borders. No shadows or gradients.
- Icons: simple 1.8 px stroke line icons, inline SVG, `aria-hidden` unless standalone (then `aria-label`).
- Touch targets at least 44 px. Real `<button>`, `<a href>`, `<input>` with `<label>`. No clickable divs.
- Logo glyph: three stacked riffle waves in `--fresh-1`. Reuse as the app icon.
- A light theme is not yet designed. Build the theming via CSS variables so it can be added.

### Screens (mockups were built at these sizes)

**Desktop, 1440 × 900.** Four regions in a row:

1. 64 px nav rail: logo, Map, Plan, Journal, Gauges, spacer, Settings.
2. 380 px planner panel: wordmark and "Synced HH:MM", zone label, day chips (Today, tomorrow, chosen date selected in accent), fishery chips (Stocked trout, Steelhead and salmon, Warmwater, selected in primary), "N spots ranked" list. Each card: rank, name, two-line reason, freshness dot and stocking count in mono, score in mono (selected card gets `--surface` fill and `--fresh-2` border). Footer: "stocking shown by week, schedule may change".
3. Flexible map: stylized in the mockup, real MapLibre in the app. Layer panel top right (Stocking, Report ratings, Gauges, My pins, Advisories), freshness legend bottom left, "Prepare for offline" button bottom center. Pins coloured by stocking freshness with name chips. The selected pin is larger with an accent ring. Gauges are diamond markers.
4. 340 px waterbody sheet: name, zone and office, 2×2 stat tiles (Forecast, Daylight, Water temp, Moon), stocking history rows (week and legals), "From the weekly report" digest, Pack chips, primary "Log a trip here", link "Official regulations on ODFW".

**Phone, 390 × 844.**

- **Map + spots:** full-bleed map, search pill and layer chips floating on top, "Synced HH:MM" in the search pill, bottom sheet (rounded top, handle) listing ranked spots for the chosen date, 64 px bottom tab bar (Map, Plan, Journal, Gauges).
- **Day-of view:** header with back, name, date and zone, a "Cached" badge when offline. 2×2 conditions tiles, "What to expect" paragraph with a "Read the original report text" link, Pack checklist with real checkboxes, a regulations and advisories notice row, bottom bar with primary "Log a trip here" and secondary "Prepare for offline".
- **Log a trip:** header with close and "Draft", an offline banner ("Saved on this phone, syncs when you have signal"), fields: Where (with "GPS pinned"), Start and End times, Catch (species rows with minus and plus steppers and "Add species"), Lure or method, Notes, a "Conditions captured on save" card with chips and the cache time, primary "Save trip".

All mockup values (forecast, temps, scores, history weeks) were **sample data**. The real data comes from the sources above.

### Map layers

- **Stocking:** waterbody pins coloured by weeks since last stocking (this week, last two weeks, older). Show the week, not a date.
- **Reports:** badges from accepted `report_item` ratings.
- **Gauges:** diamond markers with latest flow and a trend arrow, labeled provisional.
- **Advisories:** accent-coloured markers or zone tint for algae and fire items.
- **My pins and past trips:** from the journal, always rendered from local data so they work offline.

## 8. Offline and PWA

- **App shell and assets:** precache with Workbox (`vite-plugin-pwa`, `generateSW` or `injectManifest`). Include self-hosted fonts. Installable manifest, icons from the logo glyph.
- **API reads:** stale-while-revalidate for map, spots, waterbody sheet and day bundles. Always show an "as of" time next to conditions.
- **Journal writes:** write to IndexedDB (Dexie) first with a client UUID, set `updated_at`, enqueue. A sync worker pushes to `/api/sync/push` when online, with retry and backoff, and pulls changes with `since`. Single user, so last-write-wins on `updated_at`. Soft delete with `deleted`.
- **Auto conditions on save:** use live values if online, otherwise the last cached values, and mark `conditions_source`.
- **Map tiles:** MapLibre with the `pmtiles` protocol. "Prepare for offline" fetches the tiles for the selected region and zoom range into the Cache API, plus conditions and pack list for the chosen day. Scope tiles to the zone and give the user a clear-cache control. Mobile storage quotas are the main constraint, so request persistent storage and handle quota errors gracefully.
- **GPS:** `navigator.geolocation` works offline for pins and trip start.
- Test with airplane mode, not just a throttled network.

## 9. Journal

- Quick log: waterbody or GPS pin, start and end times, species and counts, lure or method, notes, optional photo.
- Auto conditions captured on save (see `conditions_json`).
- Per-waterbody history: trips, catches by species, conditions of best days.
- JSON and CSV export. The database is a single file and the owner owns the data.
- The personal log stays separate from scraped data so a re-scrape or table wipe can never touch it.

## 10. Build phases and acceptance gates

Stop at each gate and report before continuing.

1. **Foundation and stocking map.** Repo, Dockerfile, compose, FastAPI skeleton, SQLite with Alembic migrations, `raw_fetch`, Willamette waterbody seed with aliases, stocking scraper with snapshots, map with the stocking layer, theme tokens, nav shell for desktop and phone.
   - *Done when:* this week's real stocking schedule appears on the map at correct locations, unmatched aliases show in the admin review list, parser tests pass against saved fixtures, `/healthz` reports source status.
2. **Reports and LLM.** Report scraper, schema-validated extraction, zone digests, review queue, `generation` cache.
   - *Done when:* saved past reports replay into reviewed items and digests, items cite a verbatim source sentence, and killing the LLM host leaves the UI working with raw items.
3. **Conditions.** USGS gauges linked to waterbodies, NWS forecast, sun and moon, advisories, the waterbody sheet and day-of view.
   - *Done when:* a waterbody sheet shows flow, weather and latest report notes together with "as of" times, and a stale source shows a stale badge.
4. **Journal and offline.** Trip and catch logging, auto conditions, IndexedDB sync queue, PMTiles caching, "Prepare for offline", service worker.
   - *Done when:* a trip logged in airplane mode syncs correctly afterwards, the app shell and cached map load with no network, and a duplicate push does not create duplicates.
5. **Planner.** Scoring function with factor breakdown, explanations, pack list, date and fishery filters.
   - *Done when:* ranking for a chosen date is explainable from the breakdown, and the LLM text never contains a number or species not in the input.
6. **Later.** Coast and marine layers (tides), statewide coverage, light theme, optional Postgres/PostGIS migration, journal-informed scoring.

## 11. Testing

- `tests/fixtures/` holds real saved HTML and JSON from every source. Parsers are tested against them, and a fixture refresh is part of fixing any scraper break.
- LLM extraction: golden-file tests on saved reports, checked by schema validation and the substring rule for `source_sentence`.
- Scoring: unit tests on factor functions and edge cases (no stocking, no gauge, missing forecast).
- Sync: idempotency and conflict tests (same UUID pushed twice, older `updated_at` loses).
- E2E (Playwright): airplane-mode journal flow, install and offline reload.
- Accessibility spot checks: keyboard navigation, contrast, 44 px targets.

## 12. Constraints and safety

- Never present regulations, limits, seasons or closures as authoritative. Link to ODFW.
- Label USGS values as provisional. Label stocking as a week, with a "schedule may change" note.
- Keep original source wording one tap away from any generated summary.
- Be a polite client: identifying User-Agent, low poll rates, caching, backoff.
- Do not store secrets in the repo. Token and LLM settings come from environment variables.
- Single-user assumption: one bearer token, last-write-wins sync. If others will share the app, revisit auth and sync before building.

## 13. Open items the agent must resolve or flag

1. Terms of use and robots rules for myodfw.com, OHA, ODF, NWS. Record in `docs/sources.md` before scraping.
2. Confirm the current USGS endpoint (legacy `waterservices.usgs.gov` vs the new Water Data APIs) and OWRD access.
3. Inspect the OHA and ODF pages and the real Recreation Report page structure, then write parsers from saved fixtures.
4. Determine the Willamette zone filter value on the stocking schedule page.
5. Get the owner's starred waterbodies and gauges for the seed, and the owner's LLM model and hardware.
6. Confirm whether anyone besides the owner will use the app (affects auth and sync).
7. Source an Oregon PMTiles extract and document how it was produced and its license.

## 14. Reference artifacts

- **Design doc:** "Oregon Fishing PWA, Design" (goals, architecture, data model, LLM pipeline, offline, risks).
- **Mockups:** the "Holdover Mockups" canvas with desktop plan and map, phone map, phone day-of, phone log-a-trip, and theme plates. The screen descriptions above are sufficient to build from without opening it.
