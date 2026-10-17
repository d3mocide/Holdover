from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_token
from app.db import get_session
from app.models import Waterbody, WaterbodyAlias
from app.scheduler import run_stocking

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
