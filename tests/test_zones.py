"""Zones beyond Willamette: the seed, ranking isolation, the multi-zone stocking job and the endpoints."""
from datetime import date

from conftest import FIX
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import zones
from app.config import get_settings
from app.models import Gauge, StockingSnapshot, Waterbody, WaterbodyAlias
from app.planner import rank
from app.seed import SEED, seed_waterbodies
from app.sources import odfw_stocking
from app.zones import central, northeast, northwest, southeast, southwest

PAGES = [(FIX / "odfw_stocking" / f"central_p{i}.html").read_bytes() for i in range(4)]
NW_PAGES = [(FIX / "odfw_stocking" / f"northwest_p{i}.html").read_bytes() for i in range(4)]
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
def test_the_zone_seeds_are_consistent_and_never_invent_a_coordinate():
    allmods = [("willamette", SEED)] + [(m.ZONE, m.SEED) for m in zones.MODULES]
    names = [n[0] for _, sd in allmods for n in sd]
    assert len(names) == len(set(names))  # no waterbody name is used twice across zones
    for zone, sd in allmods:  # a stocking label is unique within its zone; ODFW reuses some across zones (LOST LAKE), which the alias namespace handles
        labels = [l for n in sd for l in n[4]]
        assert len(labels) == len(set(labels)), zone
    for m, box in ((central, (43.3, 45.8, -122.3, -119.4)), (northwest, (43.5, 46.3, -124.4, -122.7)), (southwest, (41.9, 43.95, -124.7, -121.9)),
                   (northeast, (44.3, 46.1, -120.6, -116.4)), (southeast, (41.9, 44.8, -122.4, -116.4))):
        pinned = {s_[0] for s_ in m.SEED if s_[2] is not None}
        assert pinned == set(m.PINS) and {v[0] for v in m.PINS.values()} <= {"osm", "likely"}, m.ZONE  # every pin says how it was found
        for name, kind, lat, lon, _ in m.SEED:
            if lat is not None:
                assert box[0] <= lat <= box[1] and box[2] <= lon <= box[3], name
    assert len(central.SEED) == 35 and sum(1 for s_ in central.SEED if s_[2] is None) == 13
    assert len(northwest.SEED) == 33 and sum(1 for s_ in northwest.SEED if s_[2] is None) == 11
    assert [(len(m.SEED), sum(1 for s_ in m.SEED if s_[2] is None)) for m in (southwest, northeast, southeast)] == [(43, 21), (49, 40), (36, 23)]


def test_seeding_creates_both_zones_idempotently_and_never_overwrites_a_pin_a_person_set(session):
    seed_waterbodies(session)
    n = session.scalar(select(func.count()).select_from(Waterbody))
    assert session.scalar(select(func.count()).select_from(Waterbody).where(Waterbody.zone == "central")) == 35
    assert session.scalar(select(func.count()).select_from(Waterbody).where(Waterbody.zone == "northwest")) == 33
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
    assert [z.key for z in zones.enabled(get_settings().enabled_zones)] == ["willamette", "central", "northwest", "southwest", "northeast", "southeast"]
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
    assert len(wil) == 16 and len(cen) == 8 and len(c.get("/api/gauges", params={"zone": "northwest"}).json()["gauges"]) == 7
    assert {g["site_no"] for g in cen} == {g[0] for g in central.GAUGES} and not ({g["site_no"] for g in wil} & {g["site_no"] for g in cen})
    assert session.scalar(select(func.count()).select_from(Gauge).where(Gauge.zone.is_(None))) == 0


def test_every_real_northwest_row_resolves_and_a_label_shared_with_another_zone_stays_separate(session):
    seed_waterbodies(session)
    for i, page in enumerate(PAGES):
        odfw_stocking.ingest_page(session, f"https://example.test/s?field_zone_value=1&page={i}", 200, page, i)
    for i, page in enumerate(NW_PAGES):
        odfw_stocking.ingest_page(session, f"https://example.test/s?field_zone_value=3&page={i}", 200, page, i)
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == 122 + 117
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.confirmed == 0)) == 0  # nothing left for review
    # "LOST LAKE" is on both schedules: two aliases, one per zone, pointing at two different waterbodies
    lost = session.scalars(select(WaterbodyAlias).where(WaterbodyAlias.alias_text == "LOST LAKE")).all()
    assert {a.source for a in lost} == {"odfw_stocking:central", "odfw_stocking:northwest", "odfw_stocking:northeast"}
    assert {session.get(Waterbody, a.waterbody_id).zone for a in lost} == {"central", "northwest", "northeast"}
    c = client()
    nw = {f["properties"]["name"] for f in c.get("/api/map", params={"zone": "northwest"}).json()["features"] if f["properties"]["layer"] == "stocking"}
    cen = {f["properties"]["name"] for f in c.get("/api/map", params={"zone": "central"}).json()["features"] if f["properties"]["layer"] == "stocking"}
    assert "Lost Lake (Northwest)" in nw and "Lost Lake" in cen and not (nw & cen)


def test_snapshots_attached_to_another_zones_alias_are_repointed_by_odfws_own_zone_column(session):
    from app.seed import repair_snapshot_aliases
    seed_waterbodies(session)
    # the old behaviour: Central's CLEAR LAKE rows were attached to Willamette's "Clear Lake (McKenzie)" alias
    wil_alias = session.scalar(select(WaterbodyAlias).where(WaterbodyAlias.alias_text == "CLEAR LAKE", WaterbodyAlias.source == "odfw_stocking"))
    cen_alias = session.scalar(select(WaterbodyAlias).where(WaterbodyAlias.alias_text == "CLEAR LAKE", WaterbodyAlias.source == "odfw_stocking:central"))
    assert wil_alias is not None and cen_alias is not None and wil_alias.id != cen_alias.id
    session.add_all([StockingSnapshot(scraped_at="2026-10-18T00:00:00+00:00", week_of="2027-05-03", alias_id=wil_alias.id, zone_office="Central / The Dalles", legals=100, total=100),
                     StockingSnapshot(scraped_at="2026-10-18T00:00:00+00:00", week_of="2026-10-12", alias_id=wil_alias.id, zone_office="Willamette / Springfield", legals=50, total=50)])
    session.commit()
    assert repair_snapshot_aliases(session) == 1
    snaps = session.scalars(select(StockingSnapshot).order_by(StockingSnapshot.id)).all()
    assert snaps[0].alias_id == cen_alias.id and snaps[1].alias_id == wil_alias.id  # only the Central row moved
    assert repair_snapshot_aliases(session) == 0  # idempotent


def test_the_migration_moves_existing_other_zone_aliases_into_their_zone_namespace(session):
    from importlib import import_module

    from sqlalchemy import text
    seed_waterbodies(session)
    # the state before the migration: Central's aliases (except CLEAR LAKE, which never got its own) lived under the original name
    session.execute(text("UPDATE waterbody_alias SET source = 'odfw_stocking' WHERE source = 'odfw_stocking:central' AND alias_text <> 'CLEAR LAKE'"))
    session.commit()
    mig = import_module("app.migrations.versions.0008_zone_aliases")

    class Op:
        @staticmethod
        def execute(sql):
            session.execute(text(sql))

    mig.op = Op
    mig.upgrade()
    session.commit()
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.source == "odfw_stocking:central")) == 36
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.source == "odfw_stocking")) > 50  # Willamette keeps the original


def test_seeding_confirms_a_proposal_the_ingest_left_but_never_changes_a_confirmed_alias(session):
    from app.http import now_iso
    ingest = lambda: odfw_stocking.ingest_page(session, "https://example.test/s?field_zone_value=3&page=0", 200, NW_PAGES[0], 0)
    seed_waterbodies(session)
    session.query(WaterbodyAlias).filter(WaterbodyAlias.source == "odfw_stocking:northwest").delete()  # as if the schedule arrived before the seed
    session.commit()
    ingest()
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.source == "odfw_stocking:northwest", WaterbodyAlias.confirmed == 0)) > 0
    decided = session.scalar(select(WaterbodyAlias).where(WaterbodyAlias.alias_text == "ALDER LAKE", WaterbodyAlias.source == "odfw_stocking:northwest"))
    other = session.scalar(select(Waterbody).where(Waterbody.name == "Buck Lake"))
    decided.waterbody_id, decided.confirmed = other.id, 1  # a person confirmed this label to a different water
    session.commit()
    seed_waterbodies(session)
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.source == "odfw_stocking:northwest", WaterbodyAlias.confirmed == 0)) == 0
    assert decided.waterbody_id == other.id  # left alone


import pytest  # noqa: E402

ROWS = {"southwest": (5, 164, southwest, 5), "northeast": (3, 98, northeast, 2), "southeast": (3, 74, southeast, 4)}


@pytest.mark.parametrize("key", list(ROWS))
def test_every_real_row_of_a_later_zone_resolves_to_one_of_its_own_waterbodies(session, key):
    pages, rows, mod, value = ROWS[key]
    seed_waterbodies(session)
    for i in range(pages):
        html = (FIX / "odfw_stocking" / f"{key}_p{i}.html").read_bytes()
        odfw_stocking.ingest_page(session, f"https://example.test/s?field_zone_value={value}&page={i}", 200, html, i)
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == rows
    assert session.scalar(select(func.count()).select_from(WaterbodyAlias).where(WaterbodyAlias.confirmed == 0)) == 0
    own = {s_[0] for s_ in mod.SEED}
    hit = set(session.scalars(select(Waterbody.name).join(WaterbodyAlias, WaterbodyAlias.waterbody_id == Waterbody.id)
                              .join(StockingSnapshot, StockingSnapshot.alias_id == WaterbodyAlias.id)))
    assert hit and hit <= own  # every row landed on this zone's waters, none on another zone's
    z = client().get("/api/zones").json()["zones"]
    assert next(x for x in z if x["key"] == key)["gauges"] == len(mod.GAUGES) > 0


def test_the_pin_list_names_unpinned_and_likely_waters_and_drops_one_once_a_person_moves_it(session):
    from conftest import signed_in_client
    seed_waterbodies(session)
    c = signed_in_client("boss", admin=True)
    items = c.get("/api/admin/pins").json()
    by = {i["name"]: i for i in items}
    assert by["East Lake"]["status"] == "none" and by["East Lake"]["zone"] == "central"
    assert by["Hebo Lake"]["status"] == "likely" and "point of interest" in by["Hebo Lake"]["note"] or "Hebo" in by["Hebo Lake"]["note"]
    assert "Hosmer Lake" not in by  # a clean OSM match is not a guess
    assert sum(1 for i in items if i["zone"] == "central" and i["status"] == "none") == 13
    hh = by["Hebo Lake"]["id"]
    assert c.post(f"/api/admin/waterbodies/{hh}/coords", json={"lat": 45.24, "lon": -123.8}, headers={"X-Holdover": "1"}).status_code == 200
    assert "Hebo Lake" not in {i["name"] for i in c.get("/api/admin/pins").json()}  # moved on purpose: no longer a guess
    el = by["East Lake"]["id"]
    c.post(f"/api/admin/waterbodies/{el}/coords", json={"lat": 43.72, "lon": -121.2}, headers={"X-Holdover": "1"})
    assert "East Lake" not in {i["name"] for i in c.get("/api/admin/pins").json()}
    seed_waterbodies(session)  # a re-seed never undoes a placed pin
    assert session.get(Waterbody, el).lat == 43.72
