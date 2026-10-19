"""USGS Water Data API adapter: parsing real captured pages, pagination, what each job asks for, and the legacy fallback."""
import json
from datetime import datetime, timedelta, timezone

import pytest
from conftest import FIX, usgs_fetch
from sqlalchemy import func, select

from app.config import get_settings
from app.models import Gauge, GaugeReading, RawFetch
from app.seed import seed_waterbodies
from app.sources import usgs

P1 = (FIX / "usgs" / "continuous_p1.json").read_bytes()
P2 = (FIX / "usgs" / "continuous_p2.json").read_bytes()
LEGACY = (FIX / "usgs" / "iv_sample.json").read_bytes()


def feature(**props):
    base = {"monitoring_location_id": "USGS-14150000", "parameter_code": "00060", "unit_of_measure": "ft^3/s", "value": "1240",
            "time": "2026-10-18T14:40:00+00:00", "approval_status": "Provisional", "qualifier": None}
    return {"type": "Feature", "properties": {**base, **props}}


def collection(*features, next_href=None):
    return json.dumps({"type": "FeatureCollection", "features": list(features), "links": [{"rel": "next", "href": next_href}] if next_href else []}).encode()


# ---- parsing real data -----------------------------------------------------------------------------------------

def test_parse_real_page():
    rows = usgs.parse(P1)
    assert len(rows) == 120 and {r["parameter"] for r in rows} == {"discharge_cfs", "gage_height_ft", "water_temp_c"}
    assert all(not r["site_no"].startswith("USGS") and r["site_no"].isdigit() for r in rows)  # 'USGS-14150000' -> '14150000'
    assert all(r["provisional"] == 1 for r in rows) and all(r["observed_at"].endswith("+00:00") for r in rows)
    assert any(r["parameter"] == "water_temp_c" and 0 < r["value"] < 30 for r in rows)  # degC, as the rest of the app expects


def test_next_link():
    assert usgs.next_link(P1).startswith("https://api.waterdata.usgs.gov/ogcapi/v1/collections/continuous/items?cursor=")
    assert usgs.next_link(collection(feature())) is None
    assert usgs.next_link(b"not json") is None


def test_unsafe_readings_are_skipped_not_guessed():
    body = collection(
        feature(),                                                         # kept
        feature(unit_of_measure="m^3/s"),                                  # a unit we did not ask for: never reinterpret
        feature(qualifier="Ice"), feature(qualifier="Eqp, Mnt"),          # not real measurements
        feature(value=None), feature(value="Ice"), feature(value="abc"),  # no usable value
        feature(monitoring_location_id="OWRD-14150000"),                   # another agency's id scheme
        feature(parameter_code="00095"),                                   # a parameter we do not store
        feature(qualifier="e"),                                            # an estimate is still a number: kept
        feature(approval_status="Approved", time="2026-10-18T14:45:00+00:00"))
    rows = usgs.parse(body)
    assert len(rows) == 3 and [r["provisional"] for r in rows] == [1, 1, 0]


def test_a_dead_sensors_ancient_last_value_is_not_stored_by_a_latest_poll(session):
    seed_waterbodies(session); fill(session, hours_ago_newest=0.2)
    fresh = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = collection(feature(parameter_code="00010", unit_of_measure="degC", value="9.5", time="2009-12-15T07:45:00+00:00"),  # sensor died in 2009
                      feature(parameter_code="00010", unit_of_measure="degC", value="10.1", time=fresh))
    assert len(usgs.parse(body)) == 2                                   # parsing alone keeps everything (historical windows are bounded by the query)
    r = usgs.run_job(session, lambda u: (200, body))                    # a latest poll drops values older than 3 days
    assert r["inserted"] == 1
    assert session.scalar(select(func.min(GaugeReading.observed_at)).where(GaugeReading.parameter == "water_temp_c")) > "2020"


@pytest.mark.parametrize("body", [b"not json", b"[]", b'{"nope": 1}', b'{"code": "InvalidQuery", "description": "bad time"}',
                                  b'{"type": "FeatureCollection"}'])
def test_unexpected_payloads_raise(body):
    with pytest.raises(usgs.ParseError):
        usgs.parse(body)


def test_urls_ask_for_the_right_thing():
    latest = usgs.url_for(["14166000", "14150000"])
    assert "/latest-continuous/items?" in latest and "monitoring_location_id=USGS-14150000,USGS-14166000" in latest and "time=" not in latest
    hist = usgs.url_for(["14150000"], "PT6H", ("00060",))
    assert "/continuous/items?" in hist and "time=PT6H" in hist and "parameter_code=00060" in hist and "00010" not in hist
    assert "limit=10000" in latest


# ---- jobs ------------------------------------------------------------------------------------------------------

def test_job_follows_pages_and_stores_each_raw(session):
    seed_waterbodies(session)
    fetch = usgs_fetch()
    r = usgs.run_job(session, fetch, period="PT1H")
    assert r["ok"] and r["inserted"] > 100
    assert len(fetch.calls) == 3                                         # page 1, page 2 via its cursor, then an empty page
    assert fetch.calls[1] == usgs.next_link(P1) and "cursor=" in fetch.calls[1]
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "usgs", RawFetch.parse_ok == 1)) == 3
    again = usgs.run_job(session, usgs_fetch(), period="PT1H")
    assert again["ok"] and again["inserted"] == 0                       # same readings, no duplicates


