"""ODFW weekly trout stocking schedule (myodfw.com).

parse() is a pure function of the stored body. The page lists the *week* of a stocking, not a day,
and ODFW says the schedule can change without notice.
"""
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.http import Fetcher, http_fetch, now_iso, store_fetch
from app.matching import resolve_alias
from app.models import RawFetch, StockingSnapshot

SOURCE = "odfw_stocking"
BASE = "https://myodfw.com/fishing/species/trout/stocking-schedule"
MAX_PAGES = 12
PAGE_DELAY_S = 2.0

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DATE = re.compile(r"([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{1,2}),\s*(\d{4})")


class ParseError(Exception):
    pass


@dataclass
class StockingRow:
    week_of: str  # Monday, YYYY-MM-DD
    waterbody_raw: str
    zone_office: str
    legals: int
    trophy: int
    brood: int
    fingerling: int
    total: int


def parse_week_start(text: str) -> date:
    """'Oct. 12, 2026 - Oct. 16, 2026' or 'Sep. 14, 2026-Sep. 18, 2026' -> the first date."""
    m = _DATE.search(text)
    if not m or m.group(1).lower() not in _MONTHS:
        raise ParseError(f"unrecognised week text: {text!r}")
    return date(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)))


def _int(text: str) -> int:
    t = text.replace(",", "").strip()
    return int(t) if t else 0


def parse(body: bytes | str, allow_missing_table: bool = False) -> list[StockingRow]:
    html = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="views-table")
    if table is None:
        # An empty result set renders no table; a changed layout must not look like "no stocking".
        if soup.find(class_=re.compile("view-empty|views-view")):
            return []
        if allow_missing_table:
            return []  # past the last page ODFW renders no table and no empty-state marker
        raise ParseError("stocking table not found")
    headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
    expected = ["Week of", "Waterbody", "Zone/Office", "Legals", "Trophy", "Brood", "Fingerling", "Total"]
    if headers != expected:
        raise ParseError(f"unexpected columns: {headers}")
    rows = []
    for tr in table.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if not tds:
            continue
        if len(tds) != 8:
            raise ParseError(f"row with {len(tds)} cells: {tds}")
        rows.append(StockingRow(
            week_of=parse_week_start(tds[0]).isoformat(), waterbody_raw=tds[1],
            zone_office=tds[2], legals=_int(tds[3]), trophy=_int(tds[4]), brood=_int(tds[5]),
            fingerling=_int(tds[6]), total=_int(tds[7]),
        ))
    return rows


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def page_url(page: int, today: date, zone: int | None = None) -> str:
    zone = zone if zone is not None else get_settings().stocking_zone_value
    start = monday_of(today) - timedelta(weeks=4)
    end = start + timedelta(weeks=60)
    q = {
        "field_zone_value": zone,
        "field_planned_stocking_date_value": start.isoformat(),
        "field_planned_stocking_date_end_value": end.isoformat(),
        "page": page,
    }
    return f"{BASE}?{urlencode(q)}"


def ingest_page(session: Session, url: str, status: int | None, body: bytes, page: int = 0) -> tuple[int, int]:
    """Store raw, parse, snapshot. Returns (rows_in_page, rows_inserted). Raises nothing:
    parse failures are recorded on the raw_fetch row so the source shows as stale."""
    raw, unchanged = store_fetch(session, SOURCE, url, status, body)
    if status != 200:
        raw.parse_ok = 0
        raw.error = f"HTTP {status}"
        session.commit()
        return 0, 0
    if unchanged:
        raw.parse_ok = 1
        session.commit()
        return -1, 0  # -1: identical to last good fetch, parse skipped
    try:
        rows = parse(body, allow_missing_table=page > 0)
    except ParseError as exc:
        raw.parse_ok = 0
        raw.error = str(exc)
        session.commit()
        return 0, 0
    scraped_at = now_iso()
    for r in rows:
        alias = resolve_alias(session, r.waterbody_raw, SOURCE)
        session.add(StockingSnapshot(
            raw_fetch_id=raw.id, scraped_at=scraped_at, week_of=r.week_of, alias_id=alias.id,
            zone_office=r.zone_office, legals=r.legals, trophy=r.trophy, brood=r.brood,
            fingerling=r.fingerling, total=r.total,
        ))
    raw.parse_ok = 1
    session.commit()
    return len(rows), len(rows)


def run_job(session: Session, fetch: Fetcher = http_fetch, today: date | None = None, zone: int | None = None) -> dict:
    """Walk one zone's result pages (50 rows each) until an empty page. One raw_fetch row per page."""
    today = today or datetime.now(timezone.utc).date()
    out = {"pages": 0, "rows_seen": 0, "rows_inserted": 0, "ok": True}
    for page in range(MAX_PAGES):
        url = page_url(page, today, zone)
        status, body = fetch(url)
        n, inserted = ingest_page(session, url, status, body, page)
        out["pages"] += 1
        out["rows_inserted"] += inserted
        if status != 200 or session.scalar(select(RawFetch.parse_ok).order_by(RawFetch.id.desc()).limit(1)) != 1:
            out["ok"] = False
            break
        if n == 0:
            break  # empty page: end of results
        out["rows_seen"] += max(n, 0)
        if fetch is http_fetch:
            time.sleep(PAGE_DELAY_S)
    return out


def run_zones(session: Session, fetch: Fetcher = http_fetch, today: date | None = None, zones=None) -> dict:
    """The scheduled job: every enabled zone, one after another with the usual pause between pages. A zone that fails does not stop the
    others; the result says which. Each zone is its own run of pages, so an unchanged zone costs the same few requests."""
    from app.zones import enabled
    zones = zones if zones is not None else enabled(get_settings().enabled_zones)
    out = {"pages": 0, "rows_seen": 0, "rows_inserted": 0, "ok": True, "zones": {}}
    for i, z in enumerate(zones):
        if i and fetch is http_fetch:
            time.sleep(PAGE_DELAY_S)
        r = run_job(session, fetch, today, zone=z.stocking_value)
        out["zones"][z.key] = {k: r[k] for k in ("pages", "rows_seen", "rows_inserted", "ok")}
        for k in ("pages", "rows_seen", "rows_inserted"):
            out[k] += r[k]
        out["ok"] = out["ok"] and r["ok"]
    return out
