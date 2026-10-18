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
| 4 | **ODF fire "regulated use" zones** | Yes, ArcGIS REST | Yes, 72 polygons; **meaning of the codes unknown** | Low to medium, ODF-protected lands only | Small once decoded | Fourth; needs ODF to explain the codes |
| 5 | **OWRD gauges** | Station list yes; **readings: no documented API** | Station list only | Low for rivers: USGS already covers most; OWRD's own pages redirect to USGS | Medium to high (scraping) | Skip, or ask OWRD |
| 6 | **ODFW fish-district polygons** | Yes, ArcGIS REST | Yes (on ArcGIS Online; the handoff's URL is blocked) | Low: districts are **not** the stocking zones | Small | Low |
| 7 | **Tides and coast** (NOAA CO-OPS) | Yes, documented | Yes (South Beach) | High for Phase 12, none for the current zone | Medium | Phase 12 |

---

## 1. USGS Water Data API: do this first (deadline)

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

- **Endpoint (verified):** `services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0`,
  a standard ArcGIS REST service with GeoJSON output. `where=attr_POOState='US-OR'` returned **16 perimeters**, with
  name, acres, percent contained, cause and a current-date stamp. The layer was edited today.
- **Caveats:** the layer holds the whole season including fires that are 100% contained, so filter to still-active fires.
  A perimeter is **not** a closure: show "active fire near here" and send people to InciWeb, ODF and the forest's own
  page. Never state that an area is closed. Service metadata carries no licence text (NIFC publishes it as open data;
  confirm on their open-data page).
- **Value:** medium (safety, smoke, access). **Effort:** small to medium: fetch, point-in-radius check per waterbody, a
  warning chip on the sheet and a map layer, tests.

## 4. ODF fire "regulated use" zones

- **Endpoint (verified):** `gis.odf.oregon.gov/ags1/rest/services/WebMercator/RegulatedUse/MapServer/0`, described as
  regulated-use boundaries for "ODF protected lands", currently **72 polygons**.
- **Problem:** the only attribute is a short code (`KR`, `RR-3`, `SW-1`). Without ODF's key I cannot say what each code
  means, whether the layer is current today, or which activities are restricted. **Do not ship this without ODF
  explaining it**; restating restrictions wrongly would break the project's first rule.
- **Coverage:** ODF-protected private and state lands only. It does not cover national forests, BLM land or parks,
  which is where much of the fishing is. There is no single API for campfire restrictions across agencies.
- **Value:** low to medium. **Effort:** small once decoded. Ask ODF (gis.info or the Regulated Use page owner).

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

## 7. Tides and coast (Phase 12)

NOAA CO-OPS has a documented, free JSON API (`api.tidesandcurrents.noaa.gov/api/prod/datagetter`). **Verified** with South Beach,
Oregon (water level, 6-minute data). It requires an `application` name parameter, has request-length limits and a throttling policy, and
offers predictions as well as observations. NWS marine forecasts and NDBC buoys would complete a coast layer. This is a
whole phase (new fisheries, species, regulations to link to, a different map), not a feature.

## Not probed

Fish passage counts (Willamette Falls, Bonneville) for steelhead and salmon timing; US Forest Service alerts and closure
orders; TripCheck road conditions (needs a key). Listed so they are not forgotten; none are verified.

## Recommended order

1. **USGS migration** (deadline; small).
2. **Reservoir levels** (largest user benefit; first read the Corps' terms and ask Portland District about the service).
3. **Wildfire perimeters** (clear API, clear safety value).
4. Ask ODF what the regulated-use codes mean; decide then.
5. Leave OWRD and the district polygons unless a concrete need appears.

Each new source also needs its terms read and recorded in [sources.md](sources.md), polite polling (identifying User-Agent,
low rates, hash skip where it helps), a stale badge, saved fixtures, tests and a credit in Settings. The map and sheet
should link to the agency for anything restriction-like and never restate it.
