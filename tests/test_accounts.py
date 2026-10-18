"""Accounts, sessions, invites, per-user data and the isolation guarantees between users."""
import json
from datetime import datetime, timedelta, timezone

from conftest import PASSWORD, anonymous_client, signed_in_client
from sqlalchemy import select

from app.models import Catch, Favorite, Invite, Pin, Trip, User, UserSession, Waterbody
from app.security import hash_password, hash_token
from app.seed import seed_waterbodies

T1 = "11111111-1111-4111-8111-111111111111"
C1 = "22222222-2222-4222-8222-222222222222"


def trip(**kw):
    return {"uuid": T1, "started_at": "2026-10-17T07:00:00-07:00", "waterbody_id": None, "lat": 44.05, "lon": -123.06,
            "notes": "mine", "updated_at": "2026-10-17T14:00:00.000Z", "deleted": 0, **kw}


def catch(**kw):
    return {"uuid": C1, "trip_uuid": T1, "species": "rainbow trout", "count": 2, "updated_at": "2026-10-17T14:00:00.000Z", **kw}


# ---- sign in / out -----------------------------------------------------------------------------------------

def test_signed_out_is_a_normal_state_and_public_reads_stay_open(session):
    c = anonymous_client()
    assert c.get("/api/auth/me").json()["user"] is None
    assert c.get("/api/map").status_code == 200
    assert c.get("/api/spots").status_code == 200
    assert c.get("/healthz").status_code == 200


def test_login_me_logout(session):
    c = signed_in_client("will")
    me = c.get("/api/auth/me").json()["user"]
    assert me["username"] == "will" and me["is_admin"] is False and me["favorites"] == [] and me["home"] is None
    assert c.post("/api/auth/logout").status_code == 200
    assert c.get("/api/auth/me").json()["user"] is None
    assert c.get("/api/sync/pull").status_code == 401


def test_session_cookie_is_httponly_samesite_and_only_a_hash_is_stored(session):
    signed_in_client("will")
    c = anonymous_client()
    r = c.post("/api/auth/login", json={"username": "WILL", "password": PASSWORD})  # case-insensitive
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" not in cookie  # plain http in tests
    token = r.cookies["holdover_session"]
    assert session.get(UserSession, hash_token(token)) is not None
    assert not session.scalars(select(UserSession).where(UserSession.token_hash == token)).first()


def test_secure_flag_follows_https_through_a_proxy(session):
    signed_in_client("will")
    r = anonymous_client().post("/api/auth/login", json={"username": "will", "password": PASSWORD},
                                headers={"X-Forwarded-Proto": "https"})
    assert "secure" in r.headers["set-cookie"].lower()