def test_http_failure_marks_stale_and_a_bad_second_page_keeps_the_first(session):
    from app.scheduler import source_status
    seed_waterbodies(session)
    assert usgs.run_job(session, lambda u: (503, b"x"))["ok"] is False and source_status()["usgs"]["stale"] is True
    calls = []

    def flaky(u):
        calls.append(u)
        return (200, P1) if len(calls) == 1 else (200, b'{"code": "boom"}')
    r = usgs.run_job(session, flaky, period="PT1H")
    assert r["ok"] is False and r["inserted"] > 0                       # page 1 is real data and is kept
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "usgs", RawFetch.parse_ok == 0)) >= 1


def fill(session, hours_ago_newest, span_days=3):
    """Pretend every gauge has history: a span of discharge readings ending `hours_ago_newest` hours ago."""
    now = datetime.now(timezone.utc)
    for g in session.scalars(select(Gauge).where(Gauge.agency == "USGS")):
        for t in (now - timedelta(hours=hours_ago_newest, days=span_days), now - timedelta(hours=hours_ago_newest)):
            session.add(GaugeReading(gauge_id=g.id, parameter="discharge_cfs", value=100.0, provisional=1, observed_at=t.isoformat(timespec="minutes")))
    session.commit()


def asked(session):
    calls = []
    usgs.run_job(session, lambda u: (calls.append(u) or (200, collection())))
    return calls[0]


def test_first_run_backfills_a_week_of_discharge_only(session):
    seed_waterbodies(session)
    url = asked(session)
    assert "/continuous/items?" in url and "time=P7D" in url and "parameter_code=00060" in url and "00010" not in url


def test_routine_poll_asks_only_for_the_latest_values(session):
    seed_waterbodies(session); fill(session, hours_ago_newest=0.2)
    assert "/latest-continuous/items?" in asked(session)


def test_a_stale_gauge_triggers_a_bounded_gap_fill(session):
    seed_waterbodies(session); fill(session, hours_ago_newest=4.5)
    url = asked(session)
    assert "/continuous/items?" in url and "time=PT6H" in url and "00060,00065,00010" in url   # ceil(4.5h)+1, all parameters
    session.query(GaugeReading).delete(); session.commit(); fill(session, hours_ago_newest=100)
    assert "time=PT24H" in asked(session)                                  # never more than a day


def test_a_gauge_that_cannot_reach_two_days_does_not_cause_a_weekly_fetch_every_poll(session):
    seed_waterbodies(session)
    assert "time=P7D" in asked(session)                                    # first poll: backfill
    again = asked(session)                                                 # an hour later nothing has changed
    assert "time=P7D" not in again                                         # not another week-long download


def test_legacy_fallback_still_works_until_usgs_retires_it(session, monkeypatch):
    monkeypatch.setenv("USGS_API", "legacy"); get_settings.cache_clear()
    seed_waterbodies(session)
    calls = []

    def fetch(u):
        calls.append(u)
        return 200, LEGACY
    r = usgs.run_job(session, fetch)
    assert r["ok"] and r["inserted"] > 0 and "waterservices.usgs.gov" in calls[0] and len(calls) == 1
    assert usgs.parse_legacy(LEGACY) and {x["parameter"] for x in usgs.parse_legacy(LEGACY)} <= {"discharge_cfs", "gage_height_ft", "water_temp_c"}
    body = json.loads(LEGACY); ts = body["value"]["timeSeries"][0]
    ts["values"][0]["value"][0]["value"] = "-999999"; ts["values"][0]["value"][1]["value"] = "Ice"
    assert len(usgs.parse_legacy(json.dumps(body))) == len(usgs.parse_legacy(LEGACY)) - 2
    monkeypatch.delenv("USGS_API"); get_settings.cache_clear()


# ---- water quality (the Tualatin at Dilley reports temperature, dissolved oxygen, pH, turbidity and conductance) -----------------
TUALATIN = (FIX / "usgs" / "tualatin_latest.json").read_bytes()


def test_real_tualatin_response_yields_flow_stage_temperature_and_the_four_quality_readings():
    rows = usgs.parse(TUALATIN)
    dilley = {r["parameter"]: r["value"] for r in rows if r["site_no"] == "14203500"}
    assert {"discharge_cfs", "gage_height_ft", "water_temp_c", "dissolved_oxygen_mgl", "ph", "turbidity_fnu", "conductance_uscm"} <= set(dilley)
    assert 0 < dilley["dissolved_oxygen_mgl"] < 20 and 5 < dilley["ph"] < 10 and dilley["conductance_uscm"] > 0
    west_linn = {r["parameter"] for r in rows if r["site_no"] == "14207500"}
    assert west_linn == {"discharge_cfs", "gage_height_ft"}  # a gauge without quality sensors simply has none
    assert not any(r["parameter"] in ("ph",) and r["site_no"] == "14207500" for r in rows)


def test_a_quality_reading_in_an_unexpected_unit_is_skipped_not_reinterpreted():
    body = json.dumps({"type": "FeatureCollection", "features": [
        feature(parameter_code="00300", unit_of_measure="mg/l", value="9.5"),
        feature(parameter_code="00300", unit_of_measure="percent", value="95"),      # percent saturation: not the same thing
        feature(parameter_code="00400", unit_of_measure="pH Units", value="7.5"),
        feature(parameter_code="63680", unit_of_measure="_FNU", value="2.3"),
        feature(parameter_code="00095", unit_of_measure="mS/cm", value="0.073")]}).encode()  # milli- not micro-siemens
    got = {(r["parameter"], r["value"]) for r in usgs.parse(body)}
    assert got == {("dissolved_oxygen_mgl", 9.5), ("ph", 7.5), ("turbidity_fnu", 2.3)}


def test_the_legacy_fallback_is_still_asked_only_for_the_original_three_parameters():
    assert "parameterCd=00060,00065,00010&" in usgs.url_for_legacy(["14203500"])
