"""US Army Corps of Engineers (Northwestern Division) reservoir pool elevations for the Willamette projects.

This reads the JSON service behind the Corps' own water-control pages. It is not documented as an API:
expect it to change, and treat a parse failure as 'stale'. The server sends an incomplete certificate chain
(no DigiCert intermediate), so that one intermediate is bundled in app/certs and added to the trust store
for this host only. Certificate verification is never turned off.

Elevations are feet above sea level (NGVD29), 15-minute data, and are unverified: the Corps revises them.
Holdover shows the level, how it changed, and the same date in earlier years from the Corps' own history. It
does not say what is full pool, and it does not say whether a ramp or a lake is usable.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import RawFetch, ReservoirReading, Waterbody

SOURCE = "corps"
BASE = "https://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson"
PAGE_URL = "https://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/"
CA = str(Path(__file__).resolve().parent.parent / "certs" / "digicert-g2-tls-rsa-2020-ca1.pem")
# Corps location code -> the seeded waterbody it is the pool of. Codes were read from the service's own project
# metadata (BCL, CGR, LOP and FRN also exist there but have no waterbody here).
PROJECTS = {
    "DET": "Detroit Reservoir", "GPR": "Green Peter Reservoir", "DEX": "Dexter Reservoir", "FOS": "Foster Reservoir",
    "COT": "Cottage Grove Reservoir", "DOR": "Dorena Reservoir", "FAL": "Fall Creek Reservoir",
    "BLU": "Blue River Reservoir", "HCR": "Hills Creek Reservoir",
}
SERIES = "{}.Elev-Forebay.Inst.0.0.Best"
MIN_PERIOD_H, MAX_PERIOD_DAYS = 3, 7
HISTORY_YEARS = (1, 2, 3)
STALE_H = 3


class ParseError(Exception):
    pass


def url_for(codes=tuple(PROJECTS), *, backward: str | None = None, start: str | None = None, end: str | None = None) -> str:
    query = json.dumps([SERIES.format(c) for c in codes], separators=(",", ":"))
    url = f"{BASE}?timezone=GMT&query={quote(query, safe='')}"
    if backward:
        return f"{url}&backward={backward}"
    return f"{url}&startdate={start}&enddate={end}"


def parse(body: bytes | str) -> list[dict]:
    """Rows of {project, observed_at (UTC, minute precision), elevation_ft}. Odd values are skipped, not guessed."""
    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise TypeError("not an object")
        out = []
        for code, proj in data.items():
            if code not in PROJECTS:
                continue
            ts = proj["timeseries"].get(SERIES.format(code))
            if ts is None:
                continue
            if (ts.get("units") or "").strip().lower() != "ft":
                raise ValueError(f"{code}: unexpected units {ts.get('units')!r}")
            for t, value, *_ in ts.get("values", []):
                if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 < value < 3000:
                    continue
                at = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
                out.append({"project": code, "observed_at": at.isoformat(timespec="minutes"), "elevation_ft": float(value)})
        return out
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ParseError(f"unexpected Corps payload: {exc}") from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fetch_store(session: Session, url: str, fetch: Fetcher) -> int | None:
    """Fetch, keep the raw body, parse, insert new rows. Returns rows added, or None on failure."""
    status, body = fetch(url)
    raw, _ = store_fetch(session, SOURCE, url, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return None
    try:
        rows = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return None
    added = 0
    for r in rows:
        if session.get(ReservoirReading, (r["project"], r["observed_at"])) is None:
            session.add(ReservoirReading(raw_fetch_id=raw.id, **r))
            added += 1
    raw.parse_ok = 1
    session.commit()
    return added


def _hours_to_fetch(session: Session) -> int:
    last = session.scalar(select(ReservoirReading.observed_at).order_by(ReservoirReading.observed_at.desc()).limit(1))
    if last is None:
        return MAX_PERIOD_DAYS * 24
    gap = (_now() - datetime.fromisoformat(last)).total_seconds() / 3600 + 1
    return int(min(max(gap, MIN_PERIOD_H), MAX_PERIOD_DAYS * 24)) + 1


def _near(session: Session, project: str, target: datetime, within: timedelta) -> ReservoirReading | None:
    lo, hi = (target - within).isoformat(timespec="minutes"), (target + within).isoformat(timespec="minutes")
    rows = session.scalars(select(ReservoirReading).where(
        ReservoirReading.project == project, ReservoirReading.observed_at >= lo, ReservoirReading.observed_at <= hi)).all()
    return min(rows, key=lambda r: abs(datetime.fromisoformat(r.observed_at) - target), default=None)


def _history_gaps(session: Session, today: datetime) -> list[int]:
    return [y for y in HISTORY_YEARS if _near(session, "DET", _years_ago(today, y), timedelta(days=1)) is None]


def _years_ago(day: datetime, years: int) -> datetime:
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 Feb
        return day.replace(year=day.year - years, day=28)


def run_job(session: Session, fetch: Fetcher | None = None) -> dict:
    fetch = fetch or (lambda u: http_fetch(u, extra_ca=CA))
    added = _fetch_store(session, url_for(backward=f"{_hours_to_fetch(session)}h"), fetch)
    if added is None:
        return {"ok": False}
    out: dict = {"ok": True, "added": added}
    today = _now()
    for y in _history_gaps(session, today):  # same date in earlier years, kept once, small windows
        centre = _years_ago(today, y)
        start, end = (centre - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"), (centre + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        n = _fetch_store(session, url_for(start=start, end=end), fetch)
        out[f"history_{y}y"] = n
    return out


def _step(session: Session, project: str, latest: ReservoirReading, hours: int, within_h: int) -> float | None:
    then = _near(session, project, datetime.fromisoformat(latest.observed_at) - timedelta(hours=hours), timedelta(hours=within_h))
    return round(latest.elevation_ft - then.elevation_ft, 2) if then else None


def level(session: Session, project: str, today: datetime | None = None) -> dict | None:
    latest = session.scalar(select(ReservoirReading).where(ReservoirReading.project == project)
                            .order_by(ReservoirReading.observed_at.desc()).limit(1))
    if latest is None:
        return None
    at = datetime.fromisoformat(latest.observed_at)
    now = today or _now()
    earlier = []
    for y in HISTORY_YEARS:
        r = _near(session, project, _years_ago(at, y), timedelta(hours=18))
        if r is not None:
            earlier.append({"year": at.year - y, "elevation_ft": r.elevation_ft})
    return {"project": project, "elevation_ft": latest.elevation_ft, "as_of": latest.observed_at,
            "stale": (now - at).total_seconds() / 3600 > STALE_H,
            "change_24h_ft": _step(session, project, latest, 24, 3), "change_7d_ft": _step(session, project, latest, 24 * 7, 6),
            "earlier_years": earlier, "datum": "NGVD29", "source": "U.S. Army Corps of Engineers", "page": PAGE_URL}


def for_waterbody(session: Session, wb: Waterbody) -> dict | None:
    project = next((c for c, name in PROJECTS.items() if name == wb.name), None)
    return level(session, project) if project else None
