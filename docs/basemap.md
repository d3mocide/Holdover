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
