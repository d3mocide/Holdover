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
