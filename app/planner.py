"""Ranks spots for a date and fishery. Facts and numbers come from the database; the scoring maths is
in app/scoring.py; text is a deterministic template, optionally replaced by a cached LLM rewording."""
import json
import re
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import scoring as sc
from app.api.stocking import latest_rows
from app.astro import daylight
from app.config import get_settings
from app.conditions import GAUGE_STALE_H, FORECAST_STALE_H, _age_h, pick_weather
from app.models import Gauge, GaugeReading, Report, ReportItem, Waterbody, WaterbodyGauge
from app.sources import nws

FISHERIES = ("trout", "steelhead", "warmwater")
SPECIES_WORDS = {
    "steelhead": ("steelhead", "salmon", "coho", "chinook"),
    "warmwater": ("bass", "walleye", "panfish", "crappie", "bluegill", "shad", "perch", "catfish"),
    "trout": ("trout", "rainbow", "cutthroat", "brown"),
}


@dataclass
class Spot:
    wb: Waterbody
    score: float
    coverage: float
    factors: list[sc.Factor]
    facts: dict
    template: str


def wind_mph(s: str | None) -> float | None:
    nums = re.findall(r"\d+", s or "")
    return float(max(nums, key=float)) if nums else None


def zone_p90(rows, day: date) -> float:
    lo = sc.monday(day) - timedelta(weeks=8)
    totals = sorted(s.total or 0 for s, _ in rows if lo <= date.fromisoformat(s.week_of) <= sc.monday(day) and (s.total or 0) > 0)
    return float(totals[min(len(totals) - 1, int(0.9 * len(totals)))]) if totals else 0.0


def _gauge_inputs(session: Session, wb_id: int, day: date):
    gids = session.scalars(select(WaterbodyGauge.gauge_id).where(WaterbodyGauge.waterbody_id == wb_id)).all()
    best = (None, [], 0.0)
    for gid in gids:
        # only the two columns the factor needs, not whole ORM rows: a week of 15-minute readings is 672 of them per gauge
        rows = session.execute(select(GaugeReading.value, GaugeReading.observed_at).where(GaugeReading.gauge_id == gid, GaugeReading.parameter == "discharge_cfs")
                               .where(GaugeReading.observed_at >= (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="minutes"))
                               .order_by(GaugeReading.observed_at.desc()).limit(7 * 96)).all()
        if rows and _age_h(rows[0].observed_at) > GAUGE_STALE_H:
            continue
        if rows and len(rows) > len(best[1]):
            span = (datetime.fromisoformat(rows[0].observed_at) - datetime.fromisoformat(rows[-1].observed_at)).total_seconds() / 3600
            best = (rows[0].value, [r.value for r in rows], span)
    return best


def _report_inputs(session: Session, wb_id: int):
    rows = session.execute(select(ReportItem, Report).join(Report, Report.id == ReportItem.report_id)
                           .where(ReportItem.waterbody_id == wb_id, ReportItem.status == "accepted")
                           .order_by(Report.issued_on.desc(), ReportItem.id.desc())).all()
    rated = next(((i, r) for i, r in rows if i.rating in sc.RATING), None)
    species = " ".join((i.species or "") + " " + (i.note or "") for i, r in rows[:5]).lower()
    return rated, species, rows[0][0].source_sentence if rows else None


def in_fishery(wb: Waterbody, fishery: str, stocking_factor: sc.Factor, species_text: str) -> bool:
    hints = []
    if wb.species_json:
        try:
            hints = json.loads(wb.species_json).get("fisheries", [])
        except ValueError:
            pass
    if fishery in hints:
        return True
    if fishery == "trout" and stocking_factor.value is not None:
        return True
    return any(w in species_text for w in SPECIES_WORDS[fishery])


