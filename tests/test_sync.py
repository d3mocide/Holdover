import json

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import Catch, Trip

AUTH = {}  # auth is the signed-in session now; kept so the call sites stay readable
T1 = "11111111-1111-4111-8111-111111111111"
C1 = "22222222-2222-4222-8222-222222222222"


def client():
    from conftest import signed_in_client
    return signed_in_client()


def trip(**kw):
    d = {"uuid": T1, "started_at": "2026-10-17T07:00:00-07:00", "waterbody_id": None, "lat": 44.05, "lon": -123.06,
         "notes": "first", "conditions_source": "cached", "conditions_json": json.dumps({"x": 1}),
         "updated_at": "2026-10-17T14:00:00.000Z", "deleted": 0}
    return {**d, **kw}


def catch(**kw):
    d = {"uuid": C1, "trip_uuid": T1, "species": "rainbow trout", "count": 2, "method": "spinner",
         "updated_at": "2026-10-17T14:00:00.000Z"}
    return {**d, **kw}


def test_requires_sign_in(session):
    from conftest import anonymous_client
    c = anonymous_client()
    assert c.post("/api/sync/push", json={}).status_code == 401
    assert c.get("/api/sync/pull").status_code == 401
    assert c.get("/api/journal/export").status_code == 401


def test_duplicate_push_creates_no_duplicates(session):
    c = client()
    body = {"trips": [trip()], "catches": [catch()]}
    r1 = c.post("/api/sync/push", json=body, headers=AUTH).json()
    r2 = c.post("/api/sync/push", json=body, headers=AUTH).json()
    assert (r1["applied"], r1["stale"]) == (2, 0) and (r2["applied"], r2["stale"]) == (0, 2)
    assert session.scalar(select(func.count()).select_from(Trip)) == 1
    assert session.scalar(select(func.count()).select_from(Catch)) == 1


def test_last_write_wins(session):
    c = client()
    c.post("/api/sync/push", json={"trips": [trip(notes="new", updated_at="2026-10-17T15:00:00.000Z")]}, headers=AUTH)
    old = c.post("/api/sync/push", json={"trips": [trip(notes="old", updated_at="2026-10-17T14:00:00.000Z")]}, headers=AUTH).json()
    assert old["stale"] == 1
    session.expire_all()
    assert session.get(Trip, T1).notes == "new"
    c.post("/api/sync/push", json={"trips": [trip(notes="newest", updated_at="2026-10-17T16:00:00.000Z")]}, headers=AUTH)
    session.expire_all()
    assert session.get(Trip, T1).notes == "newest"


def test_soft_delete_syncs_and_is_pulled(session):
    c = client()
    c.post("/api/sync/push", json={"trips": [trip()]}, headers=AUTH)
    c.post("/api/sync/push", json={"trips": [trip(deleted=1, updated_at="2026-10-17T15:00:00.000Z")]}, headers=AUTH)
    pulled = c.get("/api/sync/pull", params={"since": "2026-10-17T14:30:00.000Z"}, headers=AUTH).json()
    assert [t["deleted"] for t in pulled["trips"]] == [1]
    # Old clients may still send a time cursor. They must receive late-arriving changes too.
    assert c.get("/api/sync/pull", params={"since": "2026-10-17T16:00:00.000Z"}, headers=AUTH).json()["trips"][0]["deleted"] == 1


def test_late_offline_writes_are_pulled_in_every_personal_table(session):
    from conftest import signed_in_client
    c = client()
    other = signed_in_client("other-angler")
    cursor = c.get("/api/sync/pull").json()["server_time"]
    stamp = "2020-01-01T00:00:00Z"  # created offline well before the other device's last pull
    gear_id, setup_id, pin_id = "a" * 32, "b" * 32, "c" * 32
    body = {"trips": [trip(updated_at=stamp)], "catches": [catch(updated_at=stamp)],
            "gear": [{"uuid": gear_id, "kind": "lure", "name": "Offline lure", "updated_at": stamp}],
            "setups": [{"uuid": setup_id, "name": "Offline setup", "item_uuids_json": json.dumps([gear_id]), "updated_at": stamp}],
            "pins": [{"uuid": pin_id, "lat": 44, "lon": -123, "updated_at": stamp}]}
    assert c.post("/api/sync/push", json=body).json()["applied"] == 5
    for key in body:
        assert len(c.get("/api/sync/pull", params={"since": cursor}).json()[key]) == 1
        assert other.get("/api/sync/pull", params={"since": cursor}).json()[key] == []
    # Delayed edits and tombstones must propagate as well as creates.
    for key in body:
        body[key][0].update(updated_at="2020-01-02T00:00:00Z", deleted=1)
    assert c.post("/api/sync/push", json=body).json()["applied"] == 5
    pulled = c.get("/api/sync/pull", params={"since": cursor}).json()
    assert all(pulled[key][0]["deleted"] == 1 for key in body)
    assert c.get("/api/sync/pull?since=not-a-date").status_code == 422


def test_catch_without_trip_is_rejected_not_fatal(session):
    r = client().post("/api/sync/push", json={"catches": [catch()], "pins": [
        {"uuid": "33333333-3333-4333-8333-333333333333", "lat": 44, "lon": -123, "updated_at": "2026-10-17T14:00:00Z"}]},
        headers=AUTH).json()
    assert r["rejected"][0]["reason"] == "unknown trip_uuid" and r["applied"] == 1


def test_trip_and_catch_in_same_push_regardless_of_order(session):
    r = client().post("/api/sync/push", json={"catches": [catch()], "trips": [trip()]}, headers=AUTH).json()
    assert r["applied"] == 2 and r["rejected"] == []


def test_validation(session):
    c = client()
    assert c.post("/api/sync/push", json={"trips": [trip(uuid="bad uuid!")]}, headers=AUTH).status_code == 422
    assert c.post("/api/sync/push", json={"trips": [trip(updated_at="yesterday")]}, headers=AUTH).status_code == 422
    assert c.post("/api/sync/push", json={"trips": [trip(lat=999)]}, headers=AUTH).status_code == 422


def test_export_json_and_csv(session):
    c = client()
    c.post("/api/sync/push", json={"trips": [trip()], "catches": [catch()]}, headers=AUTH)
    assert len(c.get("/api/journal/export", headers=AUTH).json()["trips"]) == 1
    csv_text = c.get("/api/journal/export?format=csv", headers=AUTH).text
    assert "rainbow trout" in csv_text and csv_text.splitlines()[0].startswith("trip_uuid")


def test_photo_upload(session, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.config import get_settings
    get_settings.cache_clear()
    c = client()
    r = c.post("/api/journal/photo", files={"file": ("a.jpg", b"\xff\xd8\xff fake", "image/jpeg")}, headers=AUTH)
    name = r.json()["photo_path"]
    assert c.get(f"/api/journal/photo/{name}", headers=AUTH).content.startswith(b"\xff\xd8")
    assert c.post("/api/journal/photo", files={"file": ("a.txt", b"x", "text/plain")}, headers=AUTH).status_code == 415
    assert c.get("/api/journal/photo/../../etc/passwd", headers=AUTH).status_code in (404, 422)
