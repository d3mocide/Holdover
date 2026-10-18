# Data source options (researched 2026-10-18)

For each unbuilt data item in the roadmap: is there an API, does it work, what does it cost to build, and is it worth it.
Priorities feed [ROADMAP.md](ROADMAP.md) (Phases 9, 11 and 12). Nothing here is built yet.

**How this was checked.** Web searches for each source, then **direct requests from this machine** to every endpoint
(a handful per source, with Holdover's identifying User-Agent). "Verified" means the endpoint answered with real data
today. "Not verified" means I only have a search result or a page's claim. Terms are summarised from what each
publisher states, not legal advice, and per [AGENTS.md](../AGENTS.md) a new source needs the owner's go-ahead and a
[sources.md](sources.md) entry before it is built.

## Summary

| # | Item | API? | Verified today | Value | Effort | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **USGS Water Data API** (replaces the legacy endpoint the app uses now) | Yes, documented (OGC API) | Yes, all 16 gauges, same values | **Required**: the app's flow data stops in early 2027 | Small to medium | **Do first** |
| 2 | **Reservoir levels** (Army Corps, 10 Willamette reservoirs) | Yes, JSON, **undocumented** | Yes, all 10 | **High**: drawdowns change access and fishing | Medium | **Second**, after reading the Corps' terms |
| 3 | **Wildfire perimeters** (NIFC WFIGS) | Yes, ArcGIS REST | Yes, 16 Oregon perimeters | Medium (safety, smoke, "check closures") | Small to medium | Third |
| 4 | **ODF fire danger by regulated-use area** (found in Vertex) | Yes, ArcGIS REST | Yes, 63 zones, level 1 Low to 4 Extreme; **codes now decoded** | Medium, ODF-protected lands only | Small | Third, with wildfire |
| 5 | **OWRD gauges** | Station list yes; **readings: no documented API** | Station list only | Low for rivers: USGS already covers most; OWRD's own pages redirect to USGS | Medium to high (scraping) | Skip, or ask OWRD |
| 6 | **ODFW fish-district polygons** | Yes, ArcGIS REST | Yes (on ArcGIS Online; the handoff's URL is blocked) | Low: districts are **not** the stocking zones | Small | Low |
| 7 | **River flood status and forecasts** (NOAA NWPS, found in Vertex) | Yes, keyless bbox API | Yes, 165 gauges in the Willamette area | Medium: official flood categories and forecast crests | Small to medium | After the Corps levels |
| 8 | **Satellite fire hotspots** (NASA FIRMS, found in Vertex) | Yes, needs a free MAP_KEY | Not probed (needs your key) | Medium: earliest fire warning | Small | When you have a key |
| 9 | **Tides and coast** (NOAA CO-OPS) | Yes, documented | Yes (South Beach) | High for Phase 12, none for the current zone | Medium | Phase 12 |

---

## 1. USGS Water Data API: do this first (deadline)

**Status: done 2026-10-18** (see BUILD_LOG). Kept below as the research record.

**Why it is urgent.** Holdover reads `waterservices.usgs.gov/nwis/iv`. USGS's own notice (January 2026) says
"WaterServices APIs will be decommissioned early 2027" and that a campaign running November 2026 through February 2027
"will retire all remaining NWISWeb pages and WaterServices". A government bulletin gives February 22, 2027, which I could
not confirm on a USGS page, and USGS says the retirement may include intentional degradation and blackouts beforehand.
The legacy endpoint answers today.

**The replacement, verified:** `https://api.waterdata.usgs.gov/ogcapi/v1/` (the October 2026 USGS post names `/v1/`; `/v0/` also
answers, so use `v1`).

- **Current values:** `collections/latest-continuous/items?monitoring_location_id=USGS-14166000,USGS-14174000,...&parameter_code=00060,00065,00010`.
  One request returned **all 16 gauges and 47 readings** (34 KB). Same numbers as the legacy endpoint (Dexter
  1,240 cfs). Fields: `monitoring_location_id`, `parameter_code`, `value`, `unit_of_measure`, `time`,
  `approval_status` ("Provisional"), `qualifier`, `last_modified`. Water temperature is in degC.
- **History (for flow versus median, and the backfill):** `collections/continuous/items?...&time=START/END`. Verified for one
  gauge; it paginates at 1,000 points, so a 7-day backfill of 16 gauges is a short loop.
- **Keys and limits:** no key was needed. USGS's docs say an API key gives "higher rate limits" (signup is on their
  "Using API Keys" page; limits were not stated on the pages I could read). One request every 30 minutes is tiny either way.
- **Terms:** USGS data is public domain; credit requested (done in Settings).

**Build plan:** swap the adapter inside `app/sources/usgs.py` (the only file that knows the URL shape, by design),
parse GeoJSON instead of the legacy `timeSeries` JSON, keep `gauge_reading` and everything downstream unchanged, new
fixtures from the live response, tests for parse and unit handling, run both for a while and compare, then remove the
legacy path. Also record the migration in sources.md. Roughly a day of work, low risk.

## 2. Reservoir levels (Army Corps): the best new feature

**Status: built 2026-10-18** (`app/sources/corps.py`). Findings while building: `timezone=GMT` returns UTC (avoids the November
DST ambiguity); `startdate=` and `enddate=` (not `start_date`) select a historical window, so the same date in earlier
years costs a small request instead of 400 days of 15-minute data (4.7 MB per reservoir); the site has no terms page.

**What it is.** The Corps' Portland District runs the big Willamette reservoirs, and their pool levels determine boat-ramp
access, fish passage drawdowns and where the water is. The Corps publishes the elevations.

**Verified.** Their water-control site serves JSON from
`https://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson?timezone=PST8PDT&query=["CODE.Elev-Forebay.Inst.0.0.Best"]&backward=1d`.
I found it by reading the Corps' own query tool's JavaScript. It returned current forebay elevations (feet) for:

| Code | Reservoir | Elevation 2026-10-18 05:30 |
| --- | --- | --- |
| DET | Detroit | 1,491.6 |
| GPR | Green Peter | 864.7 |
| LOP / DEX | Lookout Point / Dexter | 808.1 / 692.6 |
| FOS | Foster | 613.4 |
| COT | Cottage Grove | 757.9 |
| DOR | Dorena | 793.3 |
| FAL | Fall Creek | 767.3 |
| BLU | Blue River | 1,229.0 |
| HCR | Hills Creek | 1,450.3 |

Each project also reports tailwater elevation and outflow, at 15-minute intervals. The parameter ID pattern is `CODE.Elev-Forebay.Inst.0.0.Best`. Labels come from each project's own name in the service's metadata (not from memory: I first mislabelled `CGR`, which is **Cougar Dam**, as Cottage Grove). The returned dam coordinates match the seed's positions for these waters. Cougar (`CGR`, 1,533.1 ft) and Fern Ridge (`FRN`, 366.7 ft) are also available but are not in the seed.

**Cautions.**
- **Undocumented.** No public API documentation turned up; it is the service behind their own tool, so it could change.
  Ask the Portland District (or check their water-management pages) before depending on it.
- **Certificate.** The server sends an incomplete certificate chain (the DigiCert intermediate is missing), so
  `curl` and Python fail verification here although browsers work. Fix: bundle that public intermediate certificate for
  this one host. Do not disable verification.
- **Meaning.** An elevation alone says little. Two honest options: show elevation with its 24-hour and 7-day change, and
  compare with the **same date in earlier years from the Corps' own history** (the same "versus its own median" idea the
  planner uses for flow), which needs no outside numbers. Do not hard-code "full pool" heights from memory.