def rank(session: Session, day: date, fishery: str, home: tuple[float, float] | None = None, zone: str = "willamette") -> list[Spot]:
    """home overrides the server default (HOME_LAT/HOME_LON): a signed-in user's saved home, or one the browser sent. Only the zone's
    waterbodies are ranked, and "a big stocking" is judged against that zone's own recent stockings."""
    s = get_settings()
    home_lat, home_lon = home if home else (s.home_lat, s.home_lon)
    zone_ids = set(session.scalars(select(Waterbody.id).where(Waterbody.zone == zone)))
    rows = [(snap, alias) for snap, alias in latest_rows(session) if alias.waterbody_id in zone_ids]
    p90 = zone_p90(rows, day)
    by_wb: dict[int, list[tuple[str, int]]] = {}
    for snap, alias in rows:
        if alias.confirmed and alias.waterbody_id:
            by_wb.setdefault(alias.waterbody_id, []).append((snap.week_of, snap.total or 0))
    spots = []
    for wb in session.scalars(select(Waterbody).where(Waterbody.zone == zone)):
        if wb.lat is None or wb.lon is None:
            continue
        stock = sc.stocking_factor(by_wb.get(wb.id, []), day, p90, s.w_stocking) if fishery == "trout" else \
            sc.Factor("stocking", None, s.w_stocking, "not a stocked-trout fishery", applicable=False)
        rated, species_text, _ = _report_inputs(session, wb.id)
        if not in_fishery(wb, fishery, stock if fishery == "trout" else sc.Factor("s", None, 0, ""), species_text):
            continue
        rep = sc.report_factor(rated[0].rating if rated else None, rated[1].issued_on if rated else None, day, s.w_report)
        cur, hist, span = _gauge_inputs(session, wb.id, day)
        flow = sc.flow_factor(cur, hist, s.w_flow, span)
        if flow.value is not None and day != date.today():
            flow.detail += " (latest observed flow, not a forecast)"
        near = nws.area_cached(session, wb)
        wx = pick_weather(near[0], day) if near and _age_h(near[0]["fetched_at"]) <= FORECAST_STALE_H else None
        fc = sc.forecast_factor(wx["temp_f"] if wx else None, wx["precip_pct"] if wx else None,
                                wind_mph(wx["wind"]) if wx else None, s.w_forecast)
        forecast_note = f" (NWS point {near[1]:.0f} km away)" if near and fc.value is not None and near[1] >= 1 else ""
        plain_forecast = fc.detail
        fc.detail += forecast_note
        km = sc.haversine_km(home_lat, home_lon, wb.lat, wb.lon) if home_lat is not None and home_lon is not None else None
        dist = sc.distance_factor(km, s.w_distance)
        factors = [stock, rep, flow, fc, dist]
        score, coverage = sc.combine(factors)
        dl = daylight(wb.lat, wb.lon, day)
        facts = {"stocking": stock.detail if stock.value is not None else None,
                 "report": rep.detail if rep.value is not None else None,
                 "report_sentence": rated[0].source_sentence if rated else None,
                 "flow": flow.detail if flow.value is not None else None,
                 "forecast": plain_forecast if fc.value is not None else None,
                 "daylight": f"{dl['sunrise']}-{dl['sunset']}", "distance": dist.detail if dist.value is not None else None,
                 "species": rated[0].species if rated else None}
        spots.append(Spot(wb, score, coverage, factors, facts, template_text(facts, coverage)))
    spots.sort(key=lambda x: (-x.score, x.wb.name))
    return spots


def template_text(f: dict, coverage: float) -> str:
    """Two short lines from facts only. Deterministic, so it is always available when the LLM isn't."""
    line1 = [x for x in (f"Stocked: {f['stocking']}." if f["stocking"] else None,
                         f"ODFW report: {f['report'].split(': ', 1)[1]}." if f["report"] else None) if x]
    line2 = [x for x in (f"Flow {f['flow']}." if f["flow"] else None, f"Forecast {f['forecast']}." if f["forecast"] else None,
                         f"Light {f['daylight']}.") if x]
    if not line1:
        line1 = ["No recent stocking or report item for this water."]
    if coverage < 0.4:
        line2.append("Little data behind this score.")
    return " ".join(line1) + "\n" + " ".join(line2)


def facts_text(f: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in f.items() if v)
