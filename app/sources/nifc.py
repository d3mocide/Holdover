"""NIFC wildland fire perimeters (WFIGS, interagency, current) for Oregon.

Read from the public ArcGIS feature service. It is not documented as an API: expect it to change, and treat a
parse failure as 'stale'. A perimeter near a waterbody means a fire is burning in the area. It does NOT mean the
waterbody or any road to it is closed, and the absence of a perimeter does not mean there is no fire: perimeters lag
reality. The app says so and links to the agencies. Prescribed burns are left out; only wildfires count.
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.geo import contains, nearest_vertex_km
from app.http import Fetcher, http_fetch, store_fetch
from app.models import FireNearby, RawFetch, Waterbody

SOURCE = "nifc"
URL = ("https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
       "?f=geojson&where=attr_POOState%3D%27US-OR%27&outSR=4326&returnGeometry=true"
       "&outFields=poly_IncidentName%2Cpoly_GISAcres%2Cattr_PercentContained%2Cpoly_DateCurrent%2Cattr_FireCause%2Cattr_IncidentTypeCategory"
       "&geometryPrecision=5&maxAllowableOffset=0.0005")
PAGE_URL = "https://wildfire.oregon.gov"
NEAR_KM = 50
MAX_AGE_DAYS = 30  # a perimeter not updated for a month is not shown as an active fire


class ParseError(Exception):
    pass


def parse(body: bytes | str) -> list[dict]:
    """[{name, acres, contained, updated (UTC iso), type, geometry}]. An empty list is valid: it means no perimeters."""
    try:
        data = json.loads(body)
        if "error" in data:
            raise ValueError(f"service error {data['error'].get('code')}")
        out = []
        for f in data["features"]:
            p, geom = f["properties"], f.get("geometry")
            if not geom or not p.get("poly_IncidentName"):
                continue
            ms = p.get("poly_DateCurrent")
            out.append({
                "name": p["poly_IncidentName"].strip(), "acres": p.get("poly_GISAcres"), "contained": p.get("attr_PercentContained"),
                "updated": datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec="minutes") if ms else None,
                "type": p.get("attr_IncidentTypeCategory"), "geometry": geom})
        return out
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ParseError(f"unexpected NIFC payload: {exc}") from exc


def active(fires: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=MAX_AGE_DAYS)).isoformat(timespec="minutes")
    return [f for f in fires if f["type"] == "WF" and (f["contained"] is None or f["contained"] < 100)
            and f["updated"] and f["updated"] >= cutoff]


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    status, body = fetch(URL)
    raw, _ = store_fetch(session, SOURCE, URL, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False}
    try:
        fires = active(parse(body))
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False}
    n = 0
    for wb in session.scalars(select(Waterbody)):
        if wb.lat is None or wb.lon is None:
            continue
        for f in fires:
            inside = contains(wb.lat, wb.lon, f["geometry"])
            d = 0.0 if inside else nearest_vertex_km(wb.lat, wb.lon, f["geometry"])
            if d <= NEAR_KM:
                session.add(FireNearby(waterbody_id=wb.id, incident=f["name"], acres=f["acres"], percent_contained=f["contained"],
                                       updated_at=f["updated"], distance_km=round(d, 1), inside=int(inside), raw_fetch_id=raw.id))
                n += 1
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "active_fires": len(fires), "near_waterbodies": n}


def current(session: Session, wb_id: int) -> dict | None:
    """Active wildfires within NEAR_KM from the newest successful fetch, nearest first; None before the first fetch."""
    last = session.scalar(select(RawFetch).where(RawFetch.source == SOURCE, RawFetch.parse_ok == 1).order_by(RawFetch.id.desc()).limit(1))
    if last is None:
        return None
    rows = session.scalars(select(FireNearby).where(FireNearby.raw_fetch_id == last.id, FireNearby.waterbody_id == wb_id)
                           .order_by(FireNearby.distance_km, FireNearby.incident)).all()
    return {"as_of": last.fetched_at, "page": PAGE_URL, "near_km": NEAR_KM,
            "fires": [{"name": r.incident, "acres": round(r.acres) if r.acres else None, "percent_contained": r.percent_contained,
                       "updated": r.updated_at, "distance_km": r.distance_km, "inside": bool(r.inside)} for r in rows]}
