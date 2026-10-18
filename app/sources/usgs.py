"""USGS instantaneous values from the Water Data API (OGC API, https://api.waterdata.usgs.gov/ogcapi/v1/).

Keyless (an API key only raises rate limits) and public domain, but every value is PROVISIONAL and the UI says so.
This adapter is the only place that knows the URL shape. It replaces the legacy waterservices.usgs.gov endpoint, which
USGS is retiring in early 2027: set USGS_API=legacy to fall back to it until then, then delete the legacy code below.

What a job fetches, and why (the GeoJSON is about ten times bulkier than the legacy JSON, and every response is stored raw):
  - routine poll: `latest-continuous`, the newest value of every series (about 34 KB for 16 gauges)
  - gap fill: `continuous` over a bounded window when the newest stored reading is old (the app was down)
  - first run or a new gauge: seven days of discharge only, which is all the flow baseline needs
"""
import json
from datetime import datetime, timedelta, timezone
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.http import Fetcher, http_fetch, store_fetch
from app.models import Gauge, GaugeReading, RawFetch

SOURCE = "usgs"
BASE = "https://api.waterdata.usgs.gov/ogcapi/v1/collections"
LEGACY_BASE = "https://waterservices.usgs.gov/nwis/iv/"
PARAMS = {"00060": "discharge_cfs", "00065": "gage_height_ft", "00010": "water_temp_c"}
# The unit each parameter must arrive in. A reading in any other unit is skipped, never silently reinterpreted.
UNITS = {"00060": "ft^3/s", "00065": "ft", "00010": "degC"}
# USGS qualifiers for readings that are not real measurements (ice, equipment malfunction, maintenance, seasonal/discontinued).
UNRELIABLE = {"ice", "eqp", "mnt", "ssn", "dis", "fld"}
PAGE_LIMIT = 10000
BACKFILL_EVERY_HOURS = 6  # a gauge that can never reach two days of history must not trigger a week-long fetch every poll
MAX_PAGES = 12
LATEST_MAX_AGE_DAYS = 3  # `latest-continuous` returns the newest value of every series, even a sensor that stopped years ago
GAP_AFTER_HOURS = 1.5  # the newest reading is older than this: fetch the missing stretch


class ParseError(Exception):
    pass


def url_for(site_nos: list[str], period: str | None = None, parameters: tuple[str, ...] = tuple(PARAMS)) -> str:
    """period None = latest value of each series; otherwise an ISO-8601 duration such as PT6H or P7D."""
    ids = ",".join(f"USGS-{s}" for s in sorted(site_nos))
    collection = "continuous" if period else "latest-continuous"
    q = f"f=json&monitoring_location_id={ids}&parameter_code={','.join(parameters)}&limit={PAGE_LIMIT}"
    return f"{BASE}/{collection}/items?{q}" + (f"&time={period}" if period else "")


def _collection(body: bytes | str) -> dict:
    try:
        d = json.loads(body)
    except ValueError as exc:
        raise ParseError(f"USGS payload is not JSON: {exc}") from exc
    if not isinstance(d, dict) or d.get("type") != "FeatureCollection" or not isinstance(d.get("features"), list):
        # The API reports errors as {"code": ..., "description": ...} with a 4xx, but never trust the shape.
        raise ParseError(f"unexpected USGS payload: {str(d.get('description') or d.get('code') or list(d)[:4])[:120] if isinstance(d, dict) else type(d)}")
    return d


def next_link(body: bytes | str) -> str | None:
    try:
        d = json.loads(body)
        return next((l["href"] for l in d.get("links", []) if l.get("rel") == "next" and l.get("href")), None)
    except (ValueError, AttributeError, TypeError):
        return None


def parse(body: bytes | str, newer_than: datetime | None = None) -> list[dict]:
    """GeoJSON from `continuous` or `latest-continuous` -> readings. Pure function of the stored body.
    newer_than drops older readings (for latest-mode, where a dead sensor's last value can be years old)."""
    out = []
    for f in _collection(body)["features"]:
        p = f.get("properties") or {}
        loc = str(p.get("monitoring_location_id") or "")
        agency, _, site = loc.partition("-")
        code = p.get("parameter_code")
        if agency != "USGS" or not site or code not in PARAMS:
            continue
        if p.get("unit_of_measure") != UNITS[code]:
            continue
        q = p.get("qualifier")
        if q and any(tok in UNRELIABLE for tok in str(q).lower().replace(",", " ").split()):
            continue
        try:
            val = float(p["value"])
            t = datetime.fromisoformat(p["time"]).astimezone(timezone.utc).isoformat(timespec="minutes")
        except (KeyError, TypeError, ValueError):
            continue  # no value (a gap), or an unparseable one
        if newer_than and datetime.fromisoformat(t) < newer_than:
            continue
        out.append({"site_no": site, "parameter": PARAMS[code], "value": val, "observed_at": t,
                    "provisional": int(str(p.get("approval_status", "")).lower() != "approved")})
    return out


