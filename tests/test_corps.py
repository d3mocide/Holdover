"""Army Corps reservoir levels: parsing the real captured response, what each job asks for, history, and failure."""
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

import pytest
from conftest import FIX
from sqlalchemy import func, select

from app.models import RawFetch, ReservoirReading, Waterbody
from app.seed import seed_waterbodies
from app.sources import corps

BODY = (FIX / "corps" / "elev_1d.json").read_bytes()


def payload(code="DET", values=(("2026-10-18T14:30:00", 1491.53, 0),), units="ft"):
    key = corps.SERIES.format(code)
    return json.dumps({code: {"name": "x", "timeseries": {key: {"units": units, "values": [list(v) for v in values]}}}}).encode()


def test_parses_the_real_response_for_all_nine_projects():
    rows = corps.parse(BODY)
    assert {r["project"] for r in rows} == set(corps.PROJECTS)
    det = [r for r in rows if r["project"] == "DET"]
    assert det[-1]["observed_at"].endswith("+00:00") and 1300 < det[-1]["elevation_ft"] < 1600
    assert len({(r["project"], r["observed_at"]) for r in rows}) == len(rows)


def test_skips_odd_values_but_rejects_wrong_units_and_garbage():
    rows = corps.parse(payload(values=[("2026-10-18T14:30:00", None, 0), ("2026-10-18T14:45:00", -5, 0), ("2026-10-18T15:00:00", 1490.0, 0)]))
    assert [r["elevation_ft"] for r in rows] == [1490.0]
    with pytest.raises(corps.ParseError):
        corps.parse(payload(units="m"))
    with pytest.raises(corps.ParseError):
        corps.parse(b"<html>maintenance</html>")
    with pytest.raises(corps.ParseError):
        corps.parse(b"[]")


def test_url_asks_for_utc_and_the_right_series():
    u = corps.url_for(("DET",), backward="3h")
    assert "timezone=GMT" in u and "DET.Elev-Forebay.Inst.0.0.Best" in unquote(u)
    assert u.endswith("&backward=3h")
    assert "startdate=2025-10-17T00:00&enddate=2025-10-19T00:00" in corps.url_for(start="2025-10-17T00:00", end="2025-10-19T00:00")


def test_bundled_intermediate_certificate_is_present():
    assert open(corps.CA).read().startswith("-----BEGIN CERTIFICATE-----")


def fetcher(calls, body=BODY, status=200):
    def f(url):
        calls.append(url)
        return status, body
    return f


def test_job_stores_raw_first_and_adds_rows_once(session):
    calls = []
    out = corps.run_job(session, fetcher(calls))
    assert out["ok"] and out["added"] > 1000
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "corps", RawFetch.parse_ok == 1)) >= 1
    n = session.scalar(select(func.count()).select_from(ReservoirReading))
    assert corps.run_job(session, fetcher([]))["added"] == 0  # same data again adds nothing
    assert session.scalar(select(func.count()).select_from(ReservoirReading)) == n


def test_first_run_looks_back_a_week_and_later_runs_only_the_gap(session):
    calls = []
    corps.run_job(session, fetcher(calls))
    assert "backward=168h" in calls[0] or "backward=169h" in calls[0]
    session.add(ReservoirReading(project="DET", observed_at=(datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat(timespec="minutes"), elevation_ft=1490))
    session.commit()
    calls.clear()
    corps.run_job(session, fetcher(calls))
    assert "backward=4h" in calls[0]


def test_failure_keeps_old_data_and_marks_the_fetch(session):
    corps.run_job(session, fetcher([]))
    n = session.scalar(select(func.count()).select_from(ReservoirReading))
    assert corps.run_job(session, fetcher([], body=b"nope", status=200)) == {"ok": False}
    assert corps.run_job(session, fetcher([], body=b"", status=503)) == {"ok": False}
    assert session.scalar(select(func.count()).select_from(ReservoirReading)) == n
    last = session.scalar(select(RawFetch).where(RawFetch.source == "corps").order_by(RawFetch.id.desc()))
    assert last.parse_ok == 0 and "503" in last.error


def seeded_level(session, rows, now):
    for t, v in rows:
        session.add(ReservoirReading(project="DET", observed_at=t.isoformat(timespec="minutes"), elevation_ft=v))
    session.commit()
    return corps.level(session, "DET", today=now)


def test_level_changes_and_same_date_in_earlier_years(session):
    now = datetime(2026, 10, 18, 14, 30, tzinfo=timezone.utc)
    d = timedelta
    rows = [(now, 1491.5), (now - d(hours=24), 1492.5), (now - d(days=7), 1500.0),
            (now.replace(year=2025), 1498.0), (now.replace(year=2024) + d(hours=5), 1450.0)]
    lv = seeded_level(session, rows, now)
    assert lv["elevation_ft"] == 1491.5 and lv["stale"] is False
    assert lv["change_24h_ft"] == -1.0 and lv["change_7d_ft"] == -8.5
    assert lv["earlier_years"] == [{"year": 2025, "elevation_ft": 1498.0}, {"year": 2024, "elevation_ft": 1450.0}]


def test_level_goes_stale_and_is_none_without_data(session):
    assert corps.level(session, "DET") is None
    now = datetime(2026, 10, 18, 14, 30, tzinfo=timezone.utc)
    lv = seeded_level(session, [(now - timedelta(hours=5), 1491.5)], now)
    assert lv["stale"] is True and lv["change_24h_ft"] is None and lv["earlier_years"] == []


def test_every_project_maps_to_a_seeded_waterbody(session):
    seed_waterbodies(session)
    names = set(session.scalars(select(Waterbody.name)))
    assert set(corps.PROJECTS.values()) <= names
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    corps.run_job(session, fetcher([]))
    assert corps.for_waterbody(session, wb)["project"] == "DET"
    other = session.scalar(select(Waterbody).where(Waterbody.name == "Carmen Reservoir"))
    assert corps.for_waterbody(session, other) is None
