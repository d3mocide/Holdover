from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.models import RawFetch, StockingSnapshot, Waterbody, WaterbodyAlias
from app.seed import seed_waterbodies
from app.sources.odfw_stocking import ingest_page

URL = "https://example.test/stocking?page=0"
AUTH = {}


def client():
    from app.main import app
    return TestClient(app)


def test_ingest_stores_raw_then_snapshots(session, stocking_html):
    seed_waterbodies(session)
    assert ingest_page(session, URL, 200, stocking_html) == (50, 50)
    raw = session.scalar(select(RawFetch))
    assert raw.body == stocking_html and raw.parse_ok == 1
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == 50


def test_identical_body_skips_parse(session, stocking_html):
    seed_waterbodies(session)
    ingest_page(session, URL, 200, stocking_html)
    assert ingest_page(session, URL, 200, stocking_html) == (-1, 0)
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == 50
    assert session.scalar(select(func.count()).select_from(RawFetch)) == 2


def test_parse_failure_keeps_last_good_and_marks_stale(session, stocking_html):
    from app.scheduler import source_status
    seed_waterbodies(session)
    ingest_page(session, URL, 200, stocking_html)
    ingest_page(session, URL, 200, b"<html>new layout</html>")
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) == 50
    st = source_status()["odfw_stocking"]
    assert st["stale"] and "table not found" in st["last_error"]


def test_http_error_recorded(session):
    assert ingest_page(session, URL, 403, b"forbidden") == (0, 0)
    assert session.scalar(select(RawFetch.parse_ok)) == 0


def test_unknown_label_goes_to_review_not_map(session, stocking_html):
    seed_waterbodies(session)
    html = stocking_html.replace(b"ESTACADA LK", b"ESTACADO LK")
    ingest_page(session, URL, 200, html)
    alias = session.scalar(select(WaterbodyAlias).where(WaterbodyAlias.alias_text == "ESTACADO LAKE"))
    assert alias.confirmed == 0 and alias.proposed_confidence and alias.proposed_confidence >= 0.6
    from conftest import signed_in_client
    c = signed_in_client("boss", admin=True)
    assert "Estacada Lake" not in {f["properties"]["name"] for f in c.get("/api/map").json()["features"]}
    queue = c.get("/api/admin/aliases", headers=AUTH).json()
    assert [q["alias_text"] for q in queue] == ["ESTACADO LAKE"]
    assert queue[0]["proposed_waterbody"]["name"] == "Estacada Lake"
    # only after human confirmation does it appear on the map
    assert c.post(f"/api/admin/aliases/{alias.id}/confirm", headers=AUTH).status_code == 200
    names = {f["properties"]["name"] for f in c.get("/api/map").json()["features"]}
    assert "Estacada Lake" in names


def test_snapshots_are_append_only_latest_wins(session, stocking_html):
    seed_waterbodies(session)
    ingest_page(session, URL, 200, stocking_html)
    ingest_page(session, URL, 200, stocking_html.replace(b"1,334", b"1,500"))
    assert session.scalar(select(func.count()).select_from(StockingSnapshot)) > 50  # nothing overwritten
    wb_id = session.scalar(select(Waterbody.id).where(Waterbody.name == "Estacada Lake"))
    body = client().get(f"/api/waterbodies/{wb_id}").json()
    assert body["stocking"][-1]["total"] == 1500
    assert body["snapshots"] == 2 * len(body["stocking"])


def test_admin_requires_an_admin_account(session):
    from conftest import anonymous_client, signed_in_client
    assert anonymous_client().get("/api/admin/aliases").status_code == 401
    assert signed_in_client("plain").get("/api/admin/aliases").status_code == 403  # signed in, not admin
    assert signed_in_client("boss", admin=True).get("/api/admin/aliases").status_code == 200


def test_unlocated_waterbodies_are_listed_not_pinned(session, stocking_html):
    seed_waterbodies(session)
    ingest_page(session, URL, 200, stocking_html)
    meta = client().get("/api/map").json()
    pinned = {f["properties"]["name"] for f in meta["features"]}
    assert not pinned & {p["name"] for p in meta["meta"]["needs_coords"]}


def test_healthz(session):
    r = client().get("/healthz").json()
    assert r["sources"]["odfw_stocking"]["stale"] is True  # never fetched
