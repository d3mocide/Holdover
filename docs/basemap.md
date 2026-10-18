# Basemap (Oregon PMTiles)

Installed: Protomaps daily build 2026-10-16, Oregon bbox extract (503 MB). Data is OpenStreetMap, ODbL; keep the attribution. The app runs without a basemap (pins on a themed ground) and shows a note.

To refresh or reinstall, put an Oregon extract at `/data/tiles/oregon.pmtiles`. With the `pmtiles` CLI and a Protomaps daily build:

    pmtiles extract https://build.protomaps.com/YYYYMMDD.pmtiles oregon.pmtiles \
      --bbox=-124.9,41.9,-116.4,46.4

The map expects the Protomaps v4 schema (`water`, `roads` layers). Protomaps basemap data is derived from OpenStreetMap (ODbL); keep the attribution. Record the build date and licence here once chosen. The server serves the file with HTTP Range support.

With the compose setup the file lives in the `holdover-data` volume. Install it with:

    docker compose exec -u root holdover mkdir -p /data/tiles
    docker compose cp oregon.pmtiles holdover:/data/tiles/oregon.pmtiles
    docker compose exec -u root holdover chown -R holdover /data/tiles
    docker compose restart holdover   # /tiles is only mounted at startup if the directory exists

The `pmtiles` CLI is a single Go binary: https://github.com/protomaps/go-pmtiles/releases (the extract above transferred about 550 MB and took about 15 seconds on a home connection).

The map draws lakes and reservoirs as closed polygons and rivers from their centerlines. River polygons in OSM are often open-ended, so they only fade in at high zoom (`web/src/lib/MapView.svelte`).

## Labels and fonts

Place and water names use MapLibre glyphs (SDF PBF) bundled in `web/public/fonts/` (Noto Sans Regular, Medium, Italic; Latin ranges 0-255 and 256-511; about 620 KB; SIL OFL 1.1, see `NOTICE.txt` there). They are served by the app itself and precached by the service worker, so labels work offline with no third-party requests. Names come from the tiles (`name:en`, falling back to `name`). A glyph range that is not bundled returns 404 and affected characters are omitted. To add more scripts, fetch more ranges from https://github.com/protomaps/basemaps-assets into the same folders.

With a basemap installed the map ground is the sea and land polygons (`earth`) are drawn on top, so the Pacific beyond the extract reads as open ocean under the side panels. The map is limited to the extract area (`maxBounds` in `MapView.svelte`).