- **Terms not read yet.** Federal data, marked provisional by the Corps; read their disclaimer before enabling.

**Value.** High: it is exactly the information anglers ask about ("is Green Peter drawn down?"), only available today on
a Corps web page. **Effort:** medium (new adapter, certificate bundle, history comparison, a card on the sheet, tests).

## 3. Wildfire perimeters (NIFC)

**Status: built 2026-10-18** (`app/sources/nifc.py`), together with section 4 as the fire card. The *Current* layer filtered to
`attr_POOState='US-OR'` returns 16 perimeters; the card keeps wildfires (not prescribed burns) under 100% contained and updated
within 30 days (4 on 2026-10-18) and shows those within 50 km. Perimeters near the Washington border are not included.

- **Endpoint (verified):** `services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0`,
  a standard ArcGIS REST service with GeoJSON output. `where=attr_POOState='US-OR'` returned **16 perimeters**, with
  name, acres, percent contained, cause and a current-date stamp. The layer was edited today.
- **Caveats:** the layer holds the whole season including fires that are 100% contained, so filter to still-active fires.
  A perimeter is **not** a closure: show "active fire near here" and send people to InciWeb, ODF and the forest's own
  page. Never state that an area is closed. Service metadata carries no licence text (NIFC publishes it as open data;
  confirm on their open-data page).
