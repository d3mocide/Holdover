from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conditions import conditions, latest_gauge
from app.db import get_session
from app.http import quick_fetch
from app.models import Gauge, Waterbody, WaterbodyGauge
from app.llm.explain import _key, cached_text
from app.llm.prompts import PACK_VERSION
from app.packlist import pack_list
from app.planner import FISHERIES, wind_mph
from app.sources import nws

router = APIRouter()


@router.get("/day/{wb_id}")
def day(wb_id: int, date_: date | None = Query(None, alias="date"), fishery: str = "trout", refresh: bool = True,
        session: Session = Depends(get_session)):
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
    cond = conditions(session, wb, d)
    w = (cond["weather"] or {}).get("day") or {}
    pack = pack_list(d, fishery if fishery in FISHERIES else "trout", w.get("temp_f"), w.get("precip_pct"),
                     wind_mph(w.get("wind")), wb.kind)
    pack["intro_source"] = "template"
    g = cached_text(session, "pack", _key(str(wb.id), d.isoformat(), fishery, facts=pack["intro"]), PACK_VERSION)
    if g:
        pack["intro"], pack["intro_source"] = g.text, "llm"
    return {"waterbody": {"id": wb.id, "name": wb.name, "kind": wb.kind, "zone": wb.zone,
                          "lat": wb.lat, "lon": wb.lon, "regs_url": wb.regs_url},
            "conditions": cond, "pack": pack}


@router.get("/gauges")
def gauges(session: Session = Depends(get_session)):
    out = []
    for g in session.scalars(select(Gauge).order_by(Gauge.name)):
        item = latest_gauge(session, g)
        item["waterbody_ids"] = [r for r in session.scalars(select(WaterbodyGauge.waterbody_id).where(WaterbodyGauge.gauge_id == g.id))]
        out.append(item)
    return {"gauges": out, "note": "USGS values are provisional and subject to revision."}
