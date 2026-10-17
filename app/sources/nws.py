"""NWS forecast (api.weather.gov). Needs the identifying User-Agent. A waterbody's grid lookup and
forecasts are cached in forecast_cache; a failed refresh leaves the old cache in place."""
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, now_iso, store_fetch
from app.models import ForecastCache, Waterbody

SOURCE = "nws"
POINTS = "https://api.weather.gov/points/{lat:.4f},{lon:.4f}"


class ParseError(Exception):
    pass


def parse_points(body: bytes | str) -> dict:
    try:
        p = json.loads(body)["properties"]
        return {"forecast": p["forecast"], "hourly": p["forecastHourly"], "grid": f'{p["gridId"]}/{p["gridX"]},{p["gridY"]}'}
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"unexpected NWS points payload: {exc}") from exc


def parse_periods(body: bytes | str, limit: int) -> tuple[list[dict], str | None]:
    try:
        p = json.loads(body)["properties"]
        periods = p["periods"][:limit]
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError(f"unexpected NWS forecast payload: {exc}") from exc
    out = [{
        "name": x.get("name"), "start": x["startTime"], "end": x["endTime"], "daytime": x.get("isDaytime"),
        "temp_f": x.get("temperature"), "precip_pct": (x.get("probabilityOfPrecipitation") or {}).get("value"),
        "wind": x.get("windSpeed"), "wind_dir": x.get("windDirection"), "short": x.get("shortForecast"),
        "detail": x.get("detailedForecast"),
    } for x in periods]
    return out, p.get("updateTime") or p.get("updated")


def refresh(session: Session, wb: Waterbody, fetch: Fetcher = http_fetch) -> dict | None:
    """Fetch and cache a forecast. Returns the payload, or None (cache untouched) on any failure."""
    if wb.lat is None or wb.lon is None:
        return None
    steps = []
    url = POINTS.format(lat=wb.lat, lon=wb.lon)
    for u, kind in [(url, "points")]:
        status, body = fetch(u)
        raw, _ = store_fetch(session, SOURCE, u, status, body)
        steps.append((raw, kind, status, body))
        if status != 200:
            raw.parse_ok, raw.error = 0, f"HTTP {status}"
            session.commit()
            return None
    try:
        pts = parse_points(steps[0][3])
    except ParseError as exc:
        steps[0][0].parse_ok, steps[0][0].error = 0, str(exc)
        session.commit()
        return None
    steps[0][0].parse_ok = 1
    payload = {"grid": pts["grid"], "fetched_at": now_iso()}
    for key, limit in [("forecast", 14), ("hourly", 36)]:
        status, body = fetch(pts[key])
        raw, _ = store_fetch(session, SOURCE, pts[key], status, body)
        if status != 200:
            raw.parse_ok, raw.error = 0, f"HTTP {status}"
            session.commit()
            return None
        try:
            payload[key], payload[f"{key}_updated"] = parse_periods(body, limit)
        except ParseError as exc:
            raw.parse_ok, raw.error = 0, str(exc)
            session.commit()
            return None
        raw.parse_ok = 1
    session.add(ForecastCache(waterbody_id=wb.id, fetched_at=payload["fetched_at"], payload_json=json.dumps(payload)))
    session.commit()
    return payload


def cached(session: Session, wb_id: int) -> dict | None:
    row = session.scalar(select(ForecastCache).where(ForecastCache.waterbody_id == wb_id)
                         .order_by(ForecastCache.fetched_at.desc()).limit(1))
    return json.loads(row.payload_json) if row else None


def age_hours(fetched_at: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds() / 3600


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    ok = fail = 0
    for wb in session.scalars(select(Waterbody).where(Waterbody.starred == 1)):
        if refresh(session, wb, fetch):
            ok += 1
        else:
            fail += 1
    return {"ok": fail == 0, "refreshed": ok, "failed": fail}
