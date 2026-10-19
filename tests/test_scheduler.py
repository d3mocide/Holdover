"""Startup catch-up and job logging."""
import logging

from app import scheduler
from app.http import store_fetch


def fake_runs(monkeypatch):
    ran = []
    for _, fn in scheduler.CATCH_UP:
        monkeypatch.setattr(scheduler, fn, lambda fn=fn: ran.append(fn) or {"ok": True})
    return ran


def test_catch_up_runs_every_source_on_a_fresh_install_in_order(session, monkeypatch):
    ran = fake_runs(monkeypatch)
    out = scheduler.catch_up()
    assert out[0] == "odfw_stocking" and out.index("nws") > out.index("odfw_stocking")  # forecasts need stocked waterbodies first
    assert ran == [fn for _, fn in scheduler.CATCH_UP]


def test_catch_up_skips_sources_that_are_fresh(session, monkeypatch):
    ran = fake_runs(monkeypatch)
    raw, _ = store_fetch(session, "usgs", "http://x", 200, b"{}")
    raw.parse_ok = 1
    session.commit()
    assert "usgs" not in scheduler.catch_up() and "run_usgs" not in ran


def test_a_job_run_is_logged_with_its_result(caplog):
    with caplog.at_level(logging.INFO, logger="holdover.scheduler"):
        scheduler._logged("usgs", {"ok": True, "added": 5})
        scheduler._logged("corps", {"ok": False})
    msgs = [(r.levelname, r.getMessage()) for r in caplog.records]
    assert ("INFO", "job usgs ok {'added': 5}") in msgs and ("WARNING", "job corps FAILED {}") in msgs


def test_start_schedules_the_catch_up(monkeypatch):
    monkeypatch.setattr(scheduler.scheduler, "start", lambda: None)
    scheduler.start()
    assert scheduler.scheduler.get_job("catch_up") is not None
    scheduler.scheduler.remove_all_jobs()


# ---- the weekly cadence -----------------------------------------------------------------------------------------------
def test_stocking_the_report_and_the_briefing_run_on_fridays_not_daily(monkeypatch):
    monkeypatch.setattr(scheduler.scheduler, "start", lambda: None)
    scheduler.scheduler.remove_all_jobs()
    scheduler.start()
    trig = {j: str(scheduler.scheduler.get_job(j).trigger) for j in ("stocking", "reports", "briefing")}
    assert "day_of_week='fri'" in trig["stocking"] and "hour='6'" in trig["stocking"]
    assert "day_of_week='fri,sat,mon'" in trig["reports"]  # Saturday and Monday are retries that skip when an issue is already stored
    assert "day_of_week='fri'" in trig["briefing"] and "hour='12'" in trig["briefing"]  # after the report has been fetched and read
    assert scheduler.scheduler.get_job("reports").kwargs == {"force": False}
    scheduler.scheduler.remove_all_jobs()


def test_the_report_is_fetched_only_when_the_newest_issue_is_five_or_more_days_old(session):
    from datetime import date

    from app.models import Report
    assert scheduler.report_due(session, date(2026, 10, 23)) is True  # nothing stored yet
    session.add(Report(raw_fetch_id=None, zone="willamette", issued_on="2026-10-16"))
    session.commit()
    assert scheduler.report_due(session, date(2026, 10, 18)) is False  # issued two days ago
    assert scheduler.report_due(session, date(2026, 10, 20)) is False
    assert scheduler.report_due(session, date(2026, 10, 21)) is True   # five days: the next one is due


def test_a_scheduled_report_run_skips_the_fetch_when_a_recent_issue_is_stored_but_a_forced_one_does_not(session, monkeypatch):
    from datetime import date, timedelta

    from app.models import Report
    session.add(Report(raw_fetch_id=None, zone="willamette", issued_on=(date.today() - timedelta(days=1)).isoformat()))
    session.commit()
    fetched = []
    monkeypatch.setattr(scheduler.odfw_report, "run_job", lambda s: fetched.append(1) or {"ok": True})
    assert scheduler.run_reports(force=False)["fetch"] == {"ok": True, "skipped": "a recent issue is already stored"} and not fetched
    scheduler.run_reports(force=True)  # the admin "run now" button
    assert fetched == [1]


def test_a_zone_with_no_data_is_fetched_at_startup_but_a_fetched_one_waits_for_friday(session, monkeypatch):
    from app import zones
    from app.sources import odfw_stocking
    from app.http import store_fetch
    store_fetch(session, "odfw_stocking", f"https://x/?field_zone_value={zones.BY_KEY['willamette'].stocking_value}&field_planned=1&page=0", 200, b"x")  # central has none
    session.commit()
    missing = odfw_stocking.zones_without_data(session, zones.enabled("willamette,central,northwest"))
    assert [z.key for z in missing] == ["central", "northwest"]
    seen = []
    monkeypatch.setattr(odfw_stocking, "run_zones", lambda s, fetch=None, today=None, zones=None: seen.append([z.key for z in zones]) or {"ok": True})
    fake_runs(monkeypatch)
    monkeypatch.setattr(scheduler, "source_status", lambda: {src: {"stale": False} for src, _ in scheduler.CATCH_UP})  # every source fresh: only the missing zone is worked on
    scheduler.catch_up()
    assert seen == [["central", "northwest"]]
