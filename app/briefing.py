"""The weekly briefing: what is worth knowing this week, assembled from everything Holdover gathers.

This module builds only FACTS: plain sentences with units, taken from the database by code. Nothing here is generated.
A language model may later write a short paragraph from a section's facts (app/llm/briefing.py); the paragraph is checked against
those same facts, stored with them, and the page falls back to the facts alone when there is none."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import scoring as sc
from app.api.reports import latest_report
from app.api.stocking import latest_rows
from app.models import FireNearby, Gauge, GaugeReading, RawFetch, Waterbody
from app.planner import FISHERIES, rank
from app.sources import corps, dart, nifc, nwps, oha
from app.sources.odfw_report import parse as parse_report
from app.zones import BY_KEY

FISHERY_LABEL = {"trout": "Stocked trout", "steelhead": "Steelhead and salmon", "warmwater": "Warmwater"}


@dataclass
class Section:
    key: str
    title: str
    facts: list[str] = field(default_factory=list)
    narrate: bool = True  # False: shown as facts only (ODFW's own wording, alerts)
    hint: str = ""  # what a good paragraph for this section does (an editorial instruction, never a fact)


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _n(n: int | None) -> str:
    return f"{n:,}" if n else "0"


def where(session: Session, today: date, zone: str) -> Section:
    s = Section("where", "Where to fish", hint="Recommend the two or three best choices and say why in a sentence each. Do not list every spot.")
    for f in FISHERIES:
        # only spots with a real signal (recent or scheduled stocking, or an accepted ODFW report item); a list padded with
        # waters that merely fit the fishery says nothing
        spots = [sp for sp in rank(session, today, f, zone=zone) if sp.coverage >= 0.4 and (sp.facts["stocking"] or sp.facts["report"])][:4]
        if spots:
            s.facts.append(f"{FISHERY_LABEL[f]}, best first:")
            s.facts += [f"{sp.wb.name}: " + " ".join(sp.template.split()) for sp in spots]
    return s


def stocking(session: Session, today: date, zone: str) -> Section:
    s = Section("stocking", "Stocking", hint="Say which week is the biggest and which waterbodies get the most. Keep it brief.")
    start = monday(today)
    weeks: dict[date, list[tuple[str, int, int, int]]] = {}
    names = {w.id: w.name for w in session.scalars(select(Waterbody).where(Waterbody.zone == zone))}
    for snap, alias in latest_rows(session):
        wk = date.fromisoformat(snap.week_of)
        if alias.confirmed and alias.waterbody_id in names and start <= wk <= start + timedelta(weeks=2):
            weeks.setdefault(wk, []).append((names[alias.waterbody_id], snap.legals or 0, snap.trophy or 0, snap.total or 0))
    for wk in sorted(weeks):
        rows = sorted(weeks[wk], key=lambda r: (-r[3], r[0]))
        label = f"This week ({wk:%b} {wk.day})" if wk == start else f"Scheduled for the week of {wk:%b} {wk.day}"
        parts = [f"{n} {_n(l)} legals" + (f" and {_n(t)} trophy" if t else "") for n, l, t, _ in rows[:8]]
        more = f", and {len(rows) - 8} more waterbodies" if len(rows) > 8 else ""
        count = f"{len(rows)} waterbod{'y' if len(rows) == 1 else 'ies'}"
        s.facts.append(f"{label}: {count}, {_n(sum(r[3] for r in rows))} fish in all: " + "; ".join(parts) + more + ".")
    return s


def _flow_line(session: Session, g: Gauge) -> str | None:
    rows = session.scalars(select(GaugeReading).where(GaugeReading.gauge_id == g.id, GaugeReading.parameter == "discharge_cfs")
                           .order_by(GaugeReading.observed_at.desc()).limit(7 * 96)).all()
    if not rows:
        return None
    span = (datetime.fromisoformat(rows[0].observed_at) - datetime.fromisoformat(rows[-1].observed_at)).total_seconds() / 3600
    f = sc.flow_factor(rows[0].value, [r.value for r in rows], 1.0, span)
    text = f.detail if f.value is not None else f"{rows[0].value:,.0f} cfs"
    flood = nwps.for_site(session, g.site_no)
    if flood and flood["elevated"]:
        text += f"; NOAA flood category {flood['label'].lower()}"
    return f"{g.name}: {text} (USGS, provisional)."


def passage_facts(session: Session, today: date, zone: str) -> Section:
    s = Section("passage", "Fish passage", hint="Say which species are moving past Willamette Falls now and how this week compares with the ten-year average. Do not say how many reach any river.")
    if zone != "willamette":
        return s
    d = dart.summary(session)
    if d is None:
        return s
    for sp in ("coho", "chinook", "steelhead"):
        x = d["species"].get(sp)
        if x:
            s.facts.append(f"{x['label']}: {x['count']:,} counted at the Willamette Falls fishway in the {d['days_reported']} days reported through {date.fromisoformat(d['through']):%b} {date.fromisoformat(d['through']).day}; the ten-year average for the same days is {x['avg10']:,} (ODFW counts, via Columbia River DART).")
    return s


def water(session: Session, today: date, zone: str) -> Section:
    s = Section("water", "Rivers and reservoirs", hint="Mention only what stands out: rivers far from their usual flow and big reservoir changes. Say the rest is near normal if it is.")
    for g in session.scalars(select(Gauge).where(Gauge.zone == zone).order_by(Gauge.name)):
        line = _flow_line(session, g)
        if line:
            s.facts.append(line)
    for code, name in (corps.PROJECTS.items() if zone == "willamette" else []):  # the Army Corps' Willamette projects
        lv = corps.level(session, code)
        if not lv:
            continue
        change = f", {'up' if lv['change_7d_ft'] > 0 else 'down'} {abs(lv['change_7d_ft']):.1f} ft over 7 days" if lv["change_7d_ft"] is not None else ""
        years = "; same date: " + ", ".join(f"{y['year']} {y['elevation_ft']:,.1f} ft" for y in lv["earlier_years"]) if lv["earlier_years"] else ""
        s.facts.append(f"{name} pool: {lv['elevation_ft']:,.1f} ft{change}{years} (Army Corps, unverified).")
    return s


def watchouts(session: Session, today: date, zone: str) -> Section:
    s = Section("alerts", "Watch-outs", narrate=False)
    names = {w.id: w.name for w in session.scalars(select(Waterbody).where(Waterbody.zone == zone))}
    for a in oha.current(session):
        if a.kind in ("algae:advisory", "algae:precaution") and a.waterbody_id in names:
            s.facts.append(f"{names[a.waterbody_id]}: {'algae advisory' if a.kind.endswith('advisory') else 'algae precaution'} (OHA, issued {a.observed_at}).")
    raw = session.scalar(select(RawFetch).where(RawFetch.source == nifc.SOURCE, RawFetch.parse_ok == 1).order_by(RawFetch.id.desc()).limit(1))
    if raw is not None:
        near: dict[str, list[tuple[float, str]]] = {}
        for r in session.scalars(select(FireNearby).where(FireNearby.raw_fetch_id == raw.id, FireNearby.waterbody_id.in_(names))):
            near.setdefault(r.incident, []).append((r.distance_km, names[r.waterbody_id]))
        for incident, rows in sorted(near.items()):
            km, wb = min(rows)
            s.facts.append(f"{incident} fire is burning; the nearest tracked waterbody is {wb}, {km:.0f} km away (NIFC perimeter; not a closure).")
    return s


def odfw(session: Session, today: date, zone: str) -> Section:
    s = Section("report", "From ODFW's weekly report", narrate=False)
    key = BY_KEY[zone].report_key
    r = latest_report(session, key)
    if r is not None:
        raw = session.get(RawFetch, r.raw_fetch_id)
        s.facts = parse_report(raw.body).zones.get(key, [])
    return s


def build(session: Session, today: date | None = None, zone: str = "willamette") -> list[Section]:
    """Sections in reading order, for one zone. Empty sections are dropped."""
    today = today or date.today()
    # watch-outs lead: safety and conditions before opportunities
    return [s for s in (watchouts(session, today, zone), where(session, today, zone), stocking(session, today, zone), passage_facts(session, today, zone), water(session, today, zone), odfw(session, today, zone)) if s.facts]
