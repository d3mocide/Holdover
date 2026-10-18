"""Accounts are optional: anonymous visitors can read everything public. Anything that stores or syncs personal
data needs a session. Sessions are server-side rows keyed by a hash of an HttpOnly cookie."""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import User, UserSession
from app.security import hash_token, new_token

COOKIE = "holdover_session"
SAFE = {"GET", "HEAD", "OPTIONS"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def iso(d: datetime) -> str:
    return d.isoformat(timespec="seconds")


def csrf_guard(request: Request) -> None:
    """Cookies ride along on cross-site requests, so state-changing calls must carry a header a cross-site page
    cannot send without a CORS preflight (which this server never approves). SameSite=Lax is the second layer."""
    if request.method not in SAFE and request.headers.get("x-holdover") != "1":
        raise HTTPException(403, "missing X-Holdover header")


def _https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"


def start_session(response: Response, request: Request, session: Session, user: User) -> None:
    s = get_settings()
    token = new_token()
    now = _now()
    session.add(UserSession(token_hash=hash_token(token), user_id=user.id, created_at=iso(now), last_used_at=iso(now),
                            expires_at=iso(now + timedelta(days=s.session_days)),
                            device=(request.headers.get("user-agent") or "")[:120] or None))
    session.commit()
    secure = s.cookie_secure if s.cookie_secure is not None else _https(request)
    response.set_cookie(COOKIE, token, max_age=s.session_days * 86400, httponly=True, samesite="lax", secure=secure, path="/")


def end_session(response: Response, request: Request, session: Session) -> None:
    token = request.cookies.get(COOKIE)
    if token:
        row = session.get(UserSession, hash_token(token))
        if row:
            session.delete(row)
            session.commit()
    response.delete_cookie(COOKIE, path="/")


def optional_user(request: Request, session: Session = Depends(get_session)) -> User | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    row = session.get(UserSession, hash_token(token))
    now = _now()
    if row is None or datetime.fromisoformat(row.expires_at) <= now:
        return None
    user = session.get(User, row.user_id)
    if user is None or user.disabled:
        return None
    if now - datetime.fromisoformat(row.last_used_at) > timedelta(hours=1):  # sliding expiry, written at most hourly
        row.last_used_at = iso(now)
        row.expires_at = iso(now + timedelta(days=get_settings().session_days))
        session.commit()
    return user


def require_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(401, "sign in required")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "admin only")
    return user
