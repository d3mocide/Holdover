from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.auth import csrf_guard, iso, require_admin
from app.config import get_settings
from app.db import get_session
from app.models import Favorite, Invite, Report, ReportItem, Trip, User, UserSession, Waterbody, WaterbodyAlias
from app.security import hash_password, hash_token, new_token, validate_password
from app.scheduler import run_briefing, run_corps, run_explain, run_nifc, run_nwps, run_nws, run_odf_fire, run_oha, run_reports, run_stocking, run_usgs

router = APIRouter(dependencies=[Depends(csrf_guard), Depends(require_admin)])


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
    jobs = {"usgs": run_usgs, "nws": run_nws, "oha": run_oha, "corps": run_corps, "odf_fire": run_odf_fire, "nifc": run_nifc, "nwps": run_nwps, "explain": run_explain, "briefing": run_briefing}
    if name not in jobs:
        raise HTTPException(404, "unknown job")
    return jobs[name]()


class Coords(BaseModel):
    # Willamette zone with margin. A wrong-hemisphere sign slip is the likeliest typo, so bounds are checked.
    lat: float | None = Field(None, ge=41.9, le=46.4)
    lon: float | None = Field(None, ge=-124.9, le=-116.4)


@router.post("/waterbodies/{wb_id}/coords")
def set_coords(wb_id: int, body: Coords, session: Session = Depends(get_session)):
    """Place or move a waterbody's pin. Send both lat and lon, or both null to remove the pin."""
    if (body.lat is None) != (body.lon is None):
        raise HTTPException(422, "send both lat and lon, or neither")
    wb = session.get(Waterbody, wb_id)
    if wb is None:
        raise HTTPException(404)
    wb.lat, wb.lon = body.lat, body.lon
    session.commit()
    return {"id": wb.id, "name": wb.name, "lat": wb.lat, "lon": wb.lon}


# ---- users and invites -------------------------------------------------------------------------------------

def _user_row(u: User, session: Session) -> dict:
    trips = session.scalar(select(func.count()).select_from(Trip).where(Trip.owner_id == u.id, Trip.deleted == 0))
    favs = session.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == u.id))
    last = session.scalar(select(func.max(UserSession.last_used_at)).where(UserSession.user_id == u.id))
    return {"id": u.id, "username": u.username, "is_admin": bool(u.is_admin), "disabled": bool(u.disabled),
            "created_at": u.created_at, "last_seen": last, "trips": trips, "favorites": favs}


@router.get("/users")
def users(session: Session = Depends(get_session)):
    return [_user_row(u, session) for u in session.scalars(select(User).order_by(User.id))]


class Disabled(BaseModel):
    disabled: bool


def _target(session: Session, uid: int) -> User:
    u = session.get(User, uid)
    if u is None:
        raise HTTPException(404)
    return u


@router.post("/users/{uid}/disabled")
def set_disabled(uid: int, body: Disabled, me: User = Depends(require_admin), session: Session = Depends(get_session)):
    u = _target(session, uid)
    if u.id == me.id:
        raise HTTPException(409, "you cannot disable your own account")
    u.disabled = int(body.disabled)
    if body.disabled:
        session.execute(delete(UserSession).where(UserSession.user_id == u.id))  # sign them out everywhere
    session.commit()
    return _user_row(u, session)


class AdminFlag(BaseModel):
    is_admin: bool


@router.post("/users/{uid}/admin")
def set_admin(uid: int, body: AdminFlag, me: User = Depends(require_admin), session: Session = Depends(get_session)):
    u = _target(session, uid)
    if not body.is_admin and u.is_admin and not session.scalar(
            select(func.count()).select_from(User).where(User.is_admin == 1, User.disabled == 0, User.id != u.id)):
        raise HTTPException(409, "there must be at least one active admin")
    u.is_admin = int(body.is_admin)
    session.commit()
    return _user_row(u, session)


class NewPassword(BaseModel):
    password: str


@router.post("/users/{uid}/password")
def reset_password(uid: int, body: NewPassword, session: Session = Depends(get_session)):
    u = _target(session, uid)
    try:
        u.password_hash = hash_password(validate_password(body.password))
    except ValueError as e:
        raise HTTPException(422, str(e))
    session.execute(delete(UserSession).where(UserSession.user_id == u.id))
    session.commit()
    return _user_row(u, session)


@router.post("/invites")
def create_invite(me: User = Depends(require_admin), session: Session = Depends(get_session)):
    """The code is shown once; only its hash is stored."""
    code = new_token()[:22]
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=get_settings().invite_days)
    inv = Invite(code_hash=hash_token(code), created_by=me.id, created_at=iso(now), expires_at=iso(exp))
    session.add(inv)
    session.commit()
    return {"id": inv.id, "code": code, "path": f"/?invite={code}", "expires_at": inv.expires_at}


@router.get("/invites")
def invites(session: Session = Depends(get_session)):
    now = iso(datetime.now(timezone.utc))
    return [{"id": i.id, "created_at": i.created_at, "expires_at": i.expires_at,
             "state": "used" if i.used_by else ("expired" if i.expires_at <= now else "open")}
            for i in session.scalars(select(Invite).order_by(Invite.id.desc()).limit(30))]


@router.delete("/invites/{iid}")
def revoke_invite(iid: int, session: Session = Depends(get_session)):
    inv = session.get(Invite, iid)
    if inv is None:
        raise HTTPException(404)
    if inv.used_by is None:
        session.delete(inv)
        session.commit()
    return {"ok": True}
