"""Sign-in, invites-based registration, and the signed-in user's own settings (home, favorites)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.auth import COOKIE, csrf_guard, end_session, iso, optional_user, require_user, start_session
from app.config import get_settings
from app.db import get_session
from app.models import Favorite, Invite, User, UserSession, Waterbody
from app.security import (burn_time, by_ip, by_user, hash_password, hash_token, validate_password, validate_username,
                          verify_password)

router = APIRouter(dependencies=[Depends(csrf_guard)])
GENERIC = "invalid username or password"


def profile(user: User, session: Session) -> dict:
    favs = [r for r in session.scalars(select(Favorite.waterbody_id).where(Favorite.user_id == user.id))]
    return {"id": user.id, "username": user.username, "is_admin": bool(user.is_admin),
            "home": {"lat": user.home_lat, "lon": user.home_lon} if user.home_lat is not None else None,
            "favorites": sorted(favs)}


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Creds(BaseModel):
    username: str
    password: str


@router.get("/auth/me")
def me(user: User | None = Depends(optional_user), session: Session = Depends(get_session)):
    """200 for everyone: signed out is a normal state, not an error."""
    s = get_settings()
    server_home = {"lat": s.home_lat, "lon": s.home_lon} if s.home_lat is not None and s.home_lon is not None else None
    return {"user": profile(user, session) if user else None, "server_home": server_home}


@router.post("/auth/login")
def login(body: Creds, request: Request, response: Response, session: Session = Depends(get_session)):
    name = (body.username or "").strip().lower()
    ip = request.client.host if request.client else "?"
    for key in (f"u:{name}", f"ip:{ip}"):
        wait = (by_user if key.startswith("u:") else by_ip).blocked(key)
        if wait:
            raise HTTPException(429, f"too many attempts, try again in {wait // 60 + 1} min", headers={"Retry-After": str(wait)})
    user = session.scalar(select(User).where(User.username == name))
    ok = bool(user) and not user.disabled and verify_password(body.password, user.password_hash)
    if user is None:
        burn_time(body.password)
    if not ok:
        by_user.fail(f"u:{name}")
        by_ip.fail(f"ip:{ip}")
        raise HTTPException(401, GENERIC)
    by_user.clear(f"u:{name}")
    start_session(response, request, session, user)
    return {"user": profile(user, session)}


@router.post("/auth/logout")
def logout(request: Request, response: Response, session: Session = Depends(get_session)):
    end_session(response, request, session)
    return {"ok": True}


def _open_invite(session: Session, code: str) -> Invite | None:
    inv = session.scalar(select(Invite).where(Invite.code_hash == hash_token(code or "")))
    if inv is None or inv.used_by is not None or datetime.fromisoformat(inv.expires_at) <= _now():
        return None
    return inv


@router.get("/auth/invite/{code}")
def invite_check(code: str, session: Session = Depends(get_session)):
    return {"valid": _open_invite(session, code) is not None}


class Register(Creds):
    invite: str


@router.post("/auth/register")
def register(body: Register, request: Request, response: Response, session: Session = Depends(get_session)):
    inv = _open_invite(session, body.invite)
    if inv is None:
        raise HTTPException(400, "this invite is invalid, used or expired")
    try:
        name, pw = validate_username(body.username), validate_password(body.password)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if session.scalar(select(User.id).where(User.username == name)) is not None:
        raise HTTPException(409, "that username is taken")
    user = User(username=name, password_hash=hash_password(pw), created_at=iso(_now()))
    session.add(user)
    session.flush()
    inv.used_by, inv.used_at = user.id, iso(_now())
    session.commit()
    start_session(response, request, session, user)
    return {"user": profile(user, session)}


class PasswordChange(BaseModel):
    current: str
    new: str


@router.post("/auth/password")
def change_password(body: PasswordChange, request: Request, user: User = Depends(require_user),
                    session: Session = Depends(get_session)):
    if not verify_password(body.current, user.password_hash):
        raise HTTPException(403, "current password is wrong")
    try:
        user.password_hash = hash_password(validate_password(body.new))
    except ValueError as e:
        raise HTTPException(422, str(e))
    keep = hash_token(request.cookies.get(COOKIE, ""))
    session.execute(delete(UserSession).where(UserSession.user_id == user.id, UserSession.token_hash != keep))  # sign out other devices
    session.commit()
    return {"ok": True}


class Home(BaseModel):
    # Willamette zone with margin. Null clears it. Half a coordinate is rejected below.
    lat: float | None = Field(None, ge=41.9, le=46.4)
    lon: float | None = Field(None, ge=-124.9, le=-116.4)


@router.put("/me/home")
def set_home(body: Home, user: User = Depends(require_user), session: Session = Depends(get_session)):
    if (body.lat is None) != (body.lon is None):
        raise HTTPException(422, "send both lat and lon, or neither")
    user.home_lat, user.home_lon = body.lat, body.lon
    session.commit()
    return profile(user, session)


def _wb_or_404(session: Session, wb_id: int) -> None:
    if session.get(Waterbody, wb_id) is None:
        raise HTTPException(404, "unknown waterbody")


@router.put("/me/favorites/{wb_id}")
def add_favorite(wb_id: int, user: User = Depends(require_user), session: Session = Depends(get_session)):
    _wb_or_404(session, wb_id)
    if session.get(Favorite, (user.id, wb_id)) is None:
        session.add(Favorite(user_id=user.id, waterbody_id=wb_id))
        session.commit()
    return profile(user, session)


@router.delete("/me/favorites/{wb_id}")
def remove_favorite(wb_id: int, user: User = Depends(require_user), session: Session = Depends(get_session)):
    fav = session.get(Favorite, (user.id, wb_id))
    if fav:
        session.delete(fav)
        session.commit()
    return profile(user, session)


class Merge(BaseModel):
    favorites: list[int] = []
    home: Home | None = None


@router.post("/me/merge")
def merge_local(body: Merge, user: User = Depends(require_user), session: Session = Depends(get_session)):
    """On sign-in the browser hands over what it had saved locally: favorites are unioned in, and a home
    location is adopted only if the account has none (the account wins)."""
    have = set(session.scalars(select(Favorite.waterbody_id).where(Favorite.user_id == user.id)))
    known = set(session.scalars(select(Waterbody.id).where(Waterbody.id.in_(body.favorites or [0]))))
    for wb_id in known - have:
        session.add(Favorite(user_id=user.id, waterbody_id=wb_id))
    h = body.home
    if h and h.lat is not None and h.lon is not None and user.home_lat is None:
        user.home_lat, user.home_lon = h.lat, h.lon
    session.commit()
    return profile(user, session)
