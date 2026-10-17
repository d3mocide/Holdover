import logging
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func, select

from app.db import session_factory
from app.http import now_iso
from app.models import RawFetch
from app.sources import odfw_stocking

log = logging.getLogger("holdover.scheduler")
scheduler = BackgroundScheduler(timezone="America/Los_Angeles")

# source -> expected cadence, used to flag a source stale when nothing succeeded recently
CADENCE = {odfw_stocking.SOURCE: timedelta(days=1)}


def run_stocking() -> dict:
    with session_factory()() as s:
        try:
            return odfw_stocking.run_job(s)
        except Exception:  # keep the scheduler alive; the failure shows in /healthz
            log.exception("stocking job crashed")
            s.rollback()
            return {"ok": False, "error": "job crashed, see logs"}


def start() -> None:
    scheduler.add_job(run_stocking, "cron", hour=6, minute=15, id="stocking", replace_existing=True,
                      misfire_grace_time=3600, coalesce=True)
    scheduler.add_job(backup, "cron", hour=3, minute=30, id="backup", replace_existing=True)
    scheduler.start()


def backup() -> None:
    import glob
    import os
    from datetime import date

    from sqlalchemy import text

    from app.config import get_settings
    from app.db import get_engine

    if not get_settings().database_url.startswith("sqlite"):
        return
    d = os.path.join(get_settings().data_dir, "backup")
    os.makedirs(d, exist_ok=True)
    dest = os.path.join(d, f"holdover-{date.today():%Y%m%d}.db")
    if os.path.exists(dest):
        os.remove(dest)
    with get_engine().connect() as c:
        c.execute(text(f"VACUUM INTO '{dest}'"))
    for old in sorted(glob.glob(os.path.join(d, "holdover-*.db")))[:-7]:
        os.remove(old)


def source_status() -> dict:
    out = {}
    with session_factory()() as s:
        for source, cadence in CADENCE.items():
            last_ok = s.scalar(select(func.max(RawFetch.fetched_at)).where(
                RawFetch.source == source, RawFetch.status == 200, RawFetch.parse_ok == 1))
            last = s.scalar(select(RawFetch).where(RawFetch.source == source).order_by(RawFetch.id.desc()).limit(1))
            stale = last_ok is None or (last is not None and last.parse_ok == 0)
            if last_ok and not stale:
                from datetime import datetime
                age = datetime.fromisoformat(now_iso()) - datetime.fromisoformat(last_ok)
                stale = age > cadence * 2
            out[source] = {"last_success": last_ok, "stale": stale,
                           "last_error": last.error if last is not None and last.parse_ok == 0 else None}
    return out