- **Value:** medium (safety, smoke, access). **Effort:** small to medium: fetch, point-in-radius check per waterbody, a
  warning chip on the sheet and a map layer, tests.

## 4. ODF fire danger by regulated-use area

**Status: built 2026-10-18** (`app/sources/odf_fire.py`). The area codes have no names in either layer, so the card shows the
code and links to ODF's map. 28 of 58 seeded waterbodies fall inside a zone; the rest get an honest "outside ODF-protected
lands" line.

**Update 2026-10-18, thanks to Vertex.** My first probe found a layer of 72 "regulated use" polygons with only short area
codes and no meaning. Vertex's ODF poller uses a different ODF service that carries the level:
`gis.odf.oregon.gov/odfags/rest/services/Hosted/Fire_Danger_Level_View/FeatureServer/0` (the one behind ODF's own
fire-restrictions map). **Verified live:** 63 protection zones, fields `regusearea` (the same codes, e.g. `SW-1`, `RR-3`,
`KR`), `district`, `firedanger` (1 Low, 2 Moderate, 3 High, 4 Extreme) and `pendingchangedatetime`. Today: 30 Low,
30 Moderate, 3 High. The codes in the two ODF layers match, so the earlier mystery is solved.

- **Use:** point-in-polygon for each waterbody: "ODF fire danger here: Moderate (zone SW-1)", linking to ODF's page for what
  the level means. Never restate which activities are restricted.
- **Coverage:** ODF-protected lands only. National forests, BLM land and parks are not in it. There is no single feed for
  campfire restrictions across agencies.
- **Value:** medium. **Effort:** small (about 140 KB of simplified polygons; Vertex requests them with server-side
  simplification, `maxAllowableOffset`). Terms: the layer's copyright field says "Oregon Department of Forestry"; no licence text.

## 5. OWRD gauges: probably skip

- **Station list (verified):** a public ArcGIS layer with 662 active stations (name, number, lat/lon, status).
  OWRD says it operates "more than 200" gages, "more than 160" near real-time, reporting hourly.
- **Readings:** no documented API. The near-real-time site (`apps.wrd.state.or.us/apps/sw/hydro_near_real_time/`) is a
  web app; the page offers "download daily and instantaneous data" but names no format, and for stations that overlap
  with USGS its station page **redirects to USGS**. I did not find OWRD among the new USGS API's agency codes.
- **Value for this app:** low. The rivers that matter in the Willamette zone are already USGS gauges. What OWRD adds is
  its own sites, which would mean scraping HTML. If wanted, ask the Surface Water Hydrology Section
  (`WRD_DL_hydro_on_web_support@water.oregon.gov`) whether a feed exists.

## 6. ODFW fish-district polygons: low value

- **Endpoint (verified):** the handoff's `nrimp.dfw.state.or.us` URL now answers **503 "request rejected"** (a firewall), but the
  same layer is live on ArcGIS Online: `services.arcgis.com/uUvqNMGPm7axC2dD/ArcGIS/rest/services/FishBioDistrictst/FeatureServer/0`
  (18 districts, WGS84, 8.7 MB as GeoJSON, so it would need simplifying). Copyright text: "ODFW".
- **It is not the stocking zones.** The stocking schedule uses six zones (Central, Northeast, Northwest, Southeast,
  Southwest, Willamette). These 18 are fish-biologist districts (Upper Willamette, Mid Willamette, NWWD-Cascade Unit, ...).
  They cannot draw "the Willamette zone"; at best they label a waterbody with its district.
- **Privacy:** each district's attributes include the biologist's name and phone number. Use only name and region; do not
  republish staff contact details.
- **Value:** low. **Effort:** small.

### 6b. ODFW Angling Zones (the Sport Fishing Regulations zones), added 2026-10-18 at the owner's suggestion

- **What it is:** the ArcGIS Online item `2c4418d3424a41f3aa9d46440e02c3b8` ("AnglingZones", owner ODFW_AGO, public, modified
  2023-12) describes "the zones that are found in the Oregon Sport Fishing Regulations", served as a map service at
  `nrimp.dfw.state.or.us/arcgis/rest/services/ODFW_Regs/AnglingZones/MapServer`. **Licence note on the item: "None, but please credit
  ODFW in the use of these data."** This is the regulation-zone map, so (unlike 6) it is the right unit for "which section of the
  regulations applies here".
- **Not reachable from here:** that server answers **503 "The requested URL was rejected"** (an F5 firewall) to my client, even for
  `/robots.txt`, the same behaviour as item 6. No hosted ArcGIS Online copy was found (searched the ODFW org). I did not try to
  get around the firewall. It may well work from a browser, so one option is for the owner to export the (few, rarely changing)
  polygons once from the item page and commit them as a static file, with the ODFW credit.
