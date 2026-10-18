# Data sources: terms and robots review

Record the outcome here **before** first scraping a source. Status as of 2026-10-17.

| Source | robots.txt | Terms of use | Status |
| --- | --- | --- | --- |
| myodfw.com stocking schedule | Read. `User-agent: *` disallows only admin, search, user and Drupal internals. `/fishing/species/trout/stocking-schedule` is allowed. No `Crawl-delay`. | **Not yet read.** Owner to confirm before enabling the scheduler in production. | Daily poll, one request per page with a 2 s gap (about 5 requests a day). |
| myodfw.com Recreation Report | Same robots file | Not yet read | Phase 2 |
| USGS waterservices (IV) | Not checked | Public domain, keyless. Legacy `waterservices.usgs.gov/nwis/iv` verified live 2026-10-17; USGS is migrating, so it is isolated in `app/sources/usgs.py`. All values provisional. | Live, every 30 min |
| NWS api.weather.gov | Not checked | Free, requires identifying User-Agent. points/forecast/forecastHourly shapes verified 2026-10-17. | Live, hourly for starred waterbodies, plus on demand in the day view |
| OHA algae advisories | oregon.gov robots read (only layout/admin paths blocked) | Not read | The OHA web page builds its table client-side, so the app reads the public ArcGIS feature service behind OHA's own advisory map (`HABs_Advisories_(Points)`). It is not a documented API. Daily. |
| ODF wildfire | Not checked | Not read | **Not implemented.** No feed inspected. |
| ODFW ArcGIS (zone polygons) | Not checked | Not read | Later |

## Stocking schedule: observed facts (2026-10-17)

- Willamette zone filter is `field_zone_value=6` (zones: 1 Central, 2 Northeast, 3 Northwest, 4 Southeast, 5 Southwest, 6 Willamette).
- Date filters are plain query params: `field_planned_stocking_date_value=YYYY-MM-DD` and `field_planned_stocking_date_end_value=YYYY-MM-DD`. The bracketed `[date]` form in the original notes is redirected to this form.
- Results are paged 50 rows at a time with `&page=N` (zero-based).
- The week column reads `Oct. 12, 2026 - Oct. 16, 2026` on some rows and `Sep. 14, 2026-Sep. 18, 2026` on others. The parser reads only the start date, which is a Monday.
- Some rows have a blank office (`Willamette /`).

## Resolved: Python HTTP client got 403 in the build sandbox

From this build environment, `curl` fetched myodfw.com normally while `httpx` (HTTP/1.1 and HTTP/2, any User-Agent) received `403 Forbidden`. The cause is not confirmed (likely client fingerprinting by the site's edge, possibly the build sandbox's proxy). No workaround was attempted. Fixtures were captured with `curl`. **Resolved 2026-10-17:** from a home network, httpx fetched all 11 stocking pages normally (500 rows) with an honest `Holdover/0.1 (+repo URL)` User-Agent, so the 403 was the build sandbox. The original note follows. **Still check from the real server when you deploy.** If the 403 persists there, `/healthz` will show the source as stale with `HTTP 403`; the options are asking ODFW whether they provide a feed, or a curl-based fetcher, which is the owner's call.

## Python HTTP client status by host (2026-10-17)

httpx got 200 from waterservices.usgs.gov, api.weather.gov and services.arcgis.com. Only myodfw.com returned 403 to Python clients, so the problem is specific to that site (or its edge rules).

## Gauge and advisory notes

- Gauge site numbers, names and coordinates in `app/seed.py` were checked against the live USGS service. Which gauge represents which waterbody (`GAUGE_LINKS`) is my judgement: review it.
- OHA waterbody names are matched to the seed with the same exact-after-generic-words rule as report items (`Detroit Lake` matches `Detroit Reservoir`). Unmatched OHA waters get no marker; they are not guessed.
- `starred` waterbodies get hourly NWS refreshes. None are starred yet (`POST /api/admin/waterbodies/{id}/star`).
