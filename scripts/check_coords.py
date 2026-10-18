"""Cross-check seeded waterbody coordinates against named water features in the local basemap.

Reads the Oregon PMTiles file (OpenStreetMap data via Protomaps), collects named water polygons and
points in the Willamette zone at a zoom where ponds are present, matches them to the seed by name, and
reports the distance between the seeded pin and the OSM feature. Read-only: it never edits the seed.

    pip install pmtiles mapbox-vector-tile
    python scripts/check_coords.py data/tiles/oregon.pmtiles [--zoom 14] [--json out.json]   # about 2 minutes

A match is a suggestion, not proof: OSM names differ from ODFW labels ("Lake" vs "Reservoir"), and one
water can have several polygons. Look at anything over a few km before changing the seed.
"""
import argparse
import gzip
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import mapbox_vector_tile as mvt
from pmtiles.reader import MmapSource, Reader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.seed import SEED  # noqa: E402

BBOX = (-123.75, 43.55, -121.55, 46.15)  # lon_min, lat_min, lon_max, lat_max: the Willamette zone with margin
GENERIC = {"lake", "lakes", "reservoir", "res", "lk", "pond", "pd", "pond", "park", "river", "creek", "cr", "r", "the", "of", "recreation", "east", "west", "e", "w"}


def tile_xy(lon, lat, z):
    n = 2**z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def to_lonlat(x, y, tx, ty, z):
    n = 2**z
    return (tx + x / 4096) / n * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty + y / 4096) / n))))


def ring_area_centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if a == 0:
        return 0.0, ring[0][0], ring[0][1]
    return a / 2, cx / (6 * a), cy / (6 * a)


def tokens(name):
    return {t for t in re.findall(r"[a-z0-9]+", name.lower().replace("mt ", "mount ")) if t not in GENERIC}


def km(a, b):
    dlat = (a[0] - b[0]) * 111.0
    dlon = (a[1] - b[1]) * 111.0 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dlat, dlon)


LAYERS = ("water", "pois", "landuse")


def collect(path, zoom):
    r = Reader(MmapSource(open(path, "rb")))
    x0, y1 = tile_xy(BBOX[0], BBOX[1], zoom)
    x1, y0 = tile_xy(BBOX[2], BBOX[3], zoom)
    feats = defaultdict(list)  # name -> [(weight, lat, lon, kind_detail, geom, layer)]
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            d = r.get(zoom, tx, ty)
            if not d:
                continue
            try:
                d = gzip.decompress(d)
            except OSError:
                pass
            tile = mvt.decode(d, default_options={"y_coord_down": True})
            for layer in LAYERS:
                for f in tile.get(layer, {}).get("features", []):
                    name = f["properties"].get("name")
                    if not name:
                        continue
                    g, kd = f["geometry"], f["properties"].get("kind_detail") or f["properties"].get("kind")
                    if g["type"] == "Point":
                        lon, lat = to_lonlat(*g["coordinates"], tx, ty, zoom)
                        feats[name].append((0.0, lat, lon, kd, "point", layer))
                    elif g["type"] in ("Polygon", "MultiPolygon"):
                        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
                        for poly in polys:
                            area, cx, cy = ring_area_centroid([tuple(p) for p in poly[0]])
                            lon, lat = to_lonlat(cx, cy, tx, ty, zoom)
                            feats[name].append((abs(area), lat, lon, kd, "polygon", layer))
                    elif g["type"] in ("LineString", "MultiLineString"):
                        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
                        for ln in lines:
                            mid = ln[len(ln) // 2]
                            lon, lat = to_lonlat(mid[0], mid[1], tx, ty, zoom)
                            feats[name].append((0.0, lat, lon, kd, "line", layer))
    return feats


STILL = {"lake", "pond", "reservoir"}


def best_match(seed_name, kind, labels, feats, near=None):
    want = tokens(seed_name) | {t for lab in labels for t in tokens(lab)}
    out = []
    for name, parts in feats.items():
        have = tokens(name)
        if not want or not have:
            continue
        score = len(want & have) / len(want | have)
        if score < 0.5:
            continue
        for _, lat, lon, kd, geom, layer in parts:
            # Still water matches polygons and points; moving water matches lines. A creek is not a lake.
            if kind in STILL and (geom == "line" or re.search(r"\b(creek|river|cr|r)\b", name.lower())):
                continue
            if kind not in STILL and geom != "line":
                continue
            out.append((score, name, lat, lon, kd, f"{layer}/{geom}"))
    out.sort(key=lambda m: (-m[0], km(near, (m[2], m[3])) if near else 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pmtiles")
    ap.add_argument("--zoom", type=int, default=14)
    ap.add_argument("--json")
    a = ap.parse_args()
    feats = collect(a.pmtiles, a.zoom)
    print(f"{len(feats)} named water features in the zone at z{a.zoom}\n", file=sys.stderr)
    report = []
    for name, kind, lat, lon, labels in SEED:
        near = (lat, lon) if lat is not None else None
        m = best_match(name, kind, labels, feats, near)
        row = {"waterbody": name, "kind": kind, "seed": [lat, lon], "matches": []}
        seen = set()
        for score, oname, mlat, mlon, kd, geom in m:
            key = (oname, round(mlat, 3), round(mlon, 3))
            if key in seen:
                continue
            seen.add(key)
            row["matches"].append({"osm_name": oname, "score": round(score, 2), "lat": round(mlat, 5), "lon": round(mlon, 5),
                                   "kind_detail": kd, "geom": geom, "km_from_seed": round(km(near, (mlat, mlon)), 1) if near else None})
            if len(row["matches"]) >= 4:
                break
        report.append(row)
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1))
    for r in report:
        s = r["seed"]
        head = f"{r['waterbody']:<44} seed={'none' if s[0] is None else f'{s[0]:.4f},{s[1]:.4f}'}"
        if not r["matches"]:
            print(f"{head}  -> no OSM match")
            continue
        for i, m in enumerate(r["matches"]):
            d = "" if m["km_from_seed"] is None else f"  {m['km_from_seed']:>5} km"
            print(f"{head if i == 0 else ' ' * len(head)}  -> {m['osm_name']!r} {m['lat']:.4f},{m['lon']:.4f} ({m['geom']}, {m['kind_detail']}, score {m['score']}){d}")


if __name__ == "__main__":
    main()
