from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import RawFetch, Report, ReportItem
from app.sources.odfw_report import SOURCE, URL, parse

router = APIRouter()


def latest_report(session: Session, zone: str) -> Report | None:
    return session.scalar(select(Report).where(Report.zone == zone).order_by(Report.issued_on.desc(), Report.id.desc()).limit(1))


@router.get("/reports")
def reports(zone: str = "willamette", session: Session = Depends(get_session)):
    r = latest_report(session, zone)
    if r is None:
        return {"zone": zone, "report": None}
    raw = session.get(RawFetch, r.raw_fetch_id)
    items = session.scalars(select(ReportItem).where(ReportItem.report_id == r.id, ReportItem.status == "accepted")).all()
    return {"zone": zone, "report": {
        "issued_on": r.issued_on, "source_url": URL, "fetched_at": raw.fetched_at,
        # verbatim ODFW wording, always available even when the LLM host is down
        "bullets": parse(raw.body).zones.get(zone, []),
        "items": [{"id": i.id, "waterbody_id": i.waterbody_id, "waterbody_raw": i.waterbody_raw,
                   "species": i.species, "rating": i.rating, "note": i.note, "source_sentence": i.source_sentence}
                  for i in items],
        "pending_review": session.scalar(select(func.count()).select_from(ReportItem).where(
            ReportItem.report_id == r.id, ReportItem.status == "review")),
    }}


ZONES = [("willamette", "Willamette"), ("nw", "Northwest"), ("sw", "Southwest"), ("central", "Central"), ("ne", "Northeast"), ("se", "Southeast")]


@router.get("/reports/all")
def all_reports(issued_on: str | None = None, session: Session = Depends(get_session)):
    """Every zone of one weekly report, in ODFW's own wording (re-derived from the stored page), and the issue dates we hold.
    Nothing here is generated: it works with the LLM off."""
    dates = list(session.scalars(select(Report.issued_on).distinct().order_by(Report.issued_on.desc())))
    pick = issued_on or (dates[0] if dates else None)
    rows = {r.zone: r for r in session.scalars(select(Report).where(Report.issued_on == pick))} if pick else {}
    zones, fetched = [], None
    for key, label in ZONES:
        r = rows.get(key)
        if r is None:
            continue
        raw = session.get(RawFetch, r.raw_fetch_id)
        fetched = fetched or raw.fetched_at
        zones.append({"zone": key, "label": label, "bullets": parse(raw.body).zones.get(key, [])})
    return {"issued_on": pick, "available": dates, "source_url": URL, "fetched_at": fetched, "zones": zones}
