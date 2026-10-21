"""Informational seasonal context; never feeds the fishing score or LLM facts."""
import json
import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.models import FlowBaseline, Gauge, GaugeReading, WaterbodyGauge
from app.config import get_settings

REFERENCE = date(2000, 1, 1)  # leap calendar preserves month/day, including Feb 29
WINDOW = 7


def index(day):
    return (date(2000, day.month, day.day) - REFERENCE).days


def quantile(values, fraction):
    position = (len(values) - 1) * fraction
    low = math.floor(position)
    return round(values[low] + (values[math.ceil(position)] - values[low]) * (position - low), 2)


def build_baseline(values, start, end):
    buckets = [[] for _ in range(366)]
    expected = [0] * 366
    day = date(start, 1, 1)
    while day <= date(end, 12, 31):
        value = values.get(day.isoformat())
        for offset in range(-WINDOW, WINDOW + 1):
            target = (index(day) + offset) % 366
            expected[target] += 1
            if value is not None:
                buckets[target].append((value, day.year))
        day += timedelta(days=1)
    points = {}
    for i, rows in enumerate(buckets):
        nums = sorted(v for v, _ in rows)
        years = sorted({y for _, y in rows})
        enough = len(nums) >= 75 and len(years) >= 5
        points[(REFERENCE + timedelta(days=i)).strftime("%m-%d")] = {
            "samples": len(nums), "expected": expected[i], "years": years,
            "p25": quantile(nums, .25) if enough else None, "median": quantile(nums, .5) if enough else None,
            "p75": quantile(nums, .75) if enough else None}
    return {"start_year": start, "end_year": end, "window_days": 15, "approved_days": len(values), "points": points}


def for_gauge(session, gauge, day, span=30):
    now = datetime.now(timezone.utc)
    cache = session.get(FlowBaseline, gauge.id)
    out = {"gauge": {"id": gauge.id, "name": gauge.name, "site_no": gauge.site_no}, "date": day.isoformat(),
           "as_of": cache.fetched_at if cache else None, "stale": True, "status": "pending", "current": None, "series": []}
    if not cache or not cache.payload_json:
        out["status"] = "unavailable" if cache and cache.error else "pending" if get_settings().usgs_api_key else "disabled"
        return out
    payload = json.loads(cache.payload_json)
    out.update({k: payload[k] for k in ("start_year", "end_year", "window_days", "approved_days")})
    fetched = datetime.fromisoformat(cache.fetched_at)
    out["stale"] = bool(cache.error) or fetched > now or now - fetched > timedelta(days=45) or payload["end_year"] != now.year - 1
    out["selected"] = payload["points"][day.strftime("%m-%d")]
    out["status"] = "ready" if out["selected"]["median"] is not None else "insufficient"
    if span:
        out["series"] = [{"date": (day + timedelta(days=i)).isoformat(), **payload["points"][(day + timedelta(days=i)).strftime("%m-%d")]}
                         for i in range(max(-span, (date.min - day).days), min(span, (date.max - day).days) + 1)]
    reading = session.scalar(select(GaugeReading).where(GaugeReading.gauge_id == gauge.id,
        GaugeReading.parameter == "discharge_cfs", GaugeReading.observed_at <= now.isoformat()).order_by(GaugeReading.observed_at.desc()).limit(1))
    if reading and math.isfinite(reading.value) and reading.value >= 0:
        when = datetime.fromisoformat(reading.observed_at)
        observed_day = when.astimezone(ZoneInfo("America/Los_Angeles")).date()
        baseline = payload["points"][observed_day.strftime("%m-%d")]
        stale = now - when > timedelta(hours=3)
        position = None
        if not stale and not out["stale"] and baseline["median"] is not None:
            position = "below the middle 50%" if reading.value < baseline["p25"] else "above the middle 50%" if reading.value > baseline["p75"] else "within the middle 50%"
        out["current"] = {"value": reading.value, "observed_at": reading.observed_at, "date": observed_day.isoformat(),
                          "stale": stale, "position": position, "baseline": baseline, "provisional": True}
    return out


def for_water(session, wb_id, day):
    gauge = session.scalar(select(Gauge).join(WaterbodyGauge, WaterbodyGauge.gauge_id == Gauge.id)
        .where(WaterbodyGauge.waterbody_id == wb_id, Gauge.agency == "USGS").order_by(Gauge.site_no).limit(1))
    return for_gauge(session, gauge, day, span=0) if gauge else None
