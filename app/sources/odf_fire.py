"""Oregon Department of Forestry public fire danger level, by regulated-use area.

Read from the public ArcGIS feature service behind ODF's own fire-restrictions map. It is not documented as an API:
expect it to change, and treat a parse failure as 'stale'. Only the danger level (1 Low to 4 Extreme) is used. What
that level means for a particular fire or use restriction is ODF's to say, so the app links to ODF and never restates
rules. ODF covers lands it protects; a waterbody outside every zone gets no level, never a guessed one.
"""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geo import contains
from app.http import Fetcher, http_fetch, store_fetch
from app.models import FireDanger, RawFetch, Waterbody

SOURCE = "odf_fire"
URL = ("https://gis.odf.oregon.gov/odfags/rest/services/Hosted/Fire_Danger_Level_View/FeatureServer/0/query"
       "?f=geojson&where=1%3D1&outSR=4326&returnGeometry=true&outFields=district%2Cregusearea%2Cfiredanger"
       "&geometryPrecision=4&maxAllowableOffset=0.003")
PAGE_URL = "https://gisapps.odf.oregon.gov/firerestrictions/PFR.html"
LABELS = {1: "Low", 2: "Moderate", 3: "High", 4: "Extreme"}


class ParseError(Exception):
    pass


def parse(body: bytes | str) -> list[dict]:
    """[{area, district, level, geometry}]. ArcGIS reports some failures as HTTP 200 with an error object."""
    try:
        data = json.loads(body)
        if "error" in data:
            raise ValueError(f"service error {data['error'].get('code')}")
        out = []
        for f in data["features"]:
            p, geom = f["properties"], f.get("geometry")
            if p.get("firedanger") in LABELS and geom and p.get("regusearea"):
                out.append({"area": p["regusearea"], "district": p.get("district"), "level": p["firedanger"], "geometry": geom})
        if not out:
            raise ValueError("no usable zones")
        return out
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ParseError(f"unexpected ODF fire danger payload: {exc}") from exc


def zone_for(zones: list[dict], lat: float, lon: float) -> dict | None:
    """The highest-danger zone containing the point (zones can touch; the more cautious reading wins)."""
    hits = [z for z in zones if contains(lat, lon, z["geometry"])]
    return max(hits, key=lambda z: z["level"], default=None)


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    status, body = fetch(URL)
    raw, _ = store_fetch(session, SOURCE, URL, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False}
    try:
        zones = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False}
    n = 0
    for wb in session.scalars(select(Waterbody)):
        if wb.lat is None or wb.lon is None:
            continue
        z = zone_for(zones, wb.lat, wb.lon)
        if z:
            session.add(FireDanger(waterbody_id=wb.id, level=z["level"], area=z["area"], district=z["district"], raw_fetch_id=raw.id))
            n += 1
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "zones": len(zones), "waterbodies_in_a_zone": n}


def current(session: Session, wb_id: int) -> dict | None:
    """The newest successful fetch's reading for a waterbody, with when it was fetched; None if outside every zone."""
    last = session.scalar(select(RawFetch).where(RawFetch.source == SOURCE, RawFetch.parse_ok == 1).order_by(RawFetch.id.desc()).limit(1))
    if last is None:
        return None
    row = session.scalar(select(FireDanger).where(FireDanger.raw_fetch_id == last.id, FireDanger.waterbody_id == wb_id))
    if row is None:
        return {"covered": False, "as_of": last.fetched_at, "page": PAGE_URL}
    return {"covered": True, "level": row.level, "label": LABELS[row.level], "area": row.area, "as_of": last.fetched_at, "page": PAGE_URL}


def _latest_ok(session: Session) -> RawFetch | None:
    return session.scalar(select(RawFetch).where(RawFetch.source == SOURCE, RawFetch.parse_ok == 1).order_by(RawFetch.id.desc()).limit(1))


def map_features(session: Session) -> dict:
    """Zone polygons with their level, from the newest stored response (for the map layer)."""
    raw = _latest_ok(session)
    if raw is None:
        return {"as_of": None, "features": []}
    feats = [{"type": "Feature", "geometry": z["geometry"],
              "properties": {"area": z["area"], "level": z["level"], "label": LABELS[z["level"]]}} for z in parse(raw.body)]
    return {"as_of": raw.fetched_at, "features": feats}
