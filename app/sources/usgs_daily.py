"""Approved USGS daily mean discharge, cached monthly. One gauge per job; raw pages precede parsing.
Baseline maths and presentation live in app/seasonal.py. No request-time source fetches."""
import json
import math
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

from sqlalchemy import select

from app.http import http_fetch, store_fetch, now_iso
from app.config import get_settings
from app.models import FlowBaseline, Gauge, Waterbody, WaterbodyGauge
from app.sources.usgs import BASE, ParseError, UNRELIABLE, _collection, next_link

SOURCE = "usgs_daily"
REFRESH_DAYS = 30


def fetch_daily(url):
    return http_fetch(url, api_key=get_settings().usgs_api_key)


def url_for(site, start, end):
    return f"{BASE}/daily/items?" + urlencode({"f": "json", "monitoring_location_id": f"USGS-{site}",
        "parameter_code": "00060", "statistic_id": "00003", "datetime": f"{start}-01-01/{end}-12-31", "limit": 10000})


def parse(body, site, start, end):
    out = {}
    for feature in _collection(body)["features"]:
        if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
            raise ParseError("unexpected daily feature")
        p = feature["properties"]
        if p.get("monitoring_location_id") != f"USGS-{site}" or p.get("parameter_code") != "00060" or p.get("statistic_id") != "00003":
            continue
        if p.get("unit_of_measure") != "ft^3/s":
            raise ParseError("unexpected discharge unit")
        if str(p.get("approval_status", "")).lower() != "approved":
            continue
        qualifiers = p.get("qualifier") or []
        if not isinstance(qualifiers, list):
            qualifiers = [qualifiers]
        if any(q in UNRELIABLE for value in qualifiers for q in str(value).lower().replace(",", " ").split()):
            continue
        try:
            day = date.fromisoformat(p["time"])
            value = float(p["value"])
        except (ValueError, KeyError, TypeError):
            continue
        if not start <= day.year <= end or not math.isfinite(value) or value < 0:
            continue
        key = day.isoformat()
        if key in out and out[key] != value:
            raise ParseError("conflicting daily means")
        out[key] = value
    return out


def refresh(session, gauge, fetch=fetch_daily, today=None):
    from app.seasonal import build_baseline
    if fetch is fetch_daily and not get_settings().usgs_api_key:
        return {"ok": True, "skipped": "USGS_API_KEY is required for historical downloads"}
    today = today or date.today()
    start, end = today.year - 10, today.year - 1
    cache = session.get(FlowBaseline, gauge.id)
    if cache is None:
        cache = FlowBaseline(gauge_id=gauge.id, attempted_at=now_iso())
        session.add(cache)
    cache.attempted_at = now_iso()
    url, values, seen = url_for(gauge.site_no, start, end), {}, set()
    returned, expected = 0, 0
    raw = None
    try:
        for _ in range(3):
            if url in seen or urlsplit(url).netloc != "api.waterdata.usgs.gov" or urlsplit(url).scheme != "https" or urlsplit(url).path != "/ogcapi/v1/collections/daily/items":
                raise ParseError("invalid daily pagination link")
            seen.add(url)
            status, body = fetch(url)
            raw, _ = store_fetch(session, SOURCE, url, status, body)
            if status != 200:
                raise ParseError(f"HTTP {status}")
            collection = _collection(body)
            returned += len(collection["features"])
            if isinstance(collection.get("numberMatched"), int):
                expected = max(expected, collection["numberMatched"])
            page = parse(body, gauge.site_no, start, end)
            for key, value in page.items():
                if key in values and values[key] != value:
                    raise ParseError("conflicting daily pages")
                values[key] = value
            raw.parse_ok = 1
            url = next_link(body)
            if not url:
                break
        if url or returned < expected:
            raise ParseError("daily pagination incomplete")
        if not values and cache.payload_json and json.loads(cache.payload_json)["approved_days"]:
            raise ParseError("empty approved baseline; retaining last good data")
        cache.payload_json = json.dumps(build_baseline(values, start, end), separators=(",", ":"))
        cache.fetched_at, cache.error = now_iso(), None
        session.commit()
        return {"ok": True, "site_no": gauge.site_no, "days": len(values)}
    except (ParseError, ValueError) as exc:
        if raw is not None:
            raw.parse_ok, raw.error = 0, str(exc)
        cache.error = str(exc)
        session.commit()
        return {"ok": False, "site_no": gauge.site_no, "error": str(exc)}


def run_job(session, fetch=fetch_daily):
    if fetch is fetch_daily and not get_settings().usgs_api_key:
        return {"ok": True, "skipped": "USGS_API_KEY is required for historical downloads"}
    gauges = session.scalars(select(Gauge).join(WaterbodyGauge, WaterbodyGauge.gauge_id == Gauge.id)
        .join(Waterbody, Waterbody.id == WaterbodyGauge.waterbody_id)
        .where(Gauge.agency == "USGS", Waterbody.kind == "river").distinct().order_by(Gauge.site_no)).all()
    now = datetime.now(timezone.utc)
    pending = []
    for gauge in gauges:
        cache = session.get(FlowBaseline, gauge.id)
        if cache and now - datetime.fromisoformat(cache.attempted_at) < timedelta(days=1):
            continue
        if cache and not cache.error and cache.fetched_at and now - datetime.fromisoformat(cache.fetched_at) < timedelta(days=REFRESH_DAYS):
            payload = json.loads(cache.payload_json)
            if payload["end_year"] == now.year - 1:
                continue
        pending.append((cache.attempted_at if cache else "", gauge))
    if not pending:
        return {"ok": True, "skipped": "baselines are current or retry is deferred"}
    return refresh(session, min(pending, key=lambda item: (item[0], item[1].site_no))[1], fetch)
