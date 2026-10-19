"""NOAA NWPS river flood status: the real captured response, synthetic flooding cases (none occur on a dry day), staleness."""
import json
from datetime import datetime, timezone

import pytest
from conftest import FIX
from sqlalchemy import func, select

from app.models import RawFetch, RiverStatus
from app.seed import GAUGES, seed_waterbodies
from app.sources import nwps

BODY = (FIX / "nwps_gauges.json").read_bytes()
NOW = datetime(2026, 10, 18, 17, tzinfo=timezone.utc)


def gauge(lid, cat="no_flooding", fc_cat="fcst_not_current", fc=-999, obs=6.0, valid="2026-10-18T16:00:00Z"):
    return {"lid": lid, "status": {"observed": {"primary": obs, "primaryUnit": "ft", "secondary": 4.5, "secondaryUnit": "kcfs", "floodCategory": cat, "validTime": valid},
                                   "forecast": {"primary": fc, "primaryUnit": "ft" if fc != -999 else "", "secondary": -999, "secondaryUnit": "", "floodCategory": fc_cat,
                                                "validTime": "2026-10-20T12:00:00Z"}}}


def body(*gs):
    return json.dumps({"gauges": list(gs)}).encode()


def run(session, b, status=200):
    return nwps.run_job(session, lambda url: (status, b))


def test_mapping_points_only_at_known_gauges_and_is_unique():
    from app.zones import MODULES
    sites = {g[0] for g in GAUGES} | {g[0] for m in MODULES for g in m.GAUGES}
    assert set(nwps.LIDS) <= sites and len(set(nwps.LIDS.values())) == len(nwps.LIDS)
    assert "14150000" not in nwps.LIDS and "14153500" not in nwps.LIDS  # NWPS has only reservoir gauges there


def test_every_mapped_gauge_is_in_the_real_response_with_the_same_name_family():
    rows = nwps.parse(BODY)
    assert set(rows) == set(nwps.LIDS.values())
    assert rows["ALBO3"]["category"] == "no_flooding" and rows["ALBO3"]["stage_ft"] is not None
    assert rows["ALBO3"]["fc_category"] == "no_flooding" and rows["ALBO3"]["fc_stage_ft"] is not None


def test_missing_values_are_none_not_minus_999():
    r = nwps.parse(body(gauge("ALBO3", fc_cat="fcst_not_current")))["ALBO3"]
    assert r["fc_category"] is None and r["fc_stage_ft"] is None and r["stage_ft"] == 6.0
    assert nwps.parse(body(gauge("ALBO3", obs=-999)))["ALBO3"]["stage_ft"] is None


def test_rejects_errors_garbage_and_a_response_without_our_gauges():
    for bad in (b'{"error": 1}', b"<html>", b"[]", body(gauge("ZZZZZ"))):
        with pytest.raises(nwps.ParseError):
            nwps.parse(bad)


def test_job_stores_raw_first_and_reports_status_by_usgs_site(session):
    out = run(session, BODY)
    assert out == {"ok": True, "gauges": len(nwps.LIDS)}
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "nwps", RawFetch.parse_ok == 1)) == 1
    s = nwps.for_site(session, "14174000", now=datetime.now(timezone.utc))
    assert s["category"] == "no_flooding" and s["label"] == "No flooding" and s["elevated"] is False
    assert s["page"] == "https://water.noaa.gov/gauges/ALBO3"
    assert nwps.for_site(session, "14150000") is None  # unmapped


def test_flooding_and_forecast_are_reported_and_flagged(session):
    run(session, body(gauge("ALBO3", cat="minor", obs=22.5, fc_cat="moderate", fc=27.1)))
    s = nwps.for_site(session, "14174000", now=NOW)
    assert s["elevated"] is True and s["label"] == "Minor flooding" and s["stage_ft"] == 22.5
    assert s["forecast"] == {"category": "moderate", "label": "Moderate flooding", "stage_ft": 27.1, "valid_time": "2026-10-20T12:00:00Z"}
    assert s["stale"] is False


def test_old_observation_is_stale_and_undefined_categories_say_nothing(session):
    run(session, body(gauge("ALBO3", valid="2026-10-18T05:00:00Z"), gauge("HARO3", cat="not_defined"), gauge("SLMO3", cat="obs_not_current")))
    assert nwps.for_site(session, "14174000", now=NOW)["stale"] is True
    assert nwps.for_site(session, "14166000", now=NOW) is None and nwps.for_site(session, "14191000", now=NOW) is None


def test_failure_keeps_the_last_good_status(session):
    assert nwps.for_site(session, "14174000") is None  # never fetched
    run(session, BODY)
    n = session.scalar(select(func.count()).select_from(RiverStatus))
    assert run(session, b"nope") == {"ok": False} and run(session, b"", status=503) == {"ok": False}
    assert session.scalar(select(func.count()).select_from(RiverStatus)) == n
    assert nwps.for_site(session, "14174000", now=datetime.now(timezone.utc))["category"] == "no_flooding"
    assert session.scalar(select(RawFetch).where(RawFetch.source == "nwps").order_by(RawFetch.id.desc())).parse_ok == 0


def test_gauge_bundle_carries_flood(session):
    from app.conditions import latest_gauge
    from app.models import Gauge
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == "14174000"))
    assert latest_gauge(session, g)["flood"] is None
    run(session, BODY)
    assert latest_gauge(session, g)["flood"]["category"] == "no_flooding"
