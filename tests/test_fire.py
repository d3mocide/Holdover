"""Fire card: ODF fire danger and NIFC perimeters. Real captured responses, pure geometry, and failure behaviour."""
import json
from datetime import datetime, timezone

import pytest
from conftest import FIX
from sqlalchemy import func, select

from app import geo
from app.models import FireDanger, FireNearby, RawFetch, Waterbody
from app.seed import seed_waterbodies
from app.sources import nifc, odf_fire

ODF = (FIX / "fire" / "odf_danger.json").read_bytes()
NIFC = (FIX / "fire" / "nifc_current.json").read_bytes()
NOW = datetime(2026, 10, 18, 16, tzinfo=timezone.utc)


def square(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


# ---- geometry ---------------------------------------------------------------------------------------------------
def test_point_in_polygon_with_a_hole_and_a_multipolygon():
    donut = {"type": "Polygon", "coordinates": [square(0, 0, 10, 10), square(4, 4, 6, 6)]}
    assert geo.contains(2, 2, donut) and not geo.contains(5, 5, donut) and not geo.contains(20, 20, donut)
    multi = {"type": "MultiPolygon", "coordinates": [[square(0, 0, 1, 1)], [square(5, 5, 6, 6)]]}
    assert geo.contains(5.5, 5.5, multi) and not geo.contains(3, 3, multi)


def test_nearest_vertex_distance_is_in_kilometres():
    sq = {"type": "Polygon", "coordinates": [square(-122.0, 44.0, -121.9, 44.1)]}
    assert 70 < geo.nearest_vertex_km(44.0, -122.9, sq) < 80  # about 0.9 degrees of longitude at 44 N


# ---- ODF fire danger ----------------------------------------------------------------------------------------------
def test_odf_parses_the_real_response():
    zones = odf_fire.parse(ODF)
    assert len(zones) == 63 and {z["level"] for z in zones} <= {1, 2, 3, 4}
    assert all(z["area"] and z["geometry"]["type"] in ("Polygon", "MultiPolygon") for z in zones)


def test_odf_rejects_error_objects_empty_and_garbage():
    for bad in (b'{"error": {"code": 500, "message": "boom"}}', b'{"type": "FeatureCollection", "features": []}', b"<html>", b"[]"):
        with pytest.raises(odf_fire.ParseError):
            odf_fire.parse(bad)


def test_odf_cautious_reading_when_zones_overlap():
    a = {"area": "A", "level": 1, "geometry": {"type": "Polygon", "coordinates": [square(0, 0, 2, 2)]}}
    b = {"area": "B", "level": 3, "geometry": {"type": "Polygon", "coordinates": [square(1, 1, 3, 3)]}}
    assert odf_fire.zone_for([a, b], 1.5, 1.5)["area"] == "B" and odf_fire.zone_for([a, b], 5, 5) is None


def run(session, mod, body, status=200):
    return mod.run_job(session, lambda url: (status, body))


def test_odf_job_stores_raw_first_and_reports_a_level_for_covered_waterbodies(session):
    seed_waterbodies(session)
    out = run(session, odf_fire, ODF)
    assert out["ok"] and out["zones"] == 63 and out["waterbodies_in_a_zone"] > 10
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "odf_fire", RawFetch.parse_ok == 1)) == 1
    det = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    cur = odf_fire.current(session, det.id)
    assert cur["covered"] and cur["area"] == "CM-2" and cur["level"] == 1 and cur["label"] == "Low"
    assert cur["page"].startswith("https://gisapps.odf.oregon.gov")


def test_odf_outside_every_zone_says_so_and_failure_keeps_the_last_reading(session):
    seed_waterbodies(session)
    assert odf_fire.current(session, 1) is None  # nothing fetched yet
    run(session, odf_fire, ODF)
    uncovered = session.scalar(select(Waterbody).where(~Waterbody.id.in_(select(FireDanger.waterbody_id)), Waterbody.lat.is_not(None)))
    assert odf_fire.current(session, uncovered.id)["covered"] is False
    before = session.scalar(select(func.count()).select_from(FireDanger))
    assert run(session, odf_fire, b"nonsense") == {"ok": False}
    assert run(session, odf_fire, b"", status=503) == {"ok": False}
    det = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    assert odf_fire.current(session, det.id)["covered"] and session.scalar(select(func.count()).select_from(FireDanger)) == before
    assert session.scalar(select(RawFetch).where(RawFetch.source == "odf_fire").order_by(RawFetch.id.desc())).parse_ok == 0


# ---- NIFC perimeters --------------------------------------------------------------------------------------------
def test_nifc_parses_the_real_response_and_filters_to_active_wildfires():
    fires = nifc.parse(NIFC)
    assert len(fires) == 16
    names = {f["name"] for f in nifc.active(fires, NOW)}
    assert names == {"Grasshopper", "Austin", "Hagen", "407 DET"}  # 100% contained, prescribed burns and month-old updates dropped
    assert "Bird Track 610/607A RX" not in names


def test_nifc_active_rules():
    base = {"name": "x", "acres": 1, "geometry": {}, "type": "WF", "updated": "2026-10-17T00:00+00:00", "contained": 50}
    assert nifc.active([base], NOW)
    assert nifc.active([{**base, "contained": None}], NOW)  # a new fire has no containment figure yet
    assert not nifc.active([{**base, "contained": 100}], NOW)
    assert not nifc.active([{**base, "type": "RX"}], NOW)
    assert not nifc.active([{**base, "updated": "2026-08-01T00:00+00:00"}], NOW)


def test_nifc_empty_is_valid_but_errors_are_not():
    assert nifc.parse(b'{"type": "FeatureCollection", "features": []}') == []
    for bad in (b'{"error": {"code": 400}}', b"<html>", b"[]", b'{"nope": 1}'):
        with pytest.raises(nifc.ParseError):
            nifc.parse(bad)


def test_nifc_job_end_to_end(session, monkeypatch):
    seed_waterbodies(session)
    real = nifc.active
    monkeypatch.setattr(nifc, "active", lambda fires, now=None: real(fires, NOW))
    out = run(session, nifc, NIFC)
    assert out["ok"] and out["active_fires"] == 4 and out["near_waterbodies"] > 0
    harriet = session.scalar(select(Waterbody).where(Waterbody.name == "Harriet Lake"))
    cur = nifc.current(session, harriet.id)
    assert cur["fires"][0]["name"] == "Austin" and cur["fires"][0]["distance_km"] < 10
    assert [f["distance_km"] for f in cur["fires"]] == sorted(f["distance_km"] for f in cur["fires"])
    assert all(f["distance_km"] <= nifc.NEAR_KM for f in cur["fires"])
    far = session.scalar(select(Waterbody).where(Waterbody.name == "Alton Baker Canal"))
    assert nifc.current(session, far.id)["fires"] == []  # fetched, and nothing near: different from "never fetched"
    assert run(session, nifc, b"nope") == {"ok": False}
    assert nifc.current(session, harriet.id)["fires"]  # the last good fetch is still what is shown
    assert session.scalar(select(func.count()).select_from(FireNearby)) == out["near_waterbodies"]


def test_conditions_carry_both_fire_blocks(session):
    from datetime import date

    from app.conditions import conditions
    seed_waterbodies(session)
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    c = conditions(session, wb, date(2026, 10, 18))
    assert c["fire"] == {"danger": None, "nearby": None}  # before any fetch: unknown, not "no fire"
    run(session, odf_fire, ODF)
    assert conditions(session, wb, date(2026, 10, 18))["fire"]["danger"]["label"] == "Low"
