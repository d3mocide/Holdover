"""OHA cyanobacteria (harmful algae bloom) advisories.

The OHA web page renders its table client-side, so this reads the public ArcGIS feature service that
OHA's own advisory map uses (found 2026-10-17 by following the map's item metadata). That service is
not documented as an API: expect it to change, and treat a parse failure as 'stale'.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import Advisory, RawFetch, Waterbody
from app.normalize import name_key as _key

SOURCE = "oha"
URL = ("https://services.arcgis.com/uUvqNMGPm7axC2dD/arcgis/rest/services/HABs_Advisories_(Points)/"
       "FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson&outSR=4326")
PAGE_URL = "https://www.oregon.gov/oha/ph/healthyenvironments/recreation/harmfulalgaeblooms/pages/blue-greenalgaeadvisories.aspx"
ACTIVE = {"advisory": "algae:advisory", "precaution": "algae:precaution"}  # other statuses are lifted/below RUV


class ParseError(Exception):
    pass


def parse(body: bytes | str) -> list[dict]:
    try:
        feats = json.loads(body)["features"]
        out = []
        for f in feats:
            p = f["properties"]
            status = (p.get("AdvisoryStatus") or "").strip()
            issued = p.get("Issue_Date")
            out.append({
                "name": p["WaterbodyName"], "status": status, "kind": ACTIVE.get(status.lower()),
                "details": p.get("Details") or "", "toxin": p.get("Toxin"),
                "issued": datetime.fromtimestamp(issued / 1000, timezone.utc).date().isoformat() if issued else None,
                "lon": f["geometry"]["coordinates"][0] if f.get("geometry") else None,
                "lat": f["geometry"]["coordinates"][1] if f.get("geometry") else None,
            })
        return out
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"unexpected OHA payload: {exc}") from exc


def match(session: Session, name: str) -> int | None:
    key = _key(name)
    hits = [wb.id for wb in session.scalars(select(Waterbody)) if key and _key(wb.name) == key]
    return hits[0] if len(hits) == 1 else None


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    status, body = fetch(URL)
    raw, _ = store_fetch(session, SOURCE, URL, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False}
    try:
        rows = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False}
    n = 0
    for r in rows:
        if r["kind"] is None:
            continue
        wb_id = match(session, r["name"])
        if wb_id is None:
            continue  # only waterbodies we track get a marker; unmatched ones are not guessed at
        session.add(Advisory(kind=r["kind"], waterbody_id=wb_id, observed_at=r["issued"], raw_fetch_id=raw.id,
                             text=f'{r["status"]}: {r["name"]}. {r["details"]}'.strip()))
        n += 1
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "tracked_advisories": n}


def current(session: Session, wb_id: int | None = None) -> list[Advisory]:
    """Advisories from the newest successful fetch (snapshot model, like stocking)."""
    last = session.scalar(select(RawFetch.id).where(RawFetch.source == SOURCE, RawFetch.parse_ok == 1)
                          .order_by(RawFetch.id.desc()).limit(1))
    if last is None:
        return []
    q = select(Advisory).where(Advisory.raw_fetch_id == last)
    if wb_id is not None:
        q = q.where(Advisory.waterbody_id == wb_id)
    return list(session.scalars(q))
