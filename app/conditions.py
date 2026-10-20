"""Everything the sheet and day-of view show, with an 'as of' time on each source and a stale flag.
Numbers come from the database; nothing here is generated text."""
import statistics
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.astro import daylight, moon_phase
from app.freshness import freshness
from app.models import Gauge, GaugeReading, Report, ReportItem, StockingSnapshot, Waterbody, WaterbodyAlias, WaterbodyGauge
from app import passage
from app.sources import corps, nifc, nwps, nws, odf_fire, oha

GAUGE_STALE_H = 3
FORECAST_STALE_H = 6


def _age_h(iso: str) -> float:
    return (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds() / 3600


def flow_vs_median(session: Session, gauge_id: int) -> tuple[float | None, float | None]:
    """The gauge's median flow over its recent history and how far the latest reading is from it (percent). Needs at least 24
    readings spanning two days, the same rule the planner uses, so a new gauge says nothing instead of something silly."""
    rows = session.scalars(select(GaugeReading).where(GaugeReading.gauge_id == gauge_id, GaugeReading.parameter == "discharge_cfs")
                           .where(GaugeReading.observed_at >= (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="minutes"))
                           .order_by(GaugeReading.observed_at.desc()).limit(7 * 96)).all()
    if len(rows) < 24:
        return None, None
    span = (datetime.fromisoformat(rows[0].observed_at) - datetime.fromisoformat(rows[-1].observed_at)).total_seconds() / 3600
    med = statistics.median(r.value for r in rows)
    if span < 48 or med <= 0:
        return None, None
    return round(med, 1), round((rows[0].value - med) / med * 100)


def latest_gauge(session: Session, g: Gauge) -> dict:
    out = {"id": g.id, "site_no": g.site_no, "name": g.name, "lat": g.lat, "lon": g.lon, "provisional": True,
           "values": {}, "as_of": None, "stale": True, "trend": None, "flood": nwps.for_site(session, g.site_no)}
    for param in ("discharge_cfs", "gage_height_ft", "water_temp_c", "dissolved_oxygen_mgl", "ph", "turbidity_fnu", "conductance_uscm"):
        r = session.scalar(select(GaugeReading).where(GaugeReading.gauge_id == g.id, GaugeReading.parameter == param)
                           .order_by(GaugeReading.observed_at.desc()).limit(1))
        if r is None:
            continue
        out["values"][param] = {"value": r.value, "observed_at": r.observed_at,
                                "stale": _age_h(r.observed_at) > GAUGE_STALE_H, "provisional": bool(r.provisional)}
        if out["as_of"] is None or r.observed_at > out["as_of"]:
            out["as_of"] = r.observed_at
        out["provisional"] = out["provisional"] and bool(r.provisional)
    if "water_temp_c" in out["values"]:
        out["values"]["water_temp_f"] = {**out["values"]["water_temp_c"],
                                         "value": round(out["values"]["water_temp_c"]["value"] * 9 / 5 + 32, 1)}
    q = out["values"].get("discharge_cfs")
    if q:
        out["as_of"] = q["observed_at"]  # a newer temperature sensor must not make old flow look fresh
    if q and not q["stale"]:
        cutoff = (datetime.fromisoformat(q["observed_at"]) - timedelta(hours=3)).isoformat(timespec="minutes")
        earlier = session.scalar(select(GaugeReading).where(
            GaugeReading.gauge_id == g.id, GaugeReading.parameter == "discharge_cfs", GaugeReading.observed_at <= cutoff)
            .order_by(GaugeReading.observed_at.desc()).limit(1))
        if earlier and earlier.value and (datetime.fromisoformat(cutoff) - datetime.fromisoformat(earlier.observed_at)).total_seconds() <= 3600:
            change = (q["value"] - earlier.value) / earlier.value
            out["trend"] = "rising" if change > 0.03 else "falling" if change < -0.03 else "steady"
    out["stale"] = out["as_of"] is None or _age_h(out["as_of"]) > GAUGE_STALE_H
    out["median_cfs"], out["vs_median_pct"] = flow_vs_median(session, g.id)
    return out


def pick_weather(payload: dict, day: date) -> dict | None:
    periods = payload.get("forecast") or []
    same_day = [p for p in periods if p["start"][:10] == day.isoformat()]
    daytime = [p for p in same_day if p.get("daytime")]
    p = (daytime or same_day or [None])[0]
    if p is None:
        return None
    return {k: p.get(k) for k in ("name", "temp_f", "precip_pct", "wind", "wind_dir", "short")}


def report_items(session: Session, wb_id: int, limit: int) -> list[dict]:
    """Items read from ODFW's weekly report for a waterbody: the ones a person accepted, and the model's own reading of the
    report that has not been reviewed yet (flagged `reviewed: False`, shown as such). Rejected items never appear. Only accepted
    items feed scores."""
    zone = session.scalar(select(Waterbody.zone).where(Waterbody.id == wb_id))
    rows = session.execute(select(ReportItem, Report).join(Report, Report.id == ReportItem.report_id)
                           .where(ReportItem.waterbody_id == wb_id, ReportItem.status.in_(("accepted", "review")))
                           .order_by(Report.issued_on.desc(), ReportItem.status.asc(), ReportItem.id.desc())).all()  # "accepted" sorts before "review"
    # an unreviewed reading is trusted only inside its own report zone
    return [{"issued_on": r.issued_on, "note": i.note, "rating": i.rating, "species": i.species, "source_sentence": i.source_sentence,
             "reviewed": i.status == "accepted"} for i, r in rows if i.status == "accepted" or r.zone == zone][:limit]


def conditions(session: Session, wb: Waterbody, day: date, today: date | None = None) -> dict:
    today = today or date.today()
    out: dict = {"waterbody_id": wb.id, "date": day.isoformat()}

    area = nws.area_cached(session, wb)
    if area:
        payload, distance = area
        w = pick_weather(payload, day)
        out["weather"] = {"as_of": payload["fetched_at"], "stale": _age_h(payload["fetched_at"]) > FORECAST_STALE_H,
                          "source": "NWS forecast", "distance_km": round(distance, 1), "day": w}
    else:
        out["weather"] = None

    gauges = session.scalars(select(Gauge).join(WaterbodyGauge, WaterbodyGauge.gauge_id == Gauge.id)
                             .where(WaterbodyGauge.waterbody_id == wb.id)).all()
    out["gauges"] = [latest_gauge(session, g) for g in gauges]
    temps = [g["values"]["water_temp_f"] for g in out["gauges"] if "water_temp_f" in g["values"]]
    out["water_temp_f"] = max(temps, key=lambda t: datetime.fromisoformat(t["observed_at"])) if temps else None

    if wb.lat is not None and wb.lon is not None:
        out["daylight"] = daylight(wb.lat, wb.lon, day)
    else:
        out["daylight"] = None
    out["moon"] = moon_phase(day)

    out["reservoir"] = corps.for_waterbody(session, wb)
    out["passage"] = passage.for_waterbody(session, wb.name)
    out["fire"] = {"danger": odf_fire.current(session, wb.id), "nearby": nifc.current(session, wb.id)}

    out["advisories"] = [{"kind": a.kind, "text": a.text, "issued": a.observed_at} for a in oha.current(session, wb.id)]
    out["advisory_page"] = oha.PAGE_URL

    snaps = session.execute(
        select(StockingSnapshot).join(WaterbodyAlias, WaterbodyAlias.id == StockingSnapshot.alias_id)
        .where(WaterbodyAlias.waterbody_id == wb.id, WaterbodyAlias.confirmed == 1)
        .order_by(StockingSnapshot.week_of, StockingSnapshot.id)).scalars().all()
    newest = {s.week_of: s for s in snaps}  # later snapshot wins
    out["stocking"] = [{"week_of": w, "legals": s.legals, "trophy": s.trophy, "total": s.total,
                        "freshness": freshness(w, today)} for w, s in sorted(newest.items())
                       if freshness(w, today) in ("this_week", "recent", "upcoming")]

    out["report_items"] = report_items(session, wb.id, 3)
    return out
