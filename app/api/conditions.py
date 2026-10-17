from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conditions import conditions, latest_gauge
from app.db import get_session
from app.http import quick_fetch
from app.models import Gauge, Waterbody, WaterbodyGauge
from app.sources import nws

router = APIRouter()


@router.get("/day/{wb_id}")
def day(wb_id: int, date_: date | None = Query(None, alias="date"), refresh: bool = True, session: Session = Depends(get_session)):
    """Day-of bundle. Tries one short NWS refresh if the forecast is missing or old; any failure
    just means the cached forecast (with its own as-of time and stale flag) is served."""
    wb = session.get(Waterbody, wb_id)
    if wb is None:
        raise HTTPException(404)
    d = date_ or date.today()
    if refresh:
        cached = nws.cached(session, wb.id)
        if cached is None or nws.age_hours(cached["fetched_at"]) > 3:
            try:
                nws.refresh(session, wb, quick_fetch)
            except Exception:
                session.rollback()
    return {"waterbody": {"id": wb.id, "name": wb.name, "kind": wb.kind, "zone": wb.zone,
                          "lat": wb.lat, "lon": wb.lon, "regs_url": wb.regs_url},
            "conditions": conditions(session, wb, d)}


@router.get("/gauges")
def gauges(session: Session = Depends(get_session)):
    out = []
    for g in session.scalars(select(Gauge).order_by(Gauge.name)):
        item = latest_gauge(session, g)
        item["waterbody_ids"] = [r for r in session.scalars(select(WaterbodyGauge.waterbody_id).where(WaterbodyGauge.gauge_id == g.id))]
        out.append(item)
    return {"gauges": out, "note": "USGS values are provisional and subject to revision."}