def test_wrong_password_and_unknown_user_look_identical_and_get_throttled(session):
    signed_in_client("will")
    c = anonymous_client()
    a = c.post("/api/auth/login", json={"username": "will", "password": "nope-nope-nope"})
    b = c.post("/api/auth/login", json={"username": "ghost", "password": "nope-nope-nope"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()
    for _ in range(4):
        c.post("/api/auth/login", json={"username": "will", "password": "still-wrong-1"})
    locked = c.post("/api/auth/login", json={"username": "will", "password": PASSWORD})  # even the right one waits
    assert locked.status_code == 429 and "Retry-After" in locked.headers


def test_state_changing_calls_need_the_csrf_header(session):
    c = signed_in_client("will")
    del c.headers["X-Holdover"]
    assert c.put("/api/me/home", json={"lat": 44.0, "lon": -123.0}).status_code == 403
    assert c.get("/api/auth/me").status_code == 200  # reads are fine
    c.headers["X-Holdover"] = "1"
    assert c.put("/api/me/home", json={"lat": 44.0, "lon": -123.0}).status_code == 200


def test_expired_and_disabled_sessions_stop_working(session):
    c = signed_in_client("will")
    row = session.scalars(select(UserSession)).one()
    row.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
    session.commit()
    assert c.get("/api/auth/me").json()["user"] is None
    c2 = signed_in_client("amy")
    session.scalar(select(User).where(User.username == "amy")).disabled = 1
    session.commit()
    assert c2.get("/api/auth/me").json()["user"] is None


def test_change_password_signs_out_other_devices(session):
    a = signed_in_client("will")
    b = anonymous_client()
    b.post("/api/auth/login", json={"username": "will", "password": PASSWORD})
    assert b.get("/api/auth/me").json()["user"]
    assert a.post("/api/auth/password", json={"current": "wrong-wrong-wrong", "new": "brand-new-password"}).status_code == 403
    assert a.post("/api/auth/password", json={"current": PASSWORD, "new": "short"}).status_code == 422
    assert a.post("/api/auth/password", json={"current": PASSWORD, "new": "brand-new-password"}).status_code == 200
    assert a.get("/api/auth/me").json()["user"]  # this device stays signed in
    assert b.get("/api/auth/me").json()["user"] is None  # the other one does not
    assert anonymous_client().post("/api/auth/login", json={"username": "will", "password": "brand-new-password"}).status_code == 200


# ---- invites -----------------------------------------------------------------------------------------------

def test_invite_flow_is_single_use_and_registration_without_one_is_refused(session):
    boss = signed_in_client("boss", admin=True)
    code = boss.post("/api/admin/invites").json()["code"]
    stored = session.scalars(select(Invite)).one()
    assert stored.code_hash != code and stored.code_hash == hash_token(code)  # only the hash is kept
    c = anonymous_client()
    assert c.get(f"/api/auth/invite/{code}").json() == {"valid": True}
    assert c.post("/api/auth/register", json={"invite": "made-up", "username": "eve", "password": PASSWORD}).status_code == 400
    r = c.post("/api/auth/register", json={"invite": code, "username": "Sam", "password": PASSWORD})
    assert r.status_code == 200 and r.json()["user"]["username"] == "sam" and r.json()["user"]["is_admin"] is False
    assert c.get("/api/auth/me").json()["user"]["username"] == "sam"  # registering signs you in
    assert anonymous_client().get(f"/api/auth/invite/{code}").json() == {"valid": False}  # used
    assert anonymous_client().post("/api/auth/register", json={"invite": code, "username": "x1y2z3", "password": PASSWORD}).status_code == 400


def test_invite_expiry_username_rules_and_duplicates(session):
    boss = signed_in_client("boss", admin=True)
    code = boss.post("/api/admin/invites").json()["code"]
    c = anonymous_client()
    assert c.post("/api/auth/register", json={"invite": code, "username": "a", "password": PASSWORD}).status_code == 422
    assert c.post("/api/auth/register", json={"invite": code, "username": "ok-name", "password": "short"}).status_code == 422
    assert c.post("/api/auth/register", json={"invite": code, "username": "boss", "password": PASSWORD}).status_code == 409
    inv = session.scalars(select(Invite)).one()
    inv.expires_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    session.commit()
    assert c.post("/api/auth/register", json={"invite": code, "username": "late-one", "password": PASSWORD}).status_code == 400


def test_only_admins_manage_users_and_invites(session):
    plain = signed_in_client("plain")
    for method, url in (("get", "/api/admin/users"), ("post", "/api/admin/invites"), ("get", "/api/admin/invites")):
        assert getattr(plain, method)(url).status_code == 403
    assert getattr(anonymous_client(), "get")("/api/admin/users").status_code == 401


def test_admin_can_disable_reset_and_cannot_lock_everyone_out(session):
    boss = signed_in_client("boss", admin=True)
    sam = signed_in_client("sam")
    sam_id = session.scalar(select(User.id).where(User.username == "sam"))
    boss_id = session.scalar(select(User.id).where(User.username == "boss"))
    assert boss.post(f"/api/admin/users/{sam_id}/disabled", json={"disabled": True}).json()["disabled"] is True
    assert sam.get("/api/auth/me").json()["user"] is None  # signed out everywhere immediately
    assert anonymous_client().post("/api/auth/login", json={"username": "sam", "password": PASSWORD}).status_code == 401
    assert boss.post(f"/api/admin/users/{boss_id}/disabled", json={"disabled": True}).status_code == 409  # not yourself
    assert boss.post(f"/api/admin/users/{boss_id}/admin", json={"is_admin": False}).status_code == 409  # last admin
    assert boss.post(f"/api/admin/users/{sam_id}/disabled", json={"disabled": False}).status_code == 200
    assert boss.post(f"/api/admin/users/{sam_id}/password", json={"password": "reset-by-the-admin"}).status_code == 200
    assert anonymous_client().post("/api/auth/login", json={"username": "sam", "password": "reset-by-the-admin"}).status_code == 200
    rows = {u["username"]: u for u in boss.get("/api/admin/users").json()}
    assert rows["sam"]["trips"] == 0 and "password_hash" not in rows["sam"]


# ---- per-user home and favorites --------------------------------------------------------------------------

def test_home_and_favorites_are_per_user(session):
    seed_waterbodies(session)
    wb = session.scalar(select(Waterbody.id).where(Waterbody.name == "Dexter Reservoir"))
    a, b = signed_in_client("amy"), signed_in_client("ben")
    assert a.put("/api/me/home", json={"lat": 44.05, "lon": -123.09}).json()["home"] == {"lat": 44.05, "lon": -123.09}
    assert a.put(f"/api/me/favorites/{wb}").json()["favorites"] == [wb]
    assert b.get("/api/auth/me").json()["user"]["home"] is None and b.get("/api/auth/me").json()["user"]["favorites"] == []
    assert a.put("/api/me/home", json={"lat": 44.05}).status_code == 422  # half a coordinate
    assert a.put("/api/me/home", json={"lat": 10.0, "lon": -123.0}).status_code == 422  # not in Oregon
    assert a.put("/api/me/favorites/999999").status_code == 404
    assert a.delete(f"/api/me/favorites/{wb}").json()["favorites"] == []


def test_sign_in_merges_local_favorites_and_home_without_overriding_the_account(session):
    seed_waterbodies(session)
    ids = list(session.scalars(select(Waterbody.id).order_by(Waterbody.id).limit(3)))
    c = signed_in_client("amy")
    c.put(f"/api/me/favorites/{ids[0]}")
    me = c.post("/api/me/merge", json={"favorites": [ids[1], ids[2], 999999], "home": {"lat": 44.0, "lon": -123.0}}).json()
    assert me["favorites"] == sorted(ids) and me["home"] == {"lat": 44.0, "lon": -123.0}  # unknown id dropped, home adopted
    me = c.post("/api/me/merge", json={"favorites": [], "home": {"lat": 45.0, "lon": -122.0}}).json()
    assert me["home"] == {"lat": 44.0, "lon": -123.0}  # the account's home wins


def test_planner_uses_the_signed_in_users_home_then_the_browsers_then_none(session):
    from test_planner import load

    load(session)
    anon = anonymous_client()

    def distance(c, **params):
        spots = c.get("/api/spots", params={"date": "2026-10-17", "fishery": "trout", **params}).json()["spots"]
        top = spots[0]
        return top["waterbody"]["name"], next(f for f in top["factors"] if f["name"] == "distance")

    name, none = distance(anon)
    assert none["applicable"] is False  # no home anywhere: the factor is dropped, not guessed
    lat, lon = session.scalar(select(Waterbody.lat).where(Waterbody.name == name)), session.scalar(select(Waterbody.lon).where(Waterbody.name == name))
    _, from_browser = distance(anon, home_lat=lat, home_lon=lon)  # a browser that kept its own home on the device
    assert from_browser["applicable"] is True and from_browser["detail"].startswith("0 mi")
    c = signed_in_client("amy")
    assert distance(c)[1]["applicable"] is False  # signed in but no saved home yet
    c.put("/api/me/home", json={"lat": 45.0, "lon": -122.0})
    _, saved = distance(c, home_lat=lat, home_lon=lon)  # the account's saved home beats what the browser sent
    assert saved["applicable"] is True and not saved["detail"].startswith("0 mi")
    assert anon.get("/api/spots", params={"home_lat": 999, "home_lon": 0}).status_code == 422
    top = c.get("/api/spots", params={"date": "2026-10-17"}).json()["spots"][0]
    wb = top["waterbody"]["id"]
    assert top["favorite"] is False
    c.put(f"/api/me/favorites/{wb}")
    assert c.get("/api/spots", params={"date": "2026-10-17"}).json()["spots"][0]["favorite"] is True
    assert anon.get("/api/spots", params={"date": "2026-10-17"}).json()["spots"][0]["favorite"] is False


# ---- isolation between users -------------------------------------------------------------------------------

def test_users_only_ever_see_their_own_journal(session):
    a, b = signed_in_client("amy"), signed_in_client("ben")
    assert a.post("/api/sync/push", json={"trips": [trip()], "catches": [catch()]}).json()["applied"] == 2
    assert [t["uuid"] for t in a.get("/api/sync/pull").json()["trips"]] == [T1]
    pulled = b.get("/api/sync/pull").json()
    assert (pulled["trips"], pulled["catches"], pulled["pins"]) == ([], [], [])
    assert b.get("/api/journal/export").json()["trips"] == []
    assert "owner_id" not in a.get("/api/sync/pull").json()["trips"][0]  # bookkeeping is never sent


def test_a_user_cannot_overwrite_or_attach_to_anothers_rows(session):
    a, b = signed_in_client("amy"), signed_in_client("ben")
    a.post("/api/sync/push", json={"trips": [trip()], "catches": [catch()]})
    # same uuid, newer timestamp: must be refused, not applied
    r = b.post("/api/sync/push", json={"trips": [trip(notes="hijacked", updated_at="2030-01-01T00:00:00.000Z")]}).json()
    assert r["applied"] == 0 and r["rejected"][0]["reason"] == "belongs to another account"
    # a new catch pointed at someone else's trip is refused too
    r = b.post("/api/sync/push", json={"catches": [catch(uuid="33333333-3333-4333-8333-333333333333")]}).json()
    assert r["rejected"][0]["reason"] == "trip belongs to another account"
    assert session.get(Trip, T1).notes == "mine" and session.get(Trip, T1).owner_id == session.scalar(select(User.id).where(User.username == "amy"))
    # deleting is just an update, so it is guarded the same way
    b.post("/api/sync/push", json={"trips": [trip(deleted=1, updated_at="2031-01-01T00:00:00.000Z")]})
    assert session.get(Trip, T1).deleted == 0


def test_photos_are_private_to_their_owner(session, tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app.config import get_settings
    get_settings.cache_clear()
    a, b = signed_in_client("amy"), signed_in_client("ben")
    name = a.post("/api/journal/photo", files={"file": ("a.jpg", b"\xff\xd8\xff fake", "image/jpeg")}).json()["photo_path"]
    assert name.startswith(f"{session.scalar(select(User.id).where(User.username == 'amy'))}-")
    assert a.get(f"/api/journal/photo/{name}").content.startswith(b"\xff\xd8")
    assert b.get(f"/api/journal/photo/{name}").status_code == 404
    assert anonymous_client().get(f"/api/journal/photo/{name}").status_code == 401
    a.post("/api/sync/push", json={"trips": [trip()]})
    r = b.post("/api/sync/push", json={"trips": [trip(uuid="44444444-4444-4444-8444-444444444444")],
                                       "catches": [catch(uuid="55555555-5555-4555-8555-555555555555", trip_uuid="44444444-4444-4444-8444-444444444444", photo_path=name)]}).json()
    assert r["rejected"][0]["reason"] == "photo belongs to another account"


# ---- command line, forecasts ------------------------------------------------------------------------------

def test_first_user_is_admin_and_adopts_pre_account_data(session, monkeypatch):
    from app import cli

    seed_waterbodies(session)
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Dexter Reservoir"))
    wb.starred = 1
    session.add(Trip(uuid=T1, updated_at="2026-10-17T14:00:00.000Z"))  # as an older database would hold it
    session.add(Pin(uuid="66666666-6666-4666-8666-666666666666", lat=44.0, lon=-123.0, updated_at="2026-10-17T14:00:00.000Z"))
    session.commit()
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(PASSWORD + "\n"))
    assert cli.main(["create-user", "Will", "--password-stdin"]) == 0
    will = session.scalar(select(User).where(User.username == "will"))
    assert will.is_admin == 1
    session.expire_all()
    assert session.get(Trip, T1).owner_id == will.id
    assert session.scalars(select(Favorite.waterbody_id).where(Favorite.user_id == will.id)).all() == [wb.id]
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(PASSWORD + "\n"))
    cli.main(["create-user", "amy", "--password-stdin"])
    assert session.scalar(select(User.is_admin).where(User.username == "amy")) == 0  # later users are not admin by default
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("a-new-long-password\n"))
    cli.main(["reset-password", "amy", "--password-stdin"])
    assert anonymous_client().post("/api/auth/login", json={"username": "amy", "password": "a-new-long-password"}).status_code == 200


