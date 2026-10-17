"""USGS Instantaneous Values (legacy waterservices endpoint, verified live 2026-10-17).

Keyless and public domain, but every value is PROVISIONAL (qualifier 'P') and the UI must say so.
USGS is migrating its Water Data APIs; this adapter is the only place that knows the URL shape.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import Gauge, GaugeReading

SOURCE = "usgs"
BASE = "https://waterservices.usgs.gov/nwis/iv/"
PARAMS = {"00060": "discharge_cfs", "00065": "gage_height_ft", "00010": "water_temp_c"}


class ParseError(Exception):
    pass


def url_for(site_nos: list[str], period: str = "PT6H") -> str:
    return f"{BASE}?format=json&sites={','.join(sorted(site_nos))}&parameterCd={','.join(PARAMS)}&period={period}&siteStatus=all"


def parse(body: bytes | str) -> list[dict]:
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


def run_job(session: Session, fetch: Fetcher = http_fetch, period: str = "PT6H") -> dict:
    gauges = {g.site_no: g for g in session.scalars(select(Gauge).where(Gauge.agency == "USGS"))}
    if not gauges:
        return {"ok": True, "inserted": 0}
    url = url_for(list(gauges), period)
    status, body = fetch(url)
    raw, _ = store_fetch(session, SOURCE, url, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False, "inserted": 0}
    try:
        rows = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False, "inserted": 0}
    inserted = 0
    for r in rows:
        g = gauges.get(r["site_no"])
        if g is None:
            continue
        if session.get(GaugeReading, (g.id, r["parameter"], r["observed_at"])) is None:
            session.add(GaugeReading(gauge_id=g.id, parameter=r["parameter"], value=r["value"],
                                     observed_at=r["observed_at"], provisional=r["provisional"]))
            inserted += 1
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "inserted": inserted}
