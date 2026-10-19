import json
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.conditions import conditions, latest_gauge
from app.models import Advisory, Gauge, GaugeReading, Waterbody
from app.seed import seed_waterbodies
from app.sources import nws, oha, usgs
from conftest import FIX, usgs_fetch

POINTS = (FIX / "nws" / "points.json").read_bytes()
FORECAST = (FIX / "nws" / "forecast.json").read_bytes()
HOURLY = (FIX / "nws" / "hourly.json").read_bytes()
HABS = (FIX / "oha" / "habs_points.geojson").read_bytes()


def wb(session, name):
    return session.scalar(select(Waterbody).where(Waterbody.name == name))


def test_nws_parse():
    pts = nws.parse_points(POINTS)
    assert pts["forecast"].endswith("/forecast") and pts["hourly"].endswith("/forecast/hourly")
    periods, updated = nws.parse_periods(FORECAST, 14)
    assert periods[0]["temp_f"] is not None and updated
    with pytest.raises(nws.ParseError):
        nws.parse_points(b"{}")


def nws_fetch(url):
    if "/points/" in url:
        return 200, POINTS
    return (200, HOURLY) if url.endswith("/hourly") else (200, FORECAST)


def test_nws_refresh_and_failure_keeps_cache(session):
    seed_waterbodies(session)
    w = wb(session, "Alton Baker Canal")
    assert nws.cached(session, w.id) is None
    payload = nws.refresh(session, w, nws_fetch)
    assert payload["forecast"] and payload["hourly"]
    assert nws.refresh(session, w, lambda u: (500, b"")) is None
    assert nws.cached(session, w.id)["fetched_at"] == payload["fetched_at"]


def test_oha_parse_and_match(session):
    rows = oha.parse(HABS)
    assert any(r["kind"] == "algae:precaution" and r["name"] == "Detroit Lake" for r in rows)
    assert all(r["kind"] is None for r in rows if r["status"] not in ("Advisory", "Precaution"))
    seed_waterbodies(session)
    assert oha.match(session, "Detroit Lake") == wb(session, "Detroit Reservoir").id
    assert oha.match(session, "Diamond Lake") is None  # not tracked: not guessed
    assert oha.run_job(session, lambda u: (200, HABS))["tracked_advisories"] >= 1
    assert [a.kind for a in oha.current(session, wb(session, "Detroit Reservoir").id)] == ["algae:precaution"]


def test_conditions_with_stale_flags(session):
    seed_waterbodies(session)
    w = wb(session, "Santiam River, North Fork")
    usgs.run_job(session, usgs_fetch())  # fixture readings are from 2026-10-18: old by now
    c = conditions(session, w, date(2026, 10, 17), today=date(2026, 10, 17))
    assert c["weather"] is None and c["daylight"]["sunrise"] and c["moon"]["phase"]
    g = c["gauges"][0]
    assert g["site_no"] in ("14183000", "14181500") and g["provisional"] is True
    nws.refresh(session, w, nws_fetch)
    c = conditions(session, w, date.today())
    assert c["weather"]["source"] == "NWS forecast" and c["weather"]["stale"] is False


def test_gauge_stale_and_trend(session):
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == "14183000"))
    now = datetime.now(timezone.utc)
    for hrs, val in [(4, 1000.0), (0.1, 1200.0)]:
        session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=val, provisional=1,
                                 observed_at=(now - timedelta(hours=hrs)).isoformat(timespec="minutes")))
    session.commit()
    lg = latest_gauge(session, g)
    assert lg["trend"] == "rising" and lg["stale"] is False
    session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=5.0, provisional=1,
                             observed_at=(now - timedelta(hours=30)).isoformat(timespec="minutes")))
    old = session.scalar(select(Gauge).where(Gauge.site_no == "14166000"))
    assert latest_gauge(session, old)["stale"] is True  # no readings at all


def test_api_day_gauges_and_layers(session, monkeypatch):
    from app.main import app
    import app.api.conditions as api_cond
    seed_waterbodies(session)
    usgs.run_job(session, usgs_fetch())
    oha.run_job(session, lambda u: (200, HABS))
    monkeypatch.setattr(api_cond, "quick_fetch", nws_fetch)
    c = TestClient(app)
    w = wb(session, "Detroit Reservoir")
    d = c.get(f"/api/day/{w.id}").json()
    assert d["conditions"]["weather"]["day"] and d["conditions"]["advisories"][0]["kind"] == "algae:precaution"
    assert d["conditions"]["advisory_page"].startswith("https://www.oregon.gov")
    g = c.get("/api/gauges").json()
    assert len(g["gauges"]) == 16 and "provisional" in g["note"]
    m = c.get("/api/map?layers=stocking,gauges,advisories,reports").json()
    layers = {f["properties"]["layer"] for f in m["features"]}
    assert {"gauge", "advisory"} <= layers
    assert c.get(f"/api/day/999999").status_code == 404


def test_day_endpoint_survives_nws_down(session, monkeypatch):
    from app.main import app
    import app.api.conditions as api_cond
    seed_waterbodies(session)
    monkeypatch.setattr(api_cond, "quick_fetch", lambda u: (None, b"timeout"))
    w = wb(session, "Alton Baker Canal")
    r = TestClient(app).get(f"/api/day/{w.id}")
    assert r.status_code == 200 and r.json()["conditions"]["weather"] is None


def test_nws_never_fetched_is_stale(session):
    from app.scheduler import source_status
    assert source_status()["nws"]["stale"] is True


def test_gauge_reports_flow_against_its_own_median_and_stays_quiet_without_history(session):
    from datetime import datetime, timedelta, timezone

    from app.conditions import latest_gauge
    from app.models import Gauge, GaugeReading
    from app.seed import seed_waterbodies
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == "14150000"))
    assert latest_gauge(session, g)["vs_median_pct"] is None  # no readings
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    for i in range(300):  # three days of 15-minute readings at 1,000 cfs...
        session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=1000.0, observed_at=(now - timedelta(minutes=15 * i)).isoformat(timespec="minutes")))
    session.commit()
    assert latest_gauge(session, g)["vs_median_pct"] == 0 and latest_gauge(session, g)["median_cfs"] == 1000.0
    session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=1300.0, observed_at=(now + timedelta(minutes=15)).isoformat(timespec="minutes")))
    session.commit()  # ...then a rise
    assert latest_gauge(session, g)["vs_median_pct"] == 30
    short = session.scalar(select(Gauge).where(Gauge.site_no == "14152000"))
    for i in range(30):  # 30 readings but only 7 hours: not enough to mean anything
        session.add(GaugeReading(gauge_id=short.id, parameter="discharge_cfs", value=500.0, observed_at=(now - timedelta(minutes=15 * i)).isoformat(timespec="minutes")))
    session.commit()
    assert latest_gauge(session, short)["vs_median_pct"] is None
