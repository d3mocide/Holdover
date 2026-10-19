# Data sources: terms and robots review

Record the outcome here **before** first scraping a source. Reviewed 2026-10-18 by fetching each source's own policy
pages. **This is a summary of what the sources publish, not legal advice**: the decisions marked "Owner" are yours.

| Source | robots.txt | Terms and policy (what they say) | Status |
| --- | --- | --- | --- |
| myodfw.com stocking schedule and Recreation Report | Read. `User-agent: *` disallows only admin, search, user and Drupal internals; the stocking schedule is allowed; no `Crawl-delay` | **No terms-of-use page found.** The site footer links only Accessibility and shows "© Copyright 2026 Oregon Department of Fish & Wildlife". The stocking page states nothing about reuse or automated access. See "ODFW and the state terms" below | **Once a week, on Friday**, one request per page with a 2 s gap: about 19 requests for the three enabled zones (Willamette 11 pages, Central 4, Northwest 4; each further zone is 2 to 4 more pages). The weekly report: Friday morning, and Saturday and Monday only if no new issue has arrived (skipped when the newest stored issue is under 5 days old). A zone enabled later is fetched once at startup. **Owner: decide on contacting ODFW** |
| OHA algae advisories (Oregon Health Authority) | oregon.gov robots read (only layout and admin paths blocked) | Read from OHA's public ArcGIS layer, which carries **no copyright or licence text** in its metadata. State terms below | Daily. **Owner: consider asking OHA** |
| USGS waterservices (IV) | Not checked | **Public domain** ("USGS-authored or produced data and information are considered to be in the U.S. Public Domain"). USGS asks for credit ("U.S. Geological Survey"). Values are provisional (the app says so) | Live, every 30 min, from the **Water Data API** (`api.waterdata.usgs.gov/ogcapi/v1`) since 2026-10-18. The legacy endpoint (retiring early 2027) remains only as a fallback (`USGS_API=legacy`) to be deleted. Credit in Settings |
| NWS api.weather.gov | Not checked | **Open data, free for any purpose.** A User-Agent identifying the app is required (sent on every request), with a contact so they can reach you. Rate limit is not public; if exceeded, retry after about 5 seconds. Cache-friendly; re-check `/points` periodically because grid cells can change | Live, hourly for favorites plus one stocked waterbody per ~0.25 degree cell; `/points` is resolved on every refresh, so grid changes are picked up |
| Protomaps daily builds (basemap) | n/a | **ODbL "Produced Work": OpenStreetMap attribution is required.** No usage limits stated; hotlinking the downloads is discouraged, region extracts with the `pmtiles` CLI are supported | One extract downloaded and served locally (no hotlinking). **Attribution was missing from the map until 2026-10-18; fixed and tested** |
| Army Corps NWD water control (`www.nwd-wc.usace.army.mil`) | Not checked | **No terms or disclaimer page found** on the site (home, `/dd/`, `/disclaimer.html` read; nothing). US federal works are generally public domain, but that is the general rule, not a statement from this site. The data is the service behind the Corps' own query page and is **undocumented**. Elevations are unverified, so Holdover labels them so | Hourly, one request (about 20 KB), plus up to three small history requests a day until same-date history for three earlier years is stored. The server omits its DigiCert intermediate certificate, so that public certificate is bundled in `app/certs` and added for this host only; verification is never disabled. Credit in Settings. **Owner: consider asking the Portland District whether the service may be used** |
| NOAA NWPS gauges API (`api.water.noaa.gov/nwps`) | Not checked | NOAA/NWS data, open to the public with no key and no terms page found for the API. The same open-data stance as `api.weather.gov` applies, but this API's own policy was not read | Hourly, one request (about 190 KB) with the identifying User-Agent. Credit in Settings. Only NOAA's own category and stage are shown, with a link to NWPS |
| ODF fire danger (public ArcGIS layer behind ODF's fire-restrictions map) | Not checked | The layer's metadata carries **no licence or terms text** (its description reads only "Fire_Restriction"). The State of Oregon's general terms are summarised under ODFW above (as-is, no warranty). ODF covers lands it protects; a waterbody outside every zone gets no level | Every 6 hours, one request (about 140 KB). Credit in Settings; links to ODF's own restrictions map. The app shows the danger level only and never restates rules. **Owner: consider asking ODF** |
| NIFC WFIGS current interagency perimeters (public ArcGIS layer) | Not checked | The item metadata carries a **liability disclaimer** ("shall not be held liable for improper or incorrect use of the data"; not legal documents) and credits the contributing agencies (Interior Office of Wildland Fire, USDA Forest Service, National Park Service). Federal data | Hourly, one request (about 270 KB, Oregon only). Credit in Settings. Wording: perimeters can lag, a nearby fire is not a closure |
| ODFW ArcGIS (zone polygons) | Not checked | Not read | Not implemented |
| Fonts (IBM Plex, Noto Sans) | n/a | SIL Open Font License; notice kept in `web/public/fonts/NOTICE.txt` | Bundled |

## Review findings, 2026-10-18

### ODFW and the state terms

- **No ODFW terms page exists that I could find.** The homepage, the footer and the stocking page were read. The
  only policy-like text is the copyright line and the data disclaimers on the stocking page: the schedule "is
  subject to change without notice", "shows the WEEK a waterbody will be stocked, not the exact date", the Monday
  date "indicate[s] the START of the week", some waterbodies "may not be stocked as scheduled because of poor water
  conditions", and "only 2 years of stocking history is available". Holdover already repeats the week-not-day
  and may-change messages.
- The State of Oregon publishes site-wide [Terms & Conditions](https://www.oregon.gov/pages/terms-and-conditions.aspx)
  for oregon.gov. They say content is provided "as is" with no warranty of accuracy, individual agencies may have
  their own separate terms, and visitors agree to indemnify the state for losses from their use of site content.
  They **do not mention robots, crawlers, scraping or automated access**, and say nothing about reuse of data.
  It is not stated whether they govern myodfw.com, which is a different domain.
- Contact listed on the stocking page: `odfw.info@odfw.oregon.gov`, (503) 947-6000. No contact is listed for data requests.
- **What Holdover does:** about five requests a day for stocking plus a few for the report, an identifying
  User-Agent with a link, hash comparison to skip unchanged pages, backoff on errors, and robots-compliant paths. It shows
  facts (counts, weeks) with attribution and a link to ODFW's own pages.
- **Quoted report text.** Holdover shows short verbatim sentences from the Recreation Report (it requires them, so
  every generated claim can be traced) and links to the original. The report carries ODFW's copyright. Short,
  attributed quotation is common practice but it is **your call** whether to keep it.
- **Suggested (Owner):** email ODFW once, say it is a small personal and household app that reads the public stocking
  schedule and report a few times a day, and ask whether they have a feed or any objection. Keep the polling
  rates as they are until you hear back. A written answer belongs in this file.

### OHA

The data comes from OHA's public ArcGIS feature layer, not the OHA web page. The layer has no licence text and is
not a documented API (it may change). Holdover credits OHA, says only some waters are monitored, and links to OHA's page.
**Owner:** consider a short note to OHA asking whether using the layer is acceptable.

### Credit and attribution (done)

Settings now has a "Data sources and credits" section naming ODFW, OHA, NWS, USGS, OpenStreetMap contributors with
Protomaps, MapLibre, and the font licences. The map's attribution control shows "© OpenStreetMap contributors ·
Protomaps" (it was empty, which did not meet the ODbL; `tests/e2e/offline.mjs` now fails if it is empty).

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
- Favorited waterbodies (any account's) get hourly NWS refreshes. Favorites are per account: see `docs/accounts.md`.
