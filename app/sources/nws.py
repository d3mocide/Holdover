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


def forecast_points(session: Session) -> list[Waterbody]:
    """Every user's favorite waterbodies, plus one river or stocked waterbody per ~0.25 degree cell so the planner has a
    nearby forecast for every spot without one NWS call per waterbody."""
    from app.models import Favorite, StockingSnapshot, WaterbodyAlias
    starred = list(session.scalars(select(Waterbody).where(
        Waterbody.id.in_(select(Favorite.waterbody_id)) | (Waterbody.starred == 1)).order_by(Waterbody.id)))
    stocked_ids = {r for r in session.scalars(
        select(WaterbodyAlias.waterbody_id).join(StockingSnapshot, StockingSnapshot.alias_id == WaterbodyAlias.id)
        .where(WaterbodyAlias.confirmed == 1)) if r}
    seen = {(round(w.lat * 4), round(w.lon * 4)) for w in starred if w.lat is not None}
    out = list(starred)
    for wb in session.scalars(select(Waterbody).where((Waterbody.id.in_(stocked_ids)) | (Waterbody.kind == "river")).order_by(Waterbody.id)):
        if wb.lat is None or wb.lon is None:
            continue
        cell = (round(wb.lat * 4), round(wb.lon * 4))
        if cell not in seen:
            seen.add(cell)
            out.append(wb)
    return out


def nearest_cached(session: Session, lat: float, lon: float, max_km: float = 30) -> tuple[dict, float] | None:
    from app.scoring import haversine_km
    from app.conditions import FORECAST_STALE_H
    best = None
    for wb in session.scalars(select(Waterbody)):
        if wb.lat is None or wb.lon is None:
            continue
        d = haversine_km(lat, lon, wb.lat, wb.lon)
        if d <= max_km:
            payload = cached(session, wb.id)
            if payload:
                # Prefer a current area forecast over a closer expired cache.
                rank = (age_hours(payload["fetched_at"]) > FORECAST_STALE_H, d)
                if best is None or rank < best[2]:
                    best = (payload, d, rank)
    return best[:2] if best else None


def area_cached(session: Session, wb: Waterbody) -> tuple[dict, float] | None:
    """Same bounded area forecast for cards and rankings; never infer a location for unpinned waters."""
    if wb.lat is not None and wb.lon is not None:
        return nearest_cached(session, wb.lat, wb.lon)
    payload = cached(session, wb.id)
    return (payload, 0) if payload else None


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    ok = fail = 0
    for wb in forecast_points(session):
        if refresh(session, wb, fetch):
            ok += 1
        else:
            fail += 1
    return {"ok": fail == 0, "refreshed": ok, "failed": fail}
