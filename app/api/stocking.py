"""Latest-snapshot view of stocking. A (week, alias) pair is current as of its newest snapshot;
older snapshots stay in the table and are returned by the history endpoint."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.freshness import freshness
from app.models import Report, ReportItem, StockingSnapshot, Waterbody, WaterbodyAlias

router = APIRouter()


def _today() -> date:
    return datetime.now(timezone.utc).astimezone().date()


def latest_rows(session: Session):
    newest = (
        select(func.max(StockingSnapshot.id).label("id"))
        .group_by(StockingSnapshot.week_of, StockingSnapshot.alias_id)
        .subquery()
    )
    return session.execute(
        select(StockingSnapshot, WaterbodyAlias)
        .join(newest, newest.c.id == StockingSnapshot.id)
        .join(WaterbodyAlias, WaterbodyAlias.id == StockingSnapshot.alias_id)
        .order_by(StockingSnapshot.week_of)
    ).all()


@router.get("/map")
def map_layers(zone: str = "willamette", session: Session = Depends(get_session)):
    today = _today()
    by_wb: dict[int, list[StockingSnapshot]] = {}
    for snap, alias in latest_rows(session):
        if alias.confirmed and alias.waterbody_id:
            by_wb.setdefault(alias.waterbody_id, []).append(snap)
    features, needs_coords = [], []
    for wb in session.scalars(select(Waterbody).where(Waterbody.zone == zone)):
        snaps = by_wb.get(wb.id, [])
        if not snaps:
            continue
        past = [s for s in snaps if freshness(s.week_of, today) != "upcoming"]
        nxt = [s for s in snaps if freshness(s.week_of, today) == "upcoming"]
        last = past[-1] if past else None
        upcoming = nxt[0] if nxt else None
        bucket = freshness(last.week_of, today) if last else "upcoming"
        props = {
            "id": wb.id, "name": wb.name, "kind": wb.kind, "freshness": bucket,
            "last_week": last.week_of if last else None, "last_total": last.total if last else None,
            "next_week": upcoming.week_of if upcoming else None,
            "next_total": upcoming.total if upcoming else None,
            "zone_office": (last or upcoming).zone_office,
        }
        if wb.lat is None or wb.lon is None:
            needs_coords.append(props)
            continue
        features.append({"type": "Feature", "properties": props,
                         "geometry": {"type": "Point", "coordinates": [wb.lon, wb.lat]}})
    unconfirmed = session.scalar(
        select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.confirmed == 0)
    )
    return {
        "type": "FeatureCollection", "features": features,
        "meta": {"layer": "stocking", "as_of": _latest_scrape(session), "needs_coords": needs_coords,
                 "unconfirmed_aliases": unconfirmed,
                 "note": "Stocking is shown by week; the schedule may change without notice."},
    }


def _latest_scrape(session: Session) -> str | None:
    return session.scalar(select(func.max(StockingSnapshot.scraped_at)))


@router.get("/waterbodies/{wb_id}")
def waterbody(wb_id: int, session: Session = Depends(get_session)):
    wb = session.get(Waterbody, wb_id)
    if wb is None:
        raise HTTPException(404)
    rows = session.execute(
        select(StockingSnapshot)
        .join(WaterbodyAlias, WaterbodyAlias.id == StockingSnapshot.alias_id)
        .where(WaterbodyAlias.waterbody_id == wb_id, WaterbodyAlias.confirmed == 1)
        .order_by(StockingSnapshot.week_of.desc(), StockingSnapshot.id.desc())
    ).scalars().all()
    today = _today()
    current = {r.week_of: r for r in reversed(rows)}  # newest snapshot per week wins
    return {
        "id": wb.id, "name": wb.name, "kind": wb.kind, "zone": wb.zone, "lat": wb.lat, "lon": wb.lon,
        "regs_url": wb.regs_url,
        "stocking": [
            {"week_of": w, "legals": r.legals, "trophy": r.trophy, "total": r.total,
             "zone_office": r.zone_office, "freshness": freshness(w, today), "scraped_at": r.scraped_at}
            for w, r in sorted(current.items(), reverse=True)
        ],
        "snapshots": len(rows),
        "report_items": [
            {"issued_on": r.issued_on, "species": i.species, "rating": i.rating, "note": i.note,
             "source_sentence": i.source_sentence}
            for i, r in session.execute(
                select(ReportItem, Report).join(Report, Report.id == ReportItem.report_id)
                .where(ReportItem.waterbody_id == wb_id, ReportItem.status == "accepted")
                .order_by(Report.issued_on.desc()).limit(5))
        ],
    }
