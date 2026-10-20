"""Build a tiny PMTiles file (a few polygons in the Protomaps layer names the map expects) for tests.
Not real map data: only for exercising the tile cache and offline path.

    python scripts/make_test_pmtiles.py data/tiles/oregon.pmtiles
"""
import gzip
import json
import math
import sys

import mapbox_vector_tile
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer


def lonlat_tile(lon, lat, z):
    n = 2**z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def tile_for(z, x, y):
    # one big "water" square covering the lower-left quarter of every tile, one road line across it
    g = {"water": {"features": [{"geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2048, 0], [2048, 2048], [0, 2048], [0, 0]]]},
                                 "properties": {}}]},
         "roads": {"features": [{"geometry": {"type": "LineString", "coordinates": [[0, 4096], [4096, 0]]}, "properties": {}}]}}
    return gzip.compress(mapbox_vector_tile.encode([{"name": k, **v} for k, v in g.items()], default_options={"extents": 4096}))


def main(out, bbox=(-124.5, 43.0, -121.0, 46.5)):
    tiles = {}
    for z in range(0, 12):
        x0, y0 = lonlat_tile(bbox[0], bbox[3], z)
        x1, y1 = lonlat_tile(bbox[2], bbox[1], z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                tiles[zxy_to_tileid(z, x, y)] = tile_for(z, x, y)
    with open(out, "wb") as f:
        w = Writer(f)
        for tid in sorted(tiles):
            w.write_tile(tid, tiles[tid])
        w.finalize({"tile_type": TileType.MVT, "tile_compression": Compression.GZIP, "min_zoom": 0, "max_zoom": 11,
                    "min_lon_e7": int(bbox[0]*1e7), "min_lat_e7": int(bbox[1]*1e7), "max_lon_e7": int(bbox[2]*1e7), "max_lat_e7": int(bbox[3]*1e7),
                    "center_zoom": 7, "center_lon_e7": int(-122.9e7), "center_lat_e7": int(44.6e7)},
                   {"name": "test", "vector_layers": [{"id": "water"}, {"id": "roads"}]})
    print(f"{len(tiles)} tiles -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], tuple(map(float, sys.argv[2].split(",")))) if len(sys.argv) > 2 else main(sys.argv[1])
