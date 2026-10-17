import hmac

from fastapi import Header, HTTPException

from app.config import get_settings


def require_token(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().holdover_token
    if not token:
        raise HTTPException(503, "HOLDOVER_TOKEN is not configured")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied.strip(), token):
        raise HTTPException(401, "invalid or missing bearer token", headers={"WWW-Authenticate": "Bearer"})
