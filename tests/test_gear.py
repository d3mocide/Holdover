"""Gear items and setups: validation, sync, export, and that nobody can touch or reference anyone else's gear."""
import json

from conftest import anonymous_client, signed_in_client
from sqlalchemy import select

from app.models import GearItem, GearSetup, Trip, User

G1 = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
G2 = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
S1 = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
T1 = "11111111-1111-4111-8111-111111111111"
C1 = "22222222-2222-4222-8222-222222222222"
TS = "2026-10-17T14:00:00.000Z"


def item(**kw):
    return {"uuid": G1, "kind": "lure", "name": "Panther Martin", "size": "1/8 oz", "color": "gold", "quantity": 3,
            "fisheries_json": json.dumps(["trout"]), "updated_at": TS, **kw}


def setup(**kw):
    return {"uuid": S1, "name": "Light spinning", "item_uuids_json": json.dumps([G1]), "updated_at": TS, **kw}


def trip(**kw):
    return {"uuid": T1, "started_at": "2026-10-17T07:00:00-07:00", "lat": 44.05, "lon": -123.06, "updated_at": TS, **kw}


def catch(**kw):
    return {"uuid": C1, "trip_uuid": T1, "species": "rainbow trout", "count": 2, "updated_at": TS, **kw}


def test_gear_round_trips_through_sync(session):
    c = signed_in_client("amy")
    r = c.post("/api/sync/push", json={"gear": [item(), item(uuid=G2, kind="rod", name="6wt fly rod", size="9 ft")],
                                       "setups": [setup()],
                                       "trips": [trip(setup_uuid=S1, gear_json=json.dumps([G1]))],
                                       "catches": [catch(gear_uuid=G1)]}).json()
    assert r["applied"] == 5 and r["rejected"] == []
    pulled = c.get("/api/sync/pull").json()
    assert {g["uuid"] for g in pulled["gear"]} == {G1, G2}
    assert pulled["setups"][0]["name"] == "Light spinning" and "owner_id" not in pulled["gear"][0]
    assert pulled["trips"][0]["setup_uuid"] == S1 and pulled["catches"][0]["gear_uuid"] == G1
    again = c.post("/api/sync/push", json={"gear": [item()]}).json()  # a repeat push is a no-op
    assert again["applied"] == 0 and again["stale"] == 1


def test_validation_rejects_bad_gear(session):
    c = signed_in_client("amy")
    bad = [item(kind="spaceship"), item(status="stolen"), item(name=""), item(quantity=-1), item(quantity=100000),
           item(fisheries_json='["sharks"]'), item(fisheries_json="not json"), item(uuid="bad uuid!"),
           item(name="x" * 500)]
    for b in bad:
        assert c.post("/api/sync/push", json={"gear": [b]}).status_code == 422, b
    assert c.post("/api/sync/push", json={"setups": [setup(item_uuids_json='["not-a-uuid!"]')]}).status_code == 422
    assert c.post("/api/sync/push", json={"trips": [trip(gear_json='{"a": 1}')]}).status_code == 422
    assert c.post("/api/sync/push", json={"catches": [catch(gear_uuid="nope!")]}).status_code == 422
    assert anonymous_client().post("/api/sync/push", json={"gear": [item()]}).status_code == 401


def test_gear_is_private_and_cannot_be_overwritten(session):
    a, b = signed_in_client("amy"), signed_in_client("ben")
    a.post("/api/sync/push", json={"gear": [item()], "setups": [setup()]})
    pulled = b.get("/api/sync/pull").json()
    assert pulled["gear"] == [] and pulled["setups"] == []
    r = b.post("/api/sync/push", json={"gear": [item(name="hijacked", updated_at="2031-01-01T00:00:00.000Z")],
                                       "setups": [setup(name="hijacked", updated_at="2031-01-01T00:00:00.000Z")]}).json()
    assert r["applied"] == 0 and len(r["rejected"]) == 2  # refused, whether for the uuid or for the gear it names
    assert {x["reason"] for x in r["rejected"]} <= {"belongs to another account", "gear belongs to another account"}
    assert session.get(GearItem, G1).name == "Panther Martin" and session.get(GearSetup, S1).name == "Light spinning"
    # deleting is an update, so it is guarded the same way
    b.post("/api/sync/push", json={"gear": [item(deleted=1, updated_at="2032-01-01T00:00:00.000Z")]})
    assert session.get(GearItem, G1).deleted == 0


def test_nobody_can_reference_someone_elses_gear(session):
    a, b = signed_in_client("amy"), signed_in_client("ben")
    a.post("/api/sync/push", json={"gear": [item()], "setups": [setup()]})
    mine = {"uuid": G2, "kind": "rod", "name": "Ben's rod", "updated_at": TS}
    # a trip pointing at amy's setup or item
    for t in (trip(setup_uuid=S1), trip(gear_json=json.dumps([G1]))):
        r = b.post("/api/sync/push", json={"trips": [t]}).json()
        assert r["rejected"][0]["reason"] == "gear belongs to another account" and session.get(Trip, T1) is None
    # a catch pointing at amy's lure (on ben's own trip)
    r = b.post("/api/sync/push", json={"trips": [trip()], "catches": [catch(gear_uuid=G1)]}).json()
    assert r["rejected"][0]["reason"] == "gear belongs to another account"
    # a setup that contains amy's item
    r = b.post("/api/sync/push", json={"gear": [mine], "setups": [setup(uuid="dddddddd-dddd-4ddd-8ddd-dddddddddddd")]}).json()
    assert r["rejected"][0]["reason"] == "gear belongs to another account"
    # but a reference to gear that does not exist yet is fine: it is only a pointer inside the owner's own data
    ok = b.post("/api/sync/push", json={"trips": [trip(uuid="55555555-5555-4555-8555-555555555555", gear_json=json.dumps(["eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"]))]}).json()
    assert ok["applied"] == 1


def test_gear_photos_are_owner_prefixed(session):
    a, b = signed_in_client("amy"), signed_in_client("ben")
    amy_id = session.scalar(select(User.id).where(User.username == "amy"))
    assert a.post("/api/sync/push", json={"gear": [item(photo_path=f"{amy_id}-" + "a" * 32 + ".jpg")]}).json()["applied"] == 1
    r = b.post("/api/sync/push", json={"gear": [item(uuid=G2, photo_path=f"{amy_id}-" + "a" * 32 + ".jpg")]}).json()
    assert r["rejected"][0]["reason"] == "photo belongs to another account"


def test_export_includes_gear_and_names_it_in_the_csv(session):
    c = signed_in_client("amy")
    c.post("/api/sync/push", json={"gear": [item()], "setups": [setup()], "trips": [trip(setup_uuid=S1)], "catches": [catch(gear_uuid=G1)]})
    j = c.get("/api/journal/export").json()
    assert [g["name"] for g in j["gear"]] == ["Panther Martin"] and j["setups"][0]["name"] == "Light spinning"
    rows = c.get("/api/journal/export?format=csv").text.strip().splitlines()
    assert rows[0].endswith("setup,caught_on") and rows[1].endswith("Light spinning,Panther Martin")
