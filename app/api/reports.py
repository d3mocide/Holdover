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
        "digest": {"text": r.summary_text, "model": r.model, "as_of": r.generated_at} if r.summary_text else None,
        "items": [{"id": i.id, "waterbody_id": i.waterbody_id, "waterbody_raw": i.waterbody_raw,
                   "species": i.species, "rating": i.rating, "note": i.note, "source_sentence": i.source_sentence}
                  for i in items],
        "pending_review": session.scalar(select(func.count()).select_from(ReportItem).where(
            ReportItem.report_id == r.id, ReportItem.status == "review")),
    }}
