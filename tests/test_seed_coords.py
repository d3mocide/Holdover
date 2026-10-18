from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models import Waterbody
from app.seed import COORD_UPDATES, SEED, seed_waterbodies

ORIG = {name: (lat, lon) for name, _k, lat, lon, _l in SEED}


def wb(session, name):
    return session.scalar(select(Waterbody).where(Waterbody.name == name))


def test_fresh_seed_uses_verified_coordinates(session):
    seed_waterbodies(session)
    lat, lon, _ = COORD_UPDATES["Dexter Reservoir"]
    assert (wb(session, "Dexter Reservoir").lat, wb(session, "Dexter Reservoir").lon) == (lat, lon)
    # a previously coordinate-less water gets a pin; an unverified one keeps its original value
    assert wb(session, "Turner Lake").lat is not None
    assert (wb(session, "Alton Baker Canal").lat, wb(session, "Alton Baker Canal").lon) == ORIG["Alton Baker Canal"]


def test_existing_rows_with_original_values_are_corrected_once(session):
    seed_waterbodies(session)
    w = wb(session, "Green Peter Reservoir")
    w.lat, w.lon = ORIG["Green Peter Reservoir"]  # as an older database would hold it
    session.commit()
    seed_waterbodies(session)
    session.refresh(w)
    assert (w.lat, w.lon) == COORD_UPDATES["Green Peter Reservoir"][:2]


def test_deliberately_set_coordinates_are_never_overwritten(session):
    seed_waterbodies(session)
    w = wb(session, "Green Peter Reservoir")
    w.lat, w.lon = 44.0, -122.0
    session.commit()
    seed_waterbodies(session)
    session.refresh(w)
    assert (w.lat, w.lon) == (44.0, -122.0)


def test_every_update_names_a_seed_row_and_stays_in_oregon_zone():
    names = {n for n, *_ in SEED}
    for name, (lat, lon, how) in COORD_UPDATES.items():
        assert name in names, name
        assert how in {"osm", "snap", "likely"}
        assert 43.4 < lat < 46.3 and -123.9 < lon < -121.4, name


AUTH = {"Authorization": "Bearer testtoken"}


def test_admin_can_place_move_and_clear_a_pin(session):
    from app.main import app

    seed_waterbodies(session)
    w = wb(session, "Haldeman Pond")  # no coordinate in the seed
    assert w.lat is None
    c = TestClient(app)
    url = f"/api/admin/waterbodies/{w.id}/coords"
    assert c.post(url, json={"lat": 44.0, "lon": -123.0}).status_code == 401  # needs the token
    assert c.post(url, json={"lat": 44.0, "lon": -123.0}, headers=AUTH).json()["lat"] == 44.0
    session.refresh(w)
    assert (w.lat, w.lon) == (44.0, -123.0)
    assert c.post(url, json={"lat": 44.0}, headers=AUTH).status_code == 422  # half a pin
    assert c.post(url, json={"lat": 144.0, "lon": -123.0}, headers=AUTH).status_code == 422  # out of range
    assert c.post(url, json={"lat": None, "lon": None}, headers=AUTH).status_code == 200
    session.refresh(w)
    assert w.lat is None
    assert c.post("/api/admin/waterbodies/99999/coords", json={"lat": 44, "lon": -123}, headers=AUTH).status_code == 404
