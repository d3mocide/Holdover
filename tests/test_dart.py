"""Willamette Falls fish passage (DART): the real captured CSV, blanks, revisions, failure, and the summary."""
from datetime import date

import pytest
from conftest import FIX
from sqlalchemy import func, select

from app.models import FishCount, RawFetch
from app.sources import dart

CSV = (FIX / "dart" / "wff_2026.csv").read_bytes()
TODAY = date(2026, 10, 19)


def table(*rows):
    head = "Project,Date,Chinook Run,Chin,Chin10Yr,JChin,JChin10Yr,Stlhd,Stlhd10Yr,WStlhd,WStlhd10Yr,Sock,Sock10Yr,Coho,Coho10Yr,JCoho,JCoho10Yr,Shad,Shad10Yr,LmpryDay,LmpryDay10Yr,BTrout,BTrout10Yr,Chum,Chum10Yr,Pink,TempC"
    return (head + "\n" + "\n".join(rows) + "\nNotes: ...\n").encode()


def test_parses_the_real_download_and_matches_the_published_numbers():
    rows = dart.parse(CSV)
    day = {r["species"]: (r["count"], r["avg10"]) for r in rows if r["observed_on"] == "2026-10-15"}
    assert day["coho"] == (123.0, 190.0) and day["chinook"] == (3.0, 9.0) and day["steelhead"] == (3.0, 3.0)
    assert {r["observed_on"] for r in rows} == {f"2026-09-{d:02d}" for d in range(1, 31)} | {f"2026-10-{d:02d}" for d in range(1, 16)}  # nothing for the days not yet reported


def test_a_blank_is_zero_on_a_reported_day_and_a_day_with_nothing_is_dropped():
    body = table("Willamette Falls,2026-10-14,Fa,,24,,6,,5,,,,,100,233,25,54,,,,,,,,,,",
                 "Willamette Falls,2026-10-16,Fa,,9,,2,,3,,,,,,190,,44,,,,,,,,,,")  # the second day has averages but no counts: not reported yet
    rows = dart.parse(body)
    assert {r["observed_on"] for r in rows} == {"2026-10-14"}
    assert {r["species"]: r["count"] for r in rows if r["observed_on"] == "2026-10-14"}["chinook"] == 0.0


def test_rejects_html_and_empty_tables():
    for bad in (b"<html>maintenance</html>", b"", table()):
        with pytest.raises(dart.ParseError):
            dart.parse(bad)


def run(session, body, status=200):
    return dart.run_job(session, lambda url: (status, body), TODAY)


def test_job_stores_raw_first_and_only_adds_what_is_new(session):
    first = run(session, CSV)
    assert first["ok"] and first["added"] == 540 and first["revised"] == 0
    assert session.scalar(select(func.count()).select_from(RawFetch).where(RawFetch.source == "dart", RawFetch.parse_ok == 1)) == 1
    assert run(session, CSV) == {"ok": True, "added": 0, "revised": 0}  # the same download again adds nothing
    assert dart.url_for(2026).endswith("avg=1") and "cum" not in dart.url_for(2026)  # checkboxes: only the ones we want are sent


def test_a_revised_count_is_a_new_row_and_the_newest_wins_so_history_is_kept(session):
    run(session, CSV)
    revised = CSV.replace(b"Willamette Falls,2026-10-15,Fa,3,9,,2,3,3,,,,,123,190", b"Willamette Falls,2026-10-15,Fa,3,9,,2,3,3,,,,,140,190")
    out = run(session, revised)
    assert out["revised"] == 1 and out["added"] == 0
    both = session.scalars(select(FishCount).where(FishCount.observed_on == "2026-10-15", FishCount.species == "coho").order_by(FishCount.id)).all()
    assert [b.count for b in both] == [123.0, 140.0]  # the old value is still there
    coho = dart.summary(session, 7)["species"]["coho"]
    assert coho["daily"][-1] == {"date": "2026-10-15", "count": 140}  # and the summary uses the newest


def test_failure_keeps_the_last_good_counts(session):
    run(session, CSV)
    n = session.scalar(select(func.count()).select_from(FishCount))
    assert run(session, b"<html>down</html>") == {"ok": False} and run(session, b"", status=503) == {"ok": False}
    assert session.scalar(select(func.count()).select_from(FishCount)) == n
    assert session.scalar(select(RawFetch).where(RawFetch.source == "dart").order_by(RawFetch.id.desc())).parse_ok == 0
    assert dart.summary(session)["through"] == "2026-10-15"


def test_summary_sums_the_latest_seven_reported_days_against_the_ten_year_average(session):
    assert dart.summary(session) is None  # never fetched
    run(session, CSV)
    s = dart.summary(session, 7)
    assert s["through"] == "2026-10-15" and s["from"] == "2026-10-09" and s["days_reported"] == 7
    coho = s["species"]["coho"]
    rows = {r["observed_on"]: r for r in dart.parse(CSV) if r["species"] == "coho"}
    week = [f"2026-10-{d:02d}" for d in range(9, 16)]
    assert coho["count"] == round(sum(rows[d]["count"] for d in week)) and coho["avg10"] == round(sum(rows[d]["avg10"] for d in week))
    assert [d["date"] for d in coho["daily"]] == week
    assert s["page"].startswith("https://www.cbr.washington.edu/dart") and s["project"] == "Willamette Falls"


def test_dart_is_fetched_with_the_system_trust_store_and_nothing_is_bundled(session, monkeypatch):
    import os
    seen = {}
    monkeypatch.setattr(dart, "http_fetch", lambda url, **kw: seen.update(kw) or (200, CSV))
    assert dart.run_job(session, today=TODAY)["ok"] and seen == {"system_trust": True}
    assert not os.path.exists(os.path.join(os.path.dirname(dart.__file__), "..", "certs", "emsign-ecc-root-ca-g3.pem"))


def test_system_trust_builds_a_verifying_context_and_never_turns_verification_off(monkeypatch):
    import ssl

    from app import http
    made = {}
    monkeypatch.setattr(http.httpx, "get", lambda url, **kw: made.update(kw) or type("R", (), {"status_code": 200, "content": b"x"})())
    http.http_fetch("https://example.test/", system_trust=True)
    ctx = made["verify"]
    assert isinstance(ctx, ssl.SSLContext) and ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname
