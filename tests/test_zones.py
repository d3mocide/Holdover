"""Zones beyond Willamette: the seed, ranking isolation, the multi-zone stocking job and the endpoints."""
from datetime import date

from conftest import FIX
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import zones
from app.models import Gauge, StockingSnapshot, Waterbody, WaterbodyAlias
from app.planner import rank
from app.seed import SEED, seed_waterbodies
from app.sources import odfw_stocking
from app.zones import central

PAGES = [(FIX / "odfw_stocking" / f"central_p{i}.html").read_bytes() for i in range(4)]
TODAY = date(2026, 10, 14)


def client():
    from app.main import app
    return TestClient(app)


def central_fetch(url):
    """Serves the four real Central pages for zone 1 and the Willamette fixture for zone 6."""
    page = int(url.split("page=")[1].split("&")[0]) if "page=" in url else 0
    if "field_zone_value=1" in url:
        return 200, PAGES[page] if page < 4 else b"<html><body><table><thead><tr><th>x</th></tr></thead></table></body></html>"
    return 200, (FIX / "odfw_stocking" / "wv_p0.html").read_bytes() if page == 0 else b""


# ---- the seed -----------------------------------------------------------------------------------------------------
def test_the_zone_seed_is_consistent_and_never_invents_a_coordinate():
    names = [s[0] for s in SEED] + [s[0] for s in central.SEED]
    assert len(names) == len(set(names))  # no waterbody name is used twice across zones
    labels = [l for s in SEED for l in s[4]] + [l for s in central.SEED for l in s[4]]
    assert len(labels) == len(set(labels))  # a stocking label points at exactly one waterbody
    pinned = {s[0] for s in central.SEED if s[2] is not None}
    assert pinned == set(central.PINS) and {v[0] for v in central.PINS.values()} <= {"osm", "likely"}  # every pin says how it was found
    for name, kind, lat, lon, _ in central.SEED:
        if lat is not None:
            assert 43.3 <= lat <= 45.8 and -122.3 <= lon <= -119.4, name  # inside the Central zone's area
    assert len(central.SEED) == 35 and sum(1 for s in central.SEED if s[2] is None) == 13


def test_seeding_creates_both_zones_idempotently_and_never_overwrites_a_pin_a_person_set(session):
    seed_waterbodies(session)
    n = session.scalar(select(func.count()).select_from(Waterbody))
    assert session.scalar(select(func.count()).select_from(Waterbody).where(Waterbody.zone == "central")) == 35
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Hosmer Lake"))
    wb.lat, wb.lon = 43.9, -121.7  # a person moved it
    other = session.scalar(select(Waterbody).where(Waterbody.name == "East Lake"))
    other.lat = other.lon = None
    session.commit()
    assert seed_waterbodies(session) == 0 and session.scalar(select(func.count()).select_from(Waterbody)) == n
    assert (wb.lat, wb.lon) == (43.9, -121.7) and other.lat is None


def test_every_label_on_the_real_central_schedule_resolves_to_a_waterbody(session):
    seed_waterbodies(session)
    for i, page in enumerate(PAGES):
        odfw_stocking.ingest_page(session, f"https://example.test/s?field_zone_value=1&page={i}", 200, page, i)
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == 122
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.confirmed == 0)) == 0  # nothing left for review


# ---- the job --------------------------------------------------------------------------------------------------------
def test_the_scheduled_job_fetches_each_enabled_zone_and_one_failure_does_not_stop_the_rest(session):
    seen = []

    def fetch(url):
        seen.append(url)
        return (500, b"") if "field_zone_value=6" in url else central_fetch(url)

    out = odfw_stocking.run_zones(session, fetch, TODAY, zones.enabled("willamette,central"))
    assert out["ok"] is False and set(out["zones"]) == {"willamette", "central"}
    assert out["zones"]["willamette"]["ok"] is False and out["zones"]["central"]["ok"] is True
    assert out["zones"]["central"]["rows_inserted"] == 122
    assert any("field_zone_value=1" in u for u in seen) and any("field_zone_value=6" in u for u in seen)


def test_unknown_zone_keys_are_ignored_and_the_default_is_both_zones():
    assert [z.key for z in zones.enabled("central, nowhere")] == ["central"]
    assert [z.key for z in zones.enabled("willamette,central")] == ["willamette", "central"]
    assert zones.BY_KEY["central"].stocking_value == 1 and zones.BY_KEY["willamette"].stocking_value == 6


# ---- ranking and the endpoints ----------------------------------------------------------------------------------------
def loaded(session):
    seed_waterbodies(session)
    for i, page in enumerate(PAGES):
        odfw_stocking.ingest_page(session, f"https://example.test/s?field_zone_value=1&page={i}", 200, page, i)
    odfw_stocking.ingest_page(session, "https://example.test/s?field_zone_value=6&page=0", 200, (FIX / "odfw_stocking" / "wv_p0.html").read_bytes(), 0)


def test_ranking_only_includes_the_zones_own_waterbodies(session):
    loaded(session)
    cen = {s.wb.name for s in rank(session, TODAY, "trout", zone="central")}
    wil = {s.wb.name for s in rank(session, TODAY, "trout", zone="willamette")}
    assert cen and wil and not (cen & wil)
    central_names = {s[0] for s in central.SEED}
    assert cen <= central_names and wil.isdisjoint(central_names)


def test_the_endpoints_filter_by_zone_and_reject_an_unknown_one(session):
    loaded(session)
    c = client()
    zs = {z["key"]: z for z in c.get("/api/zones").json()["zones"]}
    assert zs["central"]["waterbodies"] == 35 and zs["central"]["pinned"] == 22 and zs["willamette"]["waterbodies"] > 50
    feats = c.get("/api/map", params={"zone": "central"}).json()["features"]
    assert feats and {f["properties"]["name"] for f in feats if f["properties"]["layer"] == "stocking"} <= {s[0] for s in central.SEED}
    assert c.get("/api/spots", params={"zone": "central", "date": "2026-10-14"}).json()["zone"] == "central"
    assert c.get("/api/spots", params={"zone": "mars"}).status_code == 422 and c.get("/api/briefing", params={"zone": "mars"}).status_code == 422
    sched = c.get("/api/schedule", params={"zone": "central", "start": "2026-01-01", "end": "2028-12-31"}).json()
    assert sched["weeks"] and all(r["name"] in {s[0] for s in central.SEED} for w in sched["weeks"] for r in w["waterbodies"])


def test_gauges_belong_to_a_zone_and_the_endpoint_filters_by_it(session):
    seed_waterbodies(session)
    c = client()
    wil = c.get("/api/gauges").json()["gauges"]
    cen = c.get("/api/gauges", params={"zone": "central"}).json()["gauges"]
    assert len(wil) == 16 and len(cen) == 8
    assert {g["site_no"] for g in cen} == {g[0] for g in central.GAUGES} and not ({g["site_no"] for g in wil} & {g["site_no"] for g in cen})
    assert session.scalar(select(func.count()).select_from(Gauge).where(Gauge.zone.is_(None))) == 0
