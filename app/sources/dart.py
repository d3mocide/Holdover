"""Adult fish passage at Willamette Falls (the fishway at Oregon City), from Columbia River DART (University of Washington).

ODFW counts fish passing the fishway by video; DART republishes the daily counts as CSV with a ten-year average for each calendar day, and asks
users to credit ODFW and cite DART (see docs/sources.md). The Tualatin joins the Willamette above the falls, so fish headed for it, and for most of the
upper Willamette, pass this ladder. Counts lag by a few days (ODFW reviews the video on weekdays), are by day not by hour, and can be revised:
a changed count is stored as a new row and the newest wins, so nothing is overwritten.

A blank cell is ambiguous in DART's output (no fish, or not reported), so the parser keeps a day's blanks as zero only when the day has at least
one reported count, and drops a day with none. The wording in the app says how many days a figure covers.
"""
import csv
import io
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.http import Fetcher, http_fetch, store_fetch
from app.models import FishCount, RawFetch

SOURCE = "dart"
# DART's chain ends at a root (emSign ECC Root CA - G3) that the certifi bundle httpx uses lacks, but the operating system's store (Debian's, in the image)
# has it, so this host is fetched with the system store. Nothing is added to any trust store and verification is never turned off.
PROJECT = "WFF"
PROJECT_NAME = "Willamette Falls"
PAGE_URL = "https://www.cbr.washington.edu/dart/query/adult_daily"
# CSV column -> our species key. The 10-year average columns are the same name plus "10Yr".
COLUMNS = {"Chin": "chinook", "JChin": "jack_chinook", "Stlhd": "steelhead", "WStlhd": "wild_steelhead", "Coho": "coho", "JCoho": "jack_coho",
           "Sock": "sockeye", "Shad": "shad", "LmpryDay": "lamprey", "BTrout": "bull_trout", "Chum": "chum", "Pink": "pink"}
LABELS = {"chinook": "Chinook", "jack_chinook": "Chinook jacks", "steelhead": "Steelhead (hatchery and wild)", "wild_steelhead": "Wild steelhead",
          "coho": "Coho", "jack_coho": "Coho jacks"}
SHOWN = ("coho", "chinook", "steelhead")  # what the cards lead with; the rest are stored


class ParseError(Exception):
    pass


def url_for(year: int) -> str:
    # avg=1 adds the ten-year average of each calendar day; the other options (cumulative, normalized) stay off: DART treats any value of a checkbox as ticked
    return (f"https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php?outputFormat=csv&year={year}&proj={PROJECT}&span=no"
            f"&startdate=1%2F1&enddate=12%2F31&run=&syear={year}&eyear={year}&avg=1")


def _num(s: str) -> float | None:
    s = (s or "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse(body: bytes | str) -> list[dict]:
    """[{observed_on, species, count, avg10}]. Pure function of the stored CSV. Notes after the table are ignored."""
    text = body.decode("utf8", "replace") if isinstance(body, bytes) else body
    lines = [l for l in text.splitlines() if l.startswith("Project,") or l.startswith(PROJECT_NAME + ",")]
    if not lines or not lines[0].startswith("Project,Date"):
        raise ParseError("no DART table found")
    out = []
    try:
        for row in csv.DictReader(io.StringIO("\n".join(lines))):
            try:
                day = date.fromisoformat(row["Date"]).isoformat()
            except ValueError:
                continue  # DART pads every year to 366 rows, so a non-leap year has a "02-29": there is nothing to keep
            counts = {sp: _num(row.get(col)) for col, sp in COLUMNS.items() if col in row}
            if not any(v is not None for v in counts.values()):
                continue  # a day with nothing reported (a future date, or the lag): not a day of zeros
            for col, sp in COLUMNS.items():
                if col not in row:
                    continue
                c = counts[sp] or 0.0
                out.append({"observed_on": day, "species": sp, "count": c, "avg10": _num(row.get(col + "10Yr"))})
    except (KeyError, ValueError) as exc:
        raise ParseError(f"unexpected DART table: {exc}") from exc
    if not out:
        raise ParseError("DART table has no counts")
    return out


def _latest(session: Session, observed_on: str, species: str) -> FishCount | None:
    return session.scalar(select(FishCount).where(FishCount.project == PROJECT, FishCount.observed_on == observed_on, FishCount.species == species)
                          .order_by(FishCount.id.desc()).limit(1))


def run_job(session: Session, fetch: Fetcher | None = None, today: date | None = None) -> dict:
    fetch = fetch or (lambda u: http_fetch(u, system_trust=True))
    url = url_for((today or date.today()).year)
    status, body = fetch(url)
    raw, _ = store_fetch(session, SOURCE, url, status, body)
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
    added = changed = 0
    for r in rows:
        prev = _latest(session, r["observed_on"], r["species"])
        if prev is None or prev.count != r["count"] or prev.avg10 != r["avg10"]:
            session.add(FishCount(project=PROJECT, observed_on=r["observed_on"], species=r["species"], count=r["count"], avg10=r["avg10"], raw_fetch_id=raw.id))
            added, changed = added + (prev is None), changed + (prev is not None)
    raw.parse_ok = 1
    session.commit()
    return {"ok": True, "added": added, "revised": changed}


def _current(session: Session, since: str, until: str) -> dict[tuple[str, str], FishCount]:
    """The newest row for each (day, species) in the range."""
    newest = (select(func.max(FishCount.id)).where(FishCount.project == PROJECT, FishCount.observed_on >= since, FishCount.observed_on <= until)
              .group_by(FishCount.observed_on, FishCount.species))
    return {(r.observed_on, r.species): r for r in session.scalars(select(FishCount).where(FishCount.id.in_(newest)))}


def summary(session: Session, days: int = 7) -> dict | None:
    """The latest `days` days that have counts: per species the total and the ten-year average for the same days. None before the first fetch."""
    last = session.scalar(select(func.max(FishCount.observed_on)).where(FishCount.project == PROJECT))
    if last is None:
        return None
    end = date.fromisoformat(last)
    since = (end - timedelta(days=days - 1)).isoformat()
    cur = _current(session, since, last)
    reported = sorted({d for d, _ in cur})
    species = {}
    for sp in LABELS:
        rows = [cur[(d, sp)] for d in reported if (d, sp) in cur]
        total, avg = sum(r.count for r in rows), sum(r.avg10 or 0 for r in rows)
        if total or avg:
            species[sp] = {"label": LABELS[sp], "count": round(total), "avg10": round(avg),
                           "daily": [{"date": d, "count": round(cur[(d, sp)].count)} for d in reported if (d, sp) in cur]}
    newest = session.scalar(select(func.max(FishCount.id)))
    fetched = session.get(RawFetch, session.scalar(select(FishCount.raw_fetch_id).where(FishCount.id == newest))).fetched_at
    return {"project": PROJECT_NAME, "through": last, "from": reported[0] if reported else since, "days_reported": len(reported), "species": species,
            "fetched_at": fetched, "page": PAGE_URL}