def test_forecast_points_include_every_users_favorites(session):
    from app.sources import nws

    seed_waterbodies(session)
    ids = list(session.scalars(select(Waterbody.id).where(Waterbody.lat.is_not(None)).order_by(Waterbody.id).limit(2)))
    a, b = signed_in_client("amy"), signed_in_client("ben")
    a.put(f"/api/me/favorites/{ids[0]}")
    b.put(f"/api/me/favorites/{ids[1]}")
    assert {ids[0], ids[1]} <= {w.id for w in nws.forecast_points(session)}


def test_login_throttle_uses_the_real_address_only_when_proxies_are_trusted(session, monkeypatch):
    from app.config import get_settings

    signed_in_client("will")

    def hammer(hops, vary):
        monkeypatch.setenv("TRUSTED_PROXY_HOPS", str(hops))
        get_settings.cache_clear()
        from app import security
        security.by_ip.hits.clear()
        c, last = anonymous_client(), None
        for i in range(32):  # 30 failures from one address lock it; unknown names, so the per-user limit never trips
            xff = f"6.6.6.6, 10.0.{i if vary else 0}.1"  # the right-most entry is the proxy's view of the caller
            last = c.post("/api/auth/login", json={"username": f"ghost{i}", "password": "nope-nope-nope"}, headers={"X-Forwarded-For": xff})
        return last.status_code

    assert hammer(0, vary=True) == 429   # header ignored: it is all one address, so a spoofed header cannot dodge the limit
    assert hammer(1, vary=False) == 429  # one trusted proxy, one real client: still limited
    assert hammer(1, vary=True) == 401   # distinct real clients behind the proxy are limited separately
    monkeypatch.delenv("TRUSTED_PROXY_HOPS")
    get_settings.cache_clear()
