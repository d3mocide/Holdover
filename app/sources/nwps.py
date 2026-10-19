"""NOAA National Water Prediction Service (NWPS): the official flood category of river gauges.

Read from the public NWPS gauges API (no key). It is not guaranteed stable. Only the category NOAA publishes is
shown (no flooding, action, minor, moderate, major) and, when NOAA has a current forecast, its forecast category and
crest stage. Holdover does not compute stages or say what a category means for a river or a road: it links to NWPS.
A gauge with no flood stages defined shows nothing, and an observation that is not current is not shown as current.
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import RawFetch, RiverStatus

SOURCE = "nwps"
URL = "https://api.water.noaa.gov/nwps/v1/gauges?bbox.xmin=-124.8&bbox.ymin=41.9&bbox.xmax=-116.4&bbox.ymax=46.4&srid=EPSG_4326"  # all of Oregon, about 380 KB
PAGE = "https://water.noaa.gov/gauges/{lid}"
# USGS site number -> NWPS gauge id. Each pair was checked by name and by position (all within 120 m) against the live
# response on 2026-10-18. 14150000 (Dexter) and 14153500 (Cottage Grove Dam) are left out: NWPS's nearest gauges there are
# reservoir gauges, not the river points.
LIDS = {
    "14166000": "HARO3", "14174000": "ALBO3", "14191000": "SLMO3", "14152000": "JASO3", "14157500": "GOSO3",
    "14162500": "VIDO3", "14163150": "MKLO3", "14165500": "MRGO3", "14178000": "BCKO3", "14179000": "BRBO3",
    "14181500": "BCLO3", "14203500": "DLLO3", "14207500": "WSLO3", "14183000": "MEHO3", "14185900": "QCCO3", "14210000": "ESTO3",
    # the popular rivers (checked 2026-10-19: each NWPS gauge is within 400 m of its USGS gauge and has the same name)
    "11501000": "CHSO3",
    "11502500": "WMSO3",
    "11509500": "KEOO3",
    "13181000": "ROMO3",
    "13233300": "VALO3",
    "13333000": "TRYO3",
    "14033500": "UMAO3",
    "14038530": "JHNO3",
    "14046000": "MONO3",
    "14092500": "PERO3",
    "14103000": "MODO3",
    "14120000": "HODO3",
    "14137000": "SRMO3",
    "14142500": "SNDO3",
    "14173500": "CPAO3",
    "14187500": "WTLO3",
    "14200000": "CANO3",
    "14209500": "TLYO3",
    "14301000": "FSSO3",
    "14301500": "TLMO3",
    "14302480": "TRAO3",
    "14303600": "BEAO3",
    "14305500": "SILO3",
    "14306500": "TIDO3",
    "14307620": "MPLO3",
    "14312330": "SUMO3",
    "14319500": "WNRO3",
    "14321000": "EKTO3",
    "14339000": "EGLO3",
    "14361500": "GRAO3",
    "14369500": "ARWO3",
    "14400000": "CHTO3",
}
LABELS = {"no_flooding": "No flooding", "action": "Action stage (near flood stage)", "minor": "Minor flooding",
          "moderate": "Moderate flooding", "major": "Major flooding"}
MAX_AGE = timedelta(hours=6)  # an observation older than this is not shown as the current category


class ParseError(Exception):
    pass


def _v(x):
    """NWPS uses -999 for 'no value'."""
    return None if x is None or x == -999 else x


def parse(body: bytes | str) -> dict[str, dict]:
    """{lid: {category, stage_ft, flow_kcfs, valid_time, fc_category, fc_stage_ft, fc_valid_time}} for the gauges we map."""
    try:
        data = json.loads(body)
        if "error" in data:
            raise ValueError("service error")
        wanted, out = set(LIDS.values()), {}
        for g in data["gauges"]:
            if g["lid"] not in wanted:
                continue
            ob, fc = g["status"]["observed"], g["status"]["forecast"]
            fc_ok = fc.get("floodCategory") in LABELS and _v(fc.get("primary")) is not None
            out[g["lid"]] = {
                "category": ob.get("floodCategory"), "stage_ft": _v(ob.get("primary")) if ob.get("primaryUnit") == "ft" else None,
                "flow_kcfs": _v(ob.get("secondary")) if ob.get("secondaryUnit") == "kcfs" else None, "valid_time": ob.get("validTime"),
                "fc_category": fc["floodCategory"] if fc_ok else None,
                "fc_stage_ft": _v(fc.get("primary")) if fc_ok and fc.get("primaryUnit") == "ft" else None,
                "fc_valid_time": fc.get("validTime") if fc_ok else None}
        if not out:
            raise ValueError("none of the mapped gauges were present")
        return out
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ParseError(f"unexpected NWPS payload: {exc}") from exc


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    status, body = fetch(URL)
    raw, _ = store_fetch(session, SOURCE, URL, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return {"ok": False}
    try:
        rows = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return {"ok": False}
    for lid, r in rows.items():
        session.add(RiverStatus(lid=lid, raw_fetch_id=raw.id, **r))
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "gauges": len(rows)}


def for_site(session: Session, site_no: str, now: datetime | None = None) -> dict | None:
    """Flood status for a USGS site, from the newest successful fetch. None when the gauge is not mapped, has no flood
    stages, or nothing was fetched."""
    lid = LIDS.get(site_no)
    raw = session.scalar(select(RawFetch).where(RawFetch.source == SOURCE, RawFetch.parse_ok == 1).order_by(RawFetch.id.desc()).limit(1))
    if lid is None or raw is None:
        return None
    r = session.scalar(select(RiverStatus).where(RiverStatus.lid == lid, RiverStatus.raw_fetch_id == raw.id))
    if r is None or r.category not in LABELS:
        return None  # not_defined, out_of_service, obs_not_current ...: nothing to say
    now = now or datetime.now(timezone.utc)
    stale = r.valid_time is None or now - datetime.fromisoformat(r.valid_time.replace("Z", "+00:00")) > MAX_AGE
    return {"category": r.category, "label": LABELS[r.category], "stage_ft": r.stage_ft, "as_of": r.valid_time, "stale": stale,
            "forecast": {"category": r.fc_category, "label": LABELS[r.fc_category], "stage_ft": r.fc_stage_ft, "valid_time": r.fc_valid_time}
            if r.fc_category else None,
            "elevated": r.category != "no_flooding", "page": PAGE.format(lid=lid)}
