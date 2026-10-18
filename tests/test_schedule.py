"""The look-ahead stocking schedule: weeks in a range, month summary, ordering, and only confirmed waterbodies."""
from datetime import date

from conftest import FIX
from fastapi.testclient import TestClient

from app.seed import seed_waterbodies
from app.sources.odfw_stocking import ingest_page

URL = "https://example.test/stocking?page=0"


def setup(session, monkeypatch, stocking_html, today=date(2026, 10, 12)):
    from app.api import schedule
    seed_waterbodies(session)
    ingest_page(session, URL, 200, stocking_html)
    monkeypatch.setattr(schedule, "_today", lambda: today)
    from app.main import app
    return TestClient(app)


def test_weeks_in_range_are_sorted_and_waterbodies_biggest_first(session, monkeypatch, stocking_html):
    c = setup(session, monkeypatch, stocking_html)
    d = c.get("/api/schedule", params={"start": "2026-09-01", "end": "2027-12-31"}).json()
    weeks = [w["week_of"] for w in d["weeks"]]
    assert weeks == sorted(weeks) and len(weeks) > 3
    for w in d["weeks"]:
        totals = [r["total"] for r in w["waterbodies"]]
        assert totals == sorted(totals, reverse=True) and w["total_fish"] == sum(totals)
        assert all(r["name"] for r in w["waterbodies"])
    assert "by week" in d["note"]


def test_range_narrows_the_weeks_and_defaults_to_four_weeks_from_this_monday(session, monkeypatch, stocking_html):
    c = setup(session, monkeypatch, stocking_html)
    narrow = c.get("/api/schedule", params={"start": "2026-10-12", "end": "2026-10-18"}).json()
    assert [w["week_of"] for w in narrow["weeks"]] in (["2026-10-12"], [])
    default = c.get("/api/schedule").json()
    assert default["start"] == "2026-10-12" and default["end"] == "2026-11-09"


def test_months_summary_looks_forward_only_and_counts_match(session, monkeypatch, stocking_html):
    c = setup(session, monkeypatch, stocking_html)
    d = c.get("/api/schedule", params={"start": "2026-01-01", "end": "2028-12-31"}).json()
    months = d["months"]
    assert months and [m["month"] for m in months] == sorted(m["month"] for m in months)
    assert all(m["month"] >= "2026-10" for m in months)  # nothing before this week's month
    total_from_weeks = sum(w["total_fish"] for w in d["weeks"] if w["week_of"] >= "2026-10-12")
    assert sum(m["fish"] for m in months) == total_from_weeks


def test_unconfirmed_waterbodies_never_appear(session, monkeypatch, stocking_html):
    html = stocking_html.replace(b"ESTACADA LK", b"ESTACADO LK")  # becomes an unconfirmed alias
    from app.api import schedule
    seed_waterbodies(session)
    ingest_page(session, URL, 200, html)
    monkeypatch.setattr(schedule, "_today", lambda: date(2026, 10, 12))
    from app.main import app
    d = TestClient(app).get("/api/schedule", params={"start": "2026-01-01", "end": "2028-12-31"}).json()
    assert "Estacada Lake" not in {r["name"] for w in d["weeks"] for r in w["waterbodies"]}
