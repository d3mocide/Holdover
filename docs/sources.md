# Data sources: terms and robots review

Record the outcome here **before** first scraping a source. Status as of 2026-10-17.

| Source | robots.txt | Terms of use | Status |
| --- | --- | --- | --- |
| myodfw.com stocking schedule | Read. `User-agent: *` disallows only admin, search, user and Drupal internals. `/fishing/species/trout/stocking-schedule` is allowed. No `Crawl-delay`. | **Not yet read.** Owner to confirm before enabling the scheduler in production. | Daily poll, one request per page with a 2 s gap (about 5 requests a day). |
| myodfw.com Recreation Report | Same robots file | Not yet read | Phase 2 |
| USGS waterservices | Not checked | Public domain, keyless; endpoint currency not verified | Phase 3 |
| NWS api.weather.gov | Not checked | Free, requires identifying User-Agent | Phase 3 |
| OHA algae advisories | Not checked | Not read | Phase 3 |
| ODF wildfire | Not checked | Not read | Phase 3 |
| ODFW ArcGIS (zone polygons) | Not checked | Not read | Later |

## Stocking schedule: observed facts (2026-10-17)

- Willamette zone filter is `field_zone_value=6` (zones: 1 Central, 2 Northeast, 3 Northwest, 4 Southeast, 5 Southwest, 6 Willamette).
- Date filters are plain query params: `field_planned_stocking_date_value=YYYY-MM-DD` and `field_planned_stocking_date_end_value=YYYY-MM-DD`. The bracketed `[date]` form in the original notes is redirected to this form.
- Results are paged 50 rows at a time with `&page=N` (zero-based).
- The week column reads `Oct. 12, 2026 - Oct. 16, 2026` on some rows and `Sep. 14, 2026-Sep. 18, 2026` on others. The parser reads only the start date, which is a Monday.
- Some rows have a blank office (`Willamette /`).

## Known problem: Python HTTP client gets 403

From this build environment, `curl` fetched myodfw.com normally while `httpx` (HTTP/1.1 and HTTP/2, any User-Agent) received `403 Forbidden`. The cause is not confirmed (likely client fingerprinting by the site's edge, possibly the build sandbox's proxy). No workaround was attempted. Fixtures were captured with `curl`. **Check from the real deployment network.** If the 403 persists there, `/healthz` will show the source as stale with `HTTP 403`; the options are asking ODFW whether they provide a feed, or a curl-based fetcher, which is the owner's call.
