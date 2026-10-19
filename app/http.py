"""Polite fetching: identifying UA, backoff on 429/5xx, raw body stored before any parsing."""
import hashlib
import ssl
import time
from collections.abc import Callable
from datetime import datetime, timezone

import certifi
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import RawFetch

# A fetcher returns (status, body). Injectable so tests and fixture replays need no network.
Fetcher = Callable[[str], tuple[int | None, bytes]]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def http_fetch(url: str, *, retries: int = 3, timeout: float = 30, extra_ca: str | None = None, system_trust: bool = False) -> tuple[int | None, bytes]:
    """extra_ca: a PEM file added to the trust store for hosts that omit an intermediate certificate from their chain.
    system_trust: use the operating system's store, for a host whose (newer) root the bundled store lacks.
    Verification is never switched off."""
    verify: bool | ssl.SSLContext = True
    if system_trust:  # the operating system's certificate store (kept current by OS updates) instead of the bundled one; verification stays on
        verify = ssl.create_default_context()
    elif extra_ca:
        verify = ssl.create_default_context(cafile=certifi.where())
        verify.load_verify_locations(extra_ca)
    headers = {"User-Agent": get_settings().user_agent}
    delay = 2.0
    status: int | None = None
    body = b""
    for attempt in range(retries + 1):
        try:
            r = httpx.get(url, headers=headers, follow_redirects=True, timeout=timeout, verify=verify)
            status, body = r.status_code, r.content
        except httpx.HTTPError as exc:
            status, body = None, str(exc).encode()
        if status is not None and status != 429 and status < 500:
            break
        if attempt < retries:
            time.sleep(delay)
            delay *= 2
    return status, body


def store_fetch(session: Session, source: str, url: str, status: int | None, body: bytes) -> tuple[RawFetch, bool]:
    """Insert the raw_fetch row. Returns (row, unchanged) where unchanged means the body hash
    equals the previous successful fetch of the same URL (so parsing can be skipped)."""
    h = hashlib.sha256(body).hexdigest()
    prev = session.scalar(
        select(RawFetch)
        .where(RawFetch.source == source, RawFetch.url == url, RawFetch.status == 200, RawFetch.parse_ok == 1)
        .order_by(RawFetch.id.desc())
        .limit(1)
    )
    row = RawFetch(source=source, url=url, fetched_at=now_iso(), status=status, content_hash=h, body=body)
    session.add(row)
    session.flush()
    return row, bool(prev and prev.content_hash == h)


def quick_fetch(url: str) -> tuple[int | None, bytes]:
    """One short attempt, for on-demand refreshes inside a request."""
    return http_fetch(url, retries=0, timeout=8)
