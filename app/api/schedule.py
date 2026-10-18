"""ODFW's published stocking schedule, looked at ahead: weeks in a date range with the waterbodies stocked in each,
and a per-month summary for browsing months out. Only confirmed waterbody matches appear; the newest snapshot of a
(week, waterbody) wins, like everywhere else. Stocking is by WEEK and can change, and the response says so."""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.stocking import _latest_scrape, latest_rows
from app.db import get_session
from app.models import Waterbody

router = APIRouter()


def _today() -> date:
    return datetime.now(timezone.utc).astimezone().date()


@router.get("/schedule")
def schedule(start: date | None = Query(None), end: date | None = Query(None), session: Session = Depends(get_session)):
    today = _today()
    this_monday = today - timedelta(days=today.weekday())
    start = start or this_monday
    end = end or (start + timedelta(days=28))
    names = {w.id: w for w in session.scalars(select(Waterbody))}
    weeks: dict[str, list[dict]] = defaultdict(list)
    months: dict[str, dict] = {}
    for snap, alias in latest_rows(session):
        if not (alias.confirmed and alias.waterbody_id in names):
            continue
        wk = date.fromisoformat(snap.week_of)
        total = snap.total or 0
        if wk >= this_monday:  # the month chips only look forward
            m = months.setdefault(snap.week_of[:7], {"month": snap.week_of[:7], "weeks": set(), "waterbodies": set(), "fish": 0})
            m["weeks"].add(snap.week_of)
            m["waterbodies"].add(alias.waterbody_id)
            m["fish"] += total
        if start <= wk <= end:
            wb = names[alias.waterbody_id]
            weeks[snap.week_of].append({"id": wb.id, "name": wb.name, "kind": wb.kind, "legals": snap.legals, "trophy": snap.trophy, "total": total})
    out = []
    for wk in sorted(weeks):
        rows = sorted(weeks[wk], key=lambda r: (-r["total"], r["name"]))
        out.append({"week_of": wk, "waterbodies": rows, "total_fish": sum(r["total"] for r in rows)})
    return {
        "start": start.isoformat(), "end": end.isoformat(), "weeks": out,
        "months": [{"month": m["month"], "weeks": len(m["weeks"]), "waterbodies": len(m["waterbodies"]), "fish": m["fish"]}
                   for m in sorted(months.values(), key=lambda m: m["month"])],
        "as_of": _latest_scrape(session),
        "note": "ODFW's schedule is by week, not day, and can change without notice. Check ODFW for regulations.",
    }
