"""Propose waterbody names and pins for a new zone from the stocking schedule and the local basemap (OpenStreetMap).

Reads the unconfirmed stocking labels of a zone from a database that has fetched that zone's schedule, expands them to
readable names, and looks for same-named water features in the Oregon PMTiles inside each label's ODFW district region.
Read-only: it prints candidates for a person to choose from, and never writes the seed. A match is a suggestion, not proof.

    STOCKING_ZONE_VALUE=1 DATABASE_URL=sqlite:////tmp/central.db python -c "from app.db import session_factory; from app.sources import odfw_stocking as s; s.run_job(session_factory()())"
    DATABASE_URL=sqlite:////tmp/central.db python scripts/propose_zone.py /tmp/oregon.pmtiles central
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_coords as cc  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.db import session_factory  # noqa: E402
from app.models import StockingSnapshot, WaterbodyAlias  # noqa: E402

# lon_min, lat_min, lon_max, lat_max of each ODFW district's area, generous on purpose; used only to pick between same-named features
DISTRICT = {
    "Bend": (-122.3, 43.3, -119.4, 44.95), "The Dalles": (-122.1, 44.9, -119.9, 45.8), "Clackamas": (-122.2, 44.55, -121.4, 45.3),
}
ZONES = {"central": (-122.3, 43.3, -119.4, 45.8)}
WORDS = {"RES": "Reservoir", "LK": "Lake", "CR": "Creek", "R": "River", "PD": "Pond"}


def kind_of(label: str) -> str:
    low = label.lower()
    return "reservoir" if "reservoir" in low or " res" in low else "pond" if re.search(r"\b(pond|pit)\b", low) else "river" if re.search(r"\b(river|creek)\b", low) else "lake"


def nice(label: str) -> str:
    return " ".join(WORDS.get(w, w.capitalize()) for w in label.split())


def main():
    path, zone = sys.argv[1], sys.argv[2]
    cc.BBOX = ZONES[zone]
    feats = cc.collect(path, 14)
    print(f"{len(feats)} named water features in the {zone} zone", file=sys.stderr)
    out = []
    with session_factory()() as s:
        rows = s.execute(select(WaterbodyAlias.alias_text, func.max(StockingSnapshot.zone_office)).join(StockingSnapshot, StockingSnapshot.alias_id == WaterbodyAlias.id)
                         .group_by(WaterbodyAlias.alias_text).order_by(WaterbodyAlias.alias_text)).all()
    for label, office in rows:
        district = (office or "").split("/")[-1].strip()
        box = DISTRICT.get(district, ZONES[zone])
        kind = kind_of(label)
        cands = []
        for score, oname, lat, lon, kd, geom in cc.best_match(nice(label), kind, [label], feats):
            if box[0] <= lon <= box[2] and box[1] <= lat <= box[3]:
                cands.append({"osm_name": oname, "score": round(score, 2), "lat": round(lat, 5), "lon": round(lon, 5), "kind_detail": kd, "geom": geom})
        seen, uniq = set(), []
        for c in cands:
            k = (c["osm_name"], round(c["lat"], 2), round(c["lon"], 2))
            if k not in seen:
                seen.add(k)
                uniq.append(c)
        out.append({"label": label, "district": district, "name": nice(label), "kind": kind, "candidates": uniq[:5]})
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
