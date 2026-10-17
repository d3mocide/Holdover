"""ODFW weekly Recreation Report (https://myodfw.com/recreation-report).

The page is a single rich-text block: an intro, then "Best bets for weekend fishing" with a
"<Name> Zone -" paragraph followed by a bullet list per zone. parse() is pure.
"""
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import RawFetch, Report

SOURCE = "odfw_report"
URL = "https://myodfw.com/recreation-report"

_ZONE_HEAD = re.compile(r"^\s*(?P<name>[A-Za-z ]{2,20}?)\s+Zone\s*[-–—:]?\s*$")
_DATE = re.compile(r"^\s*([A-Z][a-z]+ \d{1,2}, \d{4})\s*$")
_ZONE_KEYS = {"nw": "nw", "northwest": "nw", "ne": "ne", "northeast": "ne", "se": "se", "southeast": "se",
              "sw": "sw", "southwest": "sw", "central": "central", "willamette": "willamette"}


class ParseError(Exception):
    pass


@dataclass
class ParsedReport:
    issued_on: str  # ISO date
    intro: str = ""
    zones: dict[str, list[str]] = field(default_factory=dict)  # zone key -> bullet texts

    def zone_text(self, zone: str) -> str:
        return "\n".join(self.zones.get(zone, []))


def _iso(text: str) -> str:
    from datetime import datetime
    return datetime.strptime(text, "%B %d, %Y").date().isoformat()


def parse(body: bytes | str) -> ParsedReport:
    html = body.decode("utf-8", "replace") if isinstance(body, bytes) else body
    soup = BeautifulSoup(html, "html.parser")
    block = soup.find(class_="field--name-description")
    if block is None:
        raise ParseError("report body block not found")
    date_node = soup.find(string=_DATE)
    if date_node is None:
        raise ParseError("issue date not found")
    out = ParsedReport(issued_on=_iso(_DATE.match(date_node).group(1)))
    current = None
    intro = []
    for el in block.find_all(["p", "ul"]):
        text = el.get_text(" ", strip=True)
        if el.name == "p":
            m = _ZONE_HEAD.match(text)
            if m and m.group("name").lower() in _ZONE_KEYS:
                current = _ZONE_KEYS[m.group("name").lower()]
                out.zones.setdefault(current, [])
                continue
            if current is None and text:
                intro.append(text)
        elif el.name == "ul" and current is not None:
            out.zones[current].extend(li.get_text(" ", strip=True) for li in el.find_all("li") if li.get_text(strip=True))
            current = None  # a zone's list ends at its <ul>; later lists are unrelated promos
    if not out.zones:
        raise ParseError("no zone sections found")
    out.intro = "\n".join(intro)
    return out


def ingest(session: Session, url: str, status: int | None, body: bytes) -> list[Report]:
    """Store raw, parse, and create one `report` row per zone. Parse failures mark the source stale."""
    raw, unchanged = store_fetch(session, SOURCE, url, status, body)
    if status != 200:
        raw.parse_ok, raw.error = 0, f"HTTP {status}"
        session.commit()
        return []
    if unchanged:
        raw.parse_ok = 1
        session.commit()
        return []
    try:
        parsed = parse(body)
    except ParseError as exc:
        raw.parse_ok, raw.error = 0, str(exc)
        session.commit()
        return []
    made = []
    for zone in parsed.zones:
        exists = session.scalar(select(Report.id).where(Report.zone == zone, Report.issued_on == parsed.issued_on,
                                                        Report.raw_fetch_id == raw.id))
        if exists is None:
            r = Report(raw_fetch_id=raw.id, zone=zone, issued_on=parsed.issued_on)
            session.add(r)
            made.append(r)
    raw.parse_ok = 1
    session.commit()
    return made


def report_text(session: Session, report: Report) -> str:
    """The verbatim zone text for a stored report (re-derived from the stored raw body)."""
    raw = session.get(RawFetch, report.raw_fetch_id)
    return parse(raw.body).zone_text(report.zone)


def run_job(session: Session, fetch: Fetcher = http_fetch) -> dict:
    status, body = fetch(URL)
    made = ingest(session, URL, status, body)
    last = session.scalar(select(RawFetch).where(RawFetch.source == SOURCE).order_by(RawFetch.id.desc()).limit(1))
    return {"ok": bool(last and last.parse_ok == 1), "new_reports": len(made)}
