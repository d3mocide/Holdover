# Basemap (Oregon PMTiles)

Not installed yet. The app runs without it (pins on a themed ground) and shows a note.

To add one, put an Oregon extract at `/data/tiles/oregon.pmtiles`. With the `pmtiles` CLI and a Protomaps daily build:

    pmtiles extract https://build.protomaps.com/YYYYMMDD.pmtiles oregon.pmtiles \
      --bbox=-124.9,41.9,-116.4,46.4

The map expects the Protomaps v4 schema (`water`, `roads` layers). Protomaps basemap data is derived from OpenStreetMap (ODbL); keep the attribution. Record the build date and licence here once chosen. The server serves the file with HTTP Range support.