def needs_backfill(session: Session) -> bool:
    """True if any gauge has under two days of history (first run, or a new gauge): the flow factor
    needs a baseline, so pull a week once instead of the usual latest values."""
    for g in session.scalars(select(Gauge).where(Gauge.agency == "USGS")):
        lo, hi = session.execute(select(func.min(GaugeReading.observed_at), func.max(GaugeReading.observed_at))
                                 .where(GaugeReading.gauge_id == g.id, GaugeReading.parameter == "discharge_cfs")).one()
        if lo is None or (datetime.fromisoformat(hi) - datetime.fromisoformat(lo)).days < 2:
            return True
    return False


def _backfilled_recently(session: Session, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    last = session.scalar(select(func.max(RawFetch.fetched_at)).where(RawFetch.source == SOURCE, RawFetch.url.like("%time=P7D%")))
    return bool(last) and (now - datetime.fromisoformat(last)).total_seconds() < BACKFILL_EVERY_HOURS * 3600


def gap_period(session: Session, now: datetime | None = None) -> str | None:
    """An ISO duration covering the stretch since the stalest gauge last reported, or None if nothing is stale."""
    now = now or datetime.now(timezone.utc)
    worst = 0.0
    for g in session.scalars(select(Gauge).where(Gauge.agency == "USGS")):
        hi = session.scalar(select(func.max(GaugeReading.observed_at)).where(GaugeReading.gauge_id == g.id, GaugeReading.parameter == "discharge_cfs"))
        if hi:
            worst = max(worst, (now - datetime.fromisoformat(hi)).total_seconds() / 3600)
    return f"PT{min(24, ceil(worst) + 1)}H" if worst > GAP_AFTER_HOURS else None


def _store(session: Session, gauges: dict, rows: list[dict]) -> int:
    inserted = 0
    for r in rows:
        g = gauges.get(r["site_no"])
        if g is not None and session.get(GaugeReading, (g.id, r["parameter"], r["observed_at"])) is None:
            session.add(GaugeReading(gauge_id=g.id, parameter=r["parameter"], value=r["value"],
                                     observed_at=r["observed_at"], provisional=r["provisional"]))
            inserted += 1
    return inserted


def run_job(session: Session, fetch: Fetcher = http_fetch, period: str | None = None) -> dict:
    gauges = {g.site_no: g for g in session.scalars(select(Gauge).where(Gauge.agency == "USGS"))}
    if not gauges:
        return {"ok": True, "inserted": 0}
    if get_settings().usgs_api == "legacy":
        return _run_legacy(session, fetch, gauges, period)
    params: tuple[str, ...] = tuple(PARAMS)
    if period is None:
        if needs_backfill(session) and not _backfilled_recently(session):
            period, params = "P7D", ("00060",)
        else:
            period = gap_period(session)  # None: just the latest values
    url, inserted, ok = url_for(list(gauges), period, params), 0, True
    cutoff = datetime.now(timezone.utc) - timedelta(days=LATEST_MAX_AGE_DAYS) if period is None else None
    for _ in range(MAX_PAGES):
        status, body = fetch(url)
        raw, _ = store_fetch(session, SOURCE, url, status, body)
        if status != 200:
            raw.parse_ok, raw.error, ok = 0, f"HTTP {status}", False
            break
        try:
            rows = parse(body, cutoff)
        except ParseError as exc:
            raw.parse_ok, raw.error, ok = 0, str(exc), False
            break
        inserted += _store(session, gauges, rows)
        raw.parse_ok = 1
        url = next_link(body)
        if not url:
            break
    session.commit()
    return {"ok": ok, "inserted": inserted}


# ---- legacy waterservices (deprecated: delete after USGS retires it, early 2027) ----------------------------------------

def url_for_legacy(site_nos: list[str], period: str = "PT6H") -> str:
    return f"{LEGACY_BASE}?format=json&sites={','.join(sorted(site_nos))}&parameterCd={','.join(PARAMS)}&period={period}&siteStatus=all"


def parse_legacy(body: bytes | str) -> list[dict]:
    try:
        d = json.loads(body)
        series = d["value"]["timeSeries"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"unexpected USGS payload: {exc}") from exc
    out = []
    for ts in series:
        site = ts["sourceInfo"]["siteCode"][0]["value"]
        code = ts["variable"]["variableCode"][0]["value"]
        if code not in PARAMS:
            continue
        nodata = float(ts["variable"].get("noDataValue", -999999))
        for block in ts["values"]:
            for v in block["value"]:
                try:
                    val = float(v["value"])
                except (TypeError, ValueError):
                    continue  # e.g. 'Ice', 'Eqp'
                if val == nodata:
                    continue
                t = datetime.fromisoformat(v["dateTime"]).astimezone(timezone.utc).isoformat(timespec="minutes")
                out.append({"site_no": site, "parameter": PARAMS[code], "value": val, "observed_at": t,
                            "provisional": int("P" in v.get("qualifiers", []))})
    return out


def _run_legacy(session: Session, fetch: Fetcher, gauges: dict, period: str | None) -> dict:
    period = period or ("P7D" if needs_backfill(session) else "PT6H")
    url = url_for_legacy(list(gauges), period)
    status, body = fetch(url)
    raw, _ = store_fetch(session, SOURCE, url, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False, "inserted": 0}
    try:
        rows = parse_legacy(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False, "inserted": 0}
    inserted = _store(session, gauges, rows)
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "inserted": inserted}
