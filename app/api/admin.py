from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_token
from app.db import get_session
from app.models import Report, ReportItem, Waterbody, WaterbodyAlias
from app.scheduler import run_explain, run_nws, run_oha, run_reports, run_stocking, run_usgs

router = APIRouter(dependencies=[Depends(require_token)])


@router.get("/aliases")
def aliases(status: str = "unconfirmed", session: Session = Depends(get_session)):
    q = select(WaterbodyAlias).order_by(WaterbodyAlias.id)
    if status == "unconfirmed":
        q = q.where(WaterbodyAlias.confirmed == 0)
    elif status == "confirmed":
        q = q.where(WaterbodyAlias.confirmed == 1)
    out = []
    for a in session.scalars(q):
        wb = session.get(Waterbody, a.waterbody_id) if a.waterbody_id else None
        out.append({"id": a.id, "alias_text": a.alias_text, "source": a.source,
                    "confirmed": bool(a.confirmed), "proposed_confidence": a.proposed_confidence,
                    "proposed_waterbody": {"id": wb.id, "name": wb.name} if wb else None})
    return out


class Confirm(BaseModel):
    waterbody_id: int | None = None  # omit to accept the current proposal


@router.post("/aliases/{alias_id}/confirm")
def confirm(alias_id: int, body: Confirm | None = None, session: Session = Depends(get_session)):
    a = session.get(WaterbodyAlias, alias_id)
    if a is None:
        raise HTTPException(404)
    wb_id = (body.waterbody_id if body else None) or a.waterbody_id
    if wb_id is None or session.get(Waterbody, wb_id) is None:
        raise HTTPException(422, "waterbody_id required: this alias has no proposal")
    a.waterbody_id, a.confirmed = wb_id, 1
    session.commit()
    return {"id": a.id, "waterbody_id": wb_id, "confirmed": True}


@router.get("/waterbodies")
def waterbodies(session: Session = Depends(get_session)):
    return [{"id": w.id, "name": w.name} for w in session.scalars(select(Waterbody).order_by(Waterbody.name))]


@router.post("/jobs/stocking/run")
def run_now():
    return run_stocking()


@router.get("/review/items")
def review_items(status: str = "review", session: Session = Depends(get_session)):
    rows = session.execute(
        select(ReportItem, Report).join(Report, Report.id == ReportItem.report_id)
        .where(ReportItem.status == status).order_by(Report.issued_on.desc(), ReportItem.id)).all()
    out = []
    for i, r in rows:
        wb = session.get(Waterbody, i.waterbody_id) if i.waterbody_id else None
        out.append({"id": i.id, "zone": r.zone, "issued_on": r.issued_on, "waterbody_raw": i.waterbody_raw,
                    "waterbody": {"id": wb.id, "name": wb.name} if wb else None, "species": i.species,
                    "rating": i.rating, "note": i.note, "source_sentence": i.source_sentence})
    return out


class Accept(BaseModel):
    waterbody_id: int | None = None  # override or supply the match


@router.post("/review/items/{item_id}/accept")
def accept_item(item_id: int, body: Accept | None = None, session: Session = Depends(get_session)):
    i = session.get(ReportItem, item_id)
    if i is None:
        raise HTTPException(404)
    if body and body.waterbody_id is not None:
        if session.get(Waterbody, body.waterbody_id) is None:
            raise HTTPException(422, "unknown waterbody")
        i.waterbody_id = body.waterbody_id
    i.status = "accepted"
    session.commit()
    return {"id": i.id, "status": i.status}


@router.post("/review/items/{item_id}/reject")
def reject_item(item_id: int, session: Session = Depends(get_session)):
    i = session.get(ReportItem, item_id)
    if i is None:
        raise HTTPException(404)
    i.status = "rejected"
    session.commit()
    return {"id": i.id, "status": i.status}


@router.post("/jobs/reports/run")
def run_reports_now():
    return run_reports()


@router.post("/jobs/{name}/run")
def run_job_now(name: str):
    jobs = {"usgs": run_usgs, "nws": run_nws, "oha": run_oha, "explain": run_explain}
    if name not in jobs:
        raise HTTPException(404, "unknown job")
    return jobs[name]()


class Star(BaseModel):
    starred: bool


@router.post("/waterbodies/{wb_id}/star")
def star(wb_id: int, body: Star, session: Session = Depends(get_session)):
    wb = session.get(Waterbody, wb_id)
    if wb is None:
        raise HTTPException(404)
    wb.starred = int(body.starred)
    session.commit()
    return {"id": wb.id, "starred": bool(wb.starred)}
