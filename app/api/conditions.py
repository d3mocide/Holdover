from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.conditions import conditions, latest_gauge
from app.db import get_session
from app.http import quick_fetch
from app.models import Gauge, GaugeReading, Waterbody, WaterbodyGauge
from app.llm.explain import _key, cached_text
from app.llm.prompts import PACK_VERSION
from app.packlist import pack_list
from app.planner import FISHERIES, wind_mph
from app.sources import nws

router = APIRouter()


@router.get("/gauges/{gauge_id}/history")
def gauge_history(gauge_id: int, hours: int = Query(168), session: Session = Depends(get_session)):
    """Bounded observed history from stored USGS data; never fetch a source inside a chart request."""
    if hours not in (24, 168):
        raise HTTPException(422, "hours must be 24 or 168")
    gauge = session.get(Gauge, gauge_id)
    if gauge is None:
        raise HTTPException(404)
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=hours)).isoformat(timespec="minutes")
    series = {}
    for param, unit in (("discharge_cfs", "cfs"), ("water_temp_c", "°F")):
        rows = session.execute(select(GaugeReading.observed_at, GaugeReading.value, GaugeReading.provisional)
                               .where(GaugeReading.gauge_id == gauge_id, GaugeReading.parameter == param,
                                      GaugeReading.observed_at >= start, GaugeReading.observed_at <= now.isoformat())
                               .order_by(GaugeReading.observed_at.desc()).limit(2500)).all()
        series[param] = {"unit": unit, "points": [{"observed_at": r.observed_at,
            "value": round(r.value * 9 / 5 + 32, 1) if param == "water_temp_c" else r.value,
            "provisional": bool(r.provisional)} for r in reversed(rows) if r.value is not None]}
    return {"gauge": {"id": gauge.id, "name": gauge.name, "site_no": gauge.site_no}, "hours": hours,
            "as_of": now.isoformat(timespec="seconds"), "series": series, "note": "Observed USGS data, provisional and subject to revision."}


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
def gauges(zone: str = "willamette", session: Session = Depends(get_session)):
    out = []
    for g in session.scalars(select(Gauge).where(Gauge.zone == zone).order_by(Gauge.name)):
        item = latest_gauge(session, g)
        item["waterbody_ids"] = [r for r in session.scalars(select(WaterbodyGauge.waterbody_id).where(WaterbodyGauge.gauge_id == g.id))]
        out.append(item)
    return {"gauges": out, "note": "USGS values are provisional and subject to revision."}