- **Use if built:** label each waterbody with its regulation zone and link to the matching ODFW regulations page (rule 1: link, never
  restate), and give statewide coverage a zone list that matches how anglers think. **Value:** medium. **Effort:** small (static
  GeoJSON plus point-in-polygon, `app/geo.py` already has it).
- **Not verified:** the layer's field names, zone count and polygon size.

### 6c. oregontails.org Oregon Fishing Guide (reference only)

A third-party blog page (`oregontails.org/oregon-fishing-map-guide/`) with a nine-zone map filterable by species, a species guide
and per-zone cards. Read 2026-10-18; its robots.txt blocks only WordPress admin and shop paths. **Not a source to ingest:** it is
a copyrighted editorial guide, it restates bag limits and seasons (which Holdover never does, rule 1, and which it warns can
change in-season), and it is not authoritative. Worth borrowing as *ideas*, written our own way: a "what's biting where" species
filter on the map, and per-zone summary cards.

## 7. River flood status and forecasts (NOAA NWPS), found in Vertex

**Status: built 2026-10-18** (`app/sources/nwps.py`). The response has no USGS site numbers, so the 14 mapped pairs were matched by name
and position (all within 120 m) and written down in `LIDS`. Gauges with no flood stages defined (most of them) show nothing.

`https://api.water.noaa.gov/nwps/v1/gauges?bbox.xmin=..&bbox.ymin=..&bbox.xmax=..&bbox.ymax=..&srid=EPSG_4326`, keyless.
**Verified:** 165 gauges in the Willamette area, each with observed stage and flow and an **official flood category**
(`no_flooding`, `action`, `minor`, `moderate`, `major`, or `not_defined`) plus forecast crest. Its Willamette at Albany
reading (4.52 kcfs) agrees with USGS (4,520 cfs). Cautions: 91 of the 165 have no defined flood stages, 9 are not current,
flow arrives in `kcfs` and `-999` means "no value". **Use:** a "river status" line for linked gauges ("Willamette at
Salem: action stage, forecast to crest Tuesday"), as a safety cue for blown-out water. It complements USGS (water
temperature and more gauges) and does not replace it. Vertex's code for this is a good reference. Effort: small to medium
(map NWPS ids `lid` to the seed gauges).

## 8. Satellite fire hotspots (NASA FIRMS), found in Vertex

VIIRS thermal detections show fires hours before incident reports. The API (`firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/{source}/{bbox}/{days}`)
needs a **free MAP_KEY** (signup at the FIRMS site), which only you can obtain, so I have not probed it. Vertex runs it
behind an optional key (idle without one) and takes care not to log URLs, since the key is in the path. Same pattern here
if you want it. Value: medium; effort small once a key exists.

## 9. Tides and coast (Phase 12)

NOAA CO-OPS has a documented, free JSON API (`api.tidesandcurrents.noaa.gov/api/prod/datagetter`). **Verified** with South Beach,
Oregon (water level, 6-minute data). It requires an `application` name parameter, has request-length limits and a throttling policy, and
offers predictions as well as observations. NWS marine forecasts and NDBC buoys would complete a coast layer. This is a
whole phase (new fisheries, species, regulations to link to, a different map), not a feature.

## Not probed

Fish passage counts (Willamette Falls, Bonneville) for steelhead and salmon timing; US Forest Service alerts and closure
orders; TripCheck road conditions (needs a key). Listed so they are not forgotten; none are verified.

## Recommended order

1. ~~USGS migration~~ **done 2026-10-18**.
2. **Reservoir levels** (largest user benefit; the Corps' terms still need reading, and Portland District could be asked about the service).
3. **Fire together**: ODF fire danger by area (verified, decoded), NIFC active perimeters, and FIRMS hotspots if you get a key. One fire card on the sheet and a map layer.
4. **River flood status** from NWPS.
5. Leave OWRD and the district polygons unless a concrete need appears.

Owner approved building from government sources on 2026-10-18 (non-commercial use). The reuse model is Vertex, the owner's own project (GPL-3.0, same license), for endpoints and parsing patterns; each source still gets its terms recorded in sources.md.

Each new source also needs its terms read and recorded in [sources.md](sources.md), polite polling (identifying User-Agent,
low rates, hash skip where it helps), a stale badge, saved fixtures, tests and a credit in Settings. The map and sheet
should link to the agency for anything restriction-like and never restate it.
