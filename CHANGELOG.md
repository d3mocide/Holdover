# Changelog

Versions follow `0.minor.patch` while the app is still changing quickly: a minor version adds features, a patch fixes things. The version is in
`pyproject.toml` and `web/package.json` (a test keeps them equal) and is shown in Settings and `/healthz`. Details and evidence for each change are
in [docs/BUILD_LOG.md](docs/BUILD_LOG.md).

## Unreleased

**Rivers.** 36 popular rivers across all six zones as waterbodies with their live gauges, flow against each river's own median, NOAA flood status (48 gauges, polled every 2 hours), water quality where a sensor is current, and Willamette Falls fish counts on the rivers above the falls. Settings, Place pins moves a river's pin to where you fish.
Rankings are about 3 times faster.

## 0.6.0

**Everywhere in Oregon.** All six ODFW zones (Willamette, Central, Northwest, Southwest, Northeast, Southeast): waterbodies, pins, gauges, stocking and a
zone pill on the map. Pins come from OpenStreetMap matches and many waters are left unpinned on purpose: admins place them from Settings, **Place pins**.

**A different Map and Plan.** Map is the map plus a "Best bets today" card. Plan looks ahead: the next 7 days, and ODFW's published stocking schedule by month, about a year out.
Forms (Log a trip, Add gear) open as a drawer beside the panel.

**Weekly report per zone.** A briefing built from the data (watch-outs, where to fish, stocking, rivers and reservoirs) ending with ODFW's own words. A local model writes short paragraphs
from those facts and every paragraph is checked against them. Without a model you get the facts.

**More conditions.** Army Corps reservoir levels (Willamette), NOAA flood status, ODF fire danger and wildfire perimeters on the sheet and the map, and a redesigned Gauges page that compares each flow with its own median.
The model's reading of ODFW's report shows as faint, labelled rating badges on the map until you accept or reject it.

**Smaller things.** A 12 or 24 hour clock setting, stocking weeks grouped as coming up and already stocked, only real alerts shown on a waterbody, no glows, hide the side panel, a Legend and zone pill that stay out of the way.

**Behind the scenes.** Stocking schedule and report are fetched once a week (Friday), with a startup catch-up so a new install or a newly enabled zone is not empty. One log line per data job. Per-zone stocking aliases (ODFW reuses
names across zones), with a repair for rows that had been attached to the wrong zone.

**Upgrading from 0.5.0** (`docker compose pull && docker compose up -d`): migrations 0007 and 0008 run automatically and the seed adds the five new zones; the first start then fetches them (about 30 ODFW requests once, then weekly) and
backfills a week of gauge flow, which takes a few minutes. New optional settings: `ENABLED_ZONES` (default all six), `LLM_EXTRACT_MODEL` and `LLM_EXTRACT_TIMEOUT` (a slower model for the weekly report), `LLM_TIMEOUT`. Rehearsed on a database built by 0.5.0:
all stocking history kept, nothing left for review. The map tiles are not in the image: run `scripts/install-basemap.sh` once if the Pi has none.

## 0.5.0

First published version: stocking map, planner, offline journal, accounts, gear, three themes, Water Data API for USGS.
