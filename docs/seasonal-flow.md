# Seasonal river-flow context

River details, Plan results and river day views have an expandable **Seasonal flow context** card: historical
median and middle 50% band, exact sample/year coverage, a textual alternative for every chart day, and one dated
instantaneous observation. Existing seven-day flow comparisons and fishing-score weights are unchanged.

## Enable historical downloads

Downloads are disabled until the owner configures a free key, following the USGS automated-client policy in
[sources.md](sources.md). Existing live-flow polling is unchanged.

1. Obtain a key through [USGS](https://api.waterdata.usgs.gov/signup).
2. Set `USGS_API_KEY` in the server environment or ignored `.env`. Never paste it into chat, commit it, or put
   it in browser storage. The historical client sends an `X-Api-Key` header; raw URLs contain no key.
3. Start the updated image, or refresh local development with `docker compose -f docker-compose.dev.yml up -d api`.
   Additive Alembic migration `0010` creates only a public derived-cache table. It changes no existing readings
   or personal tables. Production needs a release containing the feature first.
4. Reload the app. Enabled installs consider one river-linked USGS gauge per half-hour job, gradually warming
   coverage. Successful baselines refresh monthly; failures defer retries for a day. The operator CLI
   `python -m app.cli usgs_daily` runs the same bounded due-work job once, not a forced bulk refresh.

Without a key, cards and Settings explain that downloads are disabled. Existing caches remain viewable with age
labels. Full historical requests have not been run against USGS in this feature's acceptance evidence; a single
three-day response was inspected and saved as a parser fixture. No synthetic baseline is installed on personal dev.

## Baseline definition

Source: Water Data API v1 `daily`, discharge parameter `00060`, statistic `00003` (daily mean), unit `ft^3/s`.
Only approved, finite, nonnegative daily means are used; unreliable qualifiers are excluded. The requested period
is the **ten complete calendar years before retrieval** (2016–2025 for retrieval in 2026), not a period-of-record
statistic or a standardized thirty-year climate normal.

For each month/day, Holdover pools approved means in a **15-day window, ±7 days**, across baseline years. A leap
reference calendar preserves February 29 and wraps December/January. Expected samples count only real dates;
absent leap days are not fabricated. Represented years are counted from actual samples in that window.

Quantiles interpolate linearly at `(n − 1) × p` in sorted samples (`p = .25, .5, .75`). They display only with
**75 daily values across five distinct years**. Missing/insufficient dates stay blank, not bridged or assigned zero.
Every point keeps samples, expected samples and represented years. These are Holdover's smoothed summaries,
not USGS-produced percentile statistics.

Charts span thirty days either side of the selected plan date. The latest reading's dot is placed on its actual
Pacific date. Its above/within/below-middle-50% description compares against the **observation date's** baseline,
even for future plans. Instantaneous peaks can differ substantially from daily means. This is not a forecast,
validated fishing range or catch probability, and says nothing authoritative about access, regulations or flood
safety; existing official NOAA/ODFW links remain the sources for those topics.

## Freshness, failures and offline

Raw responses precede parsing. Derived caches publish only after all bounded pages succeed. HTTP/schema/unit
errors, unsafe pagination, conflicting values and incomplete paging retain the last good payload and retrieval
time, marked stale. An unexpected empty refresh retains a nonempty last good cache. Raw fetches are append-only.

A failed refresh, baseline older than 45 days, future retrieval time, or baseline ending before the previous
calendar year marks it stale. Readings older than three hours or in the future cannot support a current
comparison. Stale baselines remain readable with labels, but comparative classifications are hidden. Browser
clocks age cached values while open. A missing baseline never becomes a seven-day median labelled seasonal.

River waterbody responses and exact-date day bundles contain the full series. Preparing a river trip saves it
with those bundles in existing IndexedDB storage. Opened Plan charts use the public API cache. No personal table,
owner-model change, browser schema migration, outside map service or LLM input is added. Older bundles without
the field retain ordinary conditions and an honest missing-seasonal-chart message.

Parser/maths/cache/migration, synthetic disposable browser, accessibility and airplane-mode evidence is in
[BUILD_LOG.md](BUILD_LOG.md). Complete real-gauge download/approval coverage, field interpretation and physical
phone storage/eviction remain unverified until the key and those gates are available.
