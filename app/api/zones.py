"""GET /api/zones: the zones the app offers, with how much is known about each."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import Gauge, Waterbody
from app.zones import enabled

router = APIRouter()


@router.get("/zones")
def zones(session: Session = Depends(get_session)):
    out = []
    for z in enabled(get_settings().enabled_zones):
        wbs = session.scalar(select(func.count()).select_from(Waterbody).where(Waterbody.zone == z.key))
        pinned = session.scalar(select(func.count()).select_from(Waterbody).where(Waterbody.zone == z.key, Waterbody.lat.is_not(None)))
        gauges = session.scalar(select(func.count()).select_from(Gauge).where(Gauge.zone == z.key))
        out.append({"key": z.key, "label": z.label, "report_key": z.report_key, "waterbodies": wbs, "pinned": pinned, "gauges": gauges})
    return {"zones": out}
