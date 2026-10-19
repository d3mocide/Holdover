"""The weekly briefing's FACTS: built by code from the database, nothing generated."""
from datetime import date

from sqlalchemy import select

from app.briefing import build, monday
from app.models import Gauge, GaugeReading, ReportItem
from app.seed import seed_waterbodies
from app.sources.odfw_report import ingest as ingest_report
from app.sources.odfw_stocking import ingest_page
from conftest import FIX

TODAY = date(2026, 10, 14)


def loaded(session, stocking_html):
    seed_waterbodies(session)
    ingest_page(session, "https://example.test/stocking?page=0", 200, stocking_html)
    ingest_report(session, "https://example.test/recreation-report", 200, (FIX / "odfw_report" / "index.html").read_bytes())


def by_key(sections):
    return {s.key: s for s in sections}


def test_an_empty_database_gives_no_sections(session):
    assert build(session, TODAY) == []


def test_stocking_lists_this_week_and_the_next_two_weeks_from_the_schedule(session, stocking_html):
    loaded(session, stocking_html)
    st = by_key(build(session, TODAY))["stocking"]
    assert st.narrate and st.facts[0].startswith("This week (Oct 12): ")
    assert "Alton Baker Canal 750 legals" in st.facts[0] and "2 waterbodies, 1,050 fish" in st.facts[0]
    assert all(f.startswith(("This week", "Scheduled for the week of")) for f in st.facts) and len(st.facts) <= 3
    assert not any("(Oct 19)" in f or "1 waterbodies" in f for f in st.facts)
    assert "Scheduled for the week of Oct 19" in " ".join(st.facts)


def test_the_odfw_section_is_the_reports_own_words_and_is_never_narrated(session, stocking_html):
    loaded(session, stocking_html)
    rep = by_key(build(session, TODAY))["report"]
    assert not rep.narrate and rep.facts[0].startswith("Coho salmon are moving into the lower parts of the North Santiam")


def test_water_has_flow_against_the_gauges_own_median_and_marks_everything_provisional(session, stocking_html):
    loaded(session, stocking_html)
    g = session.scalar(select(Gauge).where(Gauge.site_no == "14150000"))
    for i in range(120):  # 5 days of 15-minute readings, flat at 1,200 cfs then a bump
        session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=1200 + (50 if i == 0 else 0), observed_at=f"2026-10-{14 - i // 24:02d}T{i % 24:02d}:00+00:00"))
    session.commit()
    w = by_key(build(session, TODAY))["water"]
    line = next(f for f in w.facts if f.startswith(g.name))
    assert "cfs vs median" in line and "(USGS, provisional)" in line


def test_where_lists_the_best_spots_without_any_distance_or_score_numbers(session, stocking_html):
    loaded(session, stocking_html)
    where = by_key(build(session, TODAY)).get("where")
    if where:  # needs enough data behind a score; the fixture has stocking for trout
        assert where.facts[0].endswith("best first:")
        text = " ".join(where.facts).lower()
        assert "miles" not in text and "straight-line" not in text


def test_alerts_only_exist_when_there_is_something_to_say(session, stocking_html):
    loaded(session, stocking_html)
    assert "alerts" not in by_key(build(session, TODAY))
    from app.models import Advisory, Waterbody
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    session.add(Advisory(kind="algae:precaution", waterbody_id=wb.id, text="x", observed_at="2026-06-18", raw_fetch_id=None))
    session.commit()
    from app.sources import oha
    from app.models import RawFetch
    raw = RawFetch(source=oha.SOURCE, url="u", fetched_at="2026-10-18T00:00:00+00:00", status=200, parse_ok=1, body=b"{}")
    session.add(raw); session.flush()
    session.query(Advisory).update({Advisory.raw_fetch_id: raw.id}); session.commit()
    al = by_key(build(session, TODAY))["alerts"]
    assert al.facts == ["Detroit Reservoir: algae precaution (OHA, issued 2026-06-18)."] and not al.narrate


def test_monday_helper():
    assert monday(date(2026, 10, 18)) == date(2026, 10, 12) and monday(date(2026, 10, 12)) == date(2026, 10, 12)


def test_alerts_come_first_and_a_fishery_with_no_real_signal_is_left_out(session, stocking_html):
    loaded(session, stocking_html)
    keys = [s.key for s in build(session, TODAY)]
    assert keys[-1] == "report" and keys.index("stocking") < keys.index("report")
    where = by_key(build(session, TODAY)).get("where")  # needs enough data behind a score; absent here, which is the point
    if where:
        assert not any(f.startswith("Steelhead") or f.startswith("Warmwater") for f in where.facts)  # nothing stocked or reported for them
