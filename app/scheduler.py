import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func, select

from app.config import get_settings
from app.db import session_factory
from app.http import now_iso
from app.models import RawFetch
from app.sources import corps, nifc, nwps, nws, odf_fire, odfw_report, odfw_stocking, oha, usgs

log = logging.getLogger("holdover.scheduler")
scheduler = BackgroundScheduler(timezone="America/Los_Angeles")

# source -> expected cadence, used to flag a source stale when nothing succeeded recently
CADENCE = {odfw_stocking.SOURCE: timedelta(days=1), odfw_report.SOURCE: timedelta(days=8),
           usgs.SOURCE: timedelta(hours=1), oha.SOURCE: timedelta(days=1), nws.SOURCE: timedelta(hours=2),
           corps.SOURCE: timedelta(hours=1), odf_fire.SOURCE: timedelta(hours=12), nifc.SOURCE: timedelta(hours=3), nwps.SOURCE: timedelta(hours=2)}
# Sources that only run for things the owner opts into (nws needs starred waterbodies)
OPTIONAL: set[str] = set()


def run_stocking() -> dict:
    with session_factory()() as s:
        try:
            return _logged("stocking", odfw_stocking.run_zones(s))
        except Exception:  # keep the scheduler alive; the failure shows in /healthz
            log.exception("stocking job crashed")
            s.rollback()
            return {"ok": False, "error": "job crashed, see logs"}


def run_reports() -> dict:
    from app.llm.jobs import process_pending
    with session_factory()() as s:
        try:
            fetched = odfw_report.run_job(s)
        except Exception:
            log.exception("report fetch crashed")
            s.rollback()
            fetched = {"ok": False}
        try:
            return {"fetch": _logged("reports", fetched), "llm": process_pending(s)}
        except Exception:
            log.exception("llm job crashed")
            s.rollback()
            return {"fetch": fetched, "llm": {"error": "job crashed, see logs"}}


def _logged(name: str, result: dict) -> dict:
    """One line per job run, so `docker compose logs holdover | grep job` shows what the pollers are doing."""
    ok = result.get("ok", True) if isinstance(result, dict) else True
    (log.info if ok else log.warning)("job %s %s %s", name, "ok" if ok else "FAILED", {k: v for k, v in result.items() if k != "ok"} if isinstance(result, dict) else "")
    return result


def _run(name: str, mod) -> dict:
    with session_factory()() as s:
        try:
            return _logged(name, mod.run_job(s))
        except Exception:
            log.exception("%s job crashed", name)
            s.rollback()
            return {"ok": False, "error": "job crashed, see logs"}


def run_usgs() -> dict:
    return _run("usgs", usgs)


def run_nws() -> dict:
    return _run("nws", nws)


def run_corps() -> dict:
    return _run("corps", corps)


def run_odf_fire() -> dict:
    return _run("odf_fire", odf_fire)


def run_nifc() -> dict:
    return _run("nifc", nifc)


def run_nwps() -> dict:
    return _run("nwps", nwps)


def run_briefing() -> dict:
    """Write the week's briefing paragraphs (slow model, runs in the background; the facts are available without it)."""
    from app.llm.briefing import generate
    from app.llm.client import LLMClient
    from app.zones import enabled
    with session_factory()() as s:
        try:
            llm, out = LLMClient.for_extraction(), {}
            for z in enabled(get_settings().enabled_zones):
                out[z.key] = _logged(f"briefing {z.key}", generate(s, llm, zone=z.key))
            return out
        except Exception:
            log.exception("briefing job crashed")
            s.rollback()
            return {"ok": False, "error": "job crashed, see logs"}


def run_oha() -> dict:
    return _run("oha", oha)


def run_explain(days: int = 2) -> dict:
    from datetime import date, timedelta

    from app.llm.client import LLMClient
    from app.llm.explain import generate_explanations, generate_pack_intros
    from app.planner import FISHERIES
    llm, out = LLMClient(), {}
    with session_factory()() as s:
        try:
            from app.zones import enabled
            for z in enabled(get_settings().enabled_zones):
                for off in range(days):
                    for f in FISHERIES:
                        d = date.today() + timedelta(days=off)
                        out[f"{z.key}:{f}+{off}"] = {**generate_explanations(s, llm, d, f, zone=z.key), "pack": generate_pack_intros(s, llm, d, f, zone=z.key)}
        except Exception:
            log.exception("explain job crashed")
            s.rollback()
    return out


def run_llm_retry() -> None:
    from app.llm.jobs import process_pending
    with session_factory()() as s:
        try:
            process_pending(s)
        except Exception:
            log.exception("llm retry crashed")
            s.rollback()


# Order matters: NWS forecasts are fetched for stocked waterbodies, so stocking goes first.
CATCH_UP = [(odfw_stocking.SOURCE, "run_stocking"), (oha.SOURCE, "run_oha"), (usgs.SOURCE, "run_usgs"), (corps.SOURCE, "run_corps"),
            (odf_fire.SOURCE, "run_odf_fire"), (nifc.SOURCE, "run_nifc"), (nwps.SOURCE, "run_nwps"), (nws.SOURCE, "run_nws"),
            (odfw_report.SOURCE, "run_reports")]


def catch_up() -> list[str]:
    """Run, one after another, every source that has no recent success. Scheduled jobs only fire at their next interval
    or cron time, so without this a new install (or one that was off for a day) shows no data until then."""
    try:
        from app.llm.client import LLMClient
        log.info("LLM: %s", LLMClient().status_line())
        extract = LLMClient.for_extraction()
        if extract.model != LLMClient().model:
            log.info("LLM for report extraction: %s", extract.status_line())
    except Exception:
        log.exception("LLM status check failed")
    status = source_status()
    ran = []
    for source, fn in CATCH_UP:
        if status.get(source, {}).get("stale", True):
            log.info("catch-up: %s is stale, running it now", source)
            globals()[fn]()
            ran.append(source)
    try:  # the weekly briefing: written once per week, so a new install (or a missed Thursday) gets one
        from app.briefing import monday
        from app.llm.briefing import stored
        from app.llm.client import LLMClient
        from datetime import date
        if LLMClient.for_extraction().configured and not stored(session_factory()(), monday(date.today())):  # willamette stands in for "any"
            log.info("catch-up: no briefing paragraphs for this week, writing them now")
            run_briefing()
            ran.append("briefing")
    except Exception:
        log.exception("briefing catch-up failed")
    log.info("catch-up finished, ran: %s", ran or "nothing")
    return ran


def start() -> None:
    scheduler.add_job(run_stocking, "cron", hour=6, minute=15, id="stocking", replace_existing=True,
                      misfire_grace_time=3600, coalesce=True)
    # Report is published weekly (usually Thursday); poll twice a day Wed-Fri, hash compare skips unchanged.
    scheduler.add_job(run_reports, "cron", day_of_week="wed-fri", hour="9,15", minute=5, id="reports",
                      replace_existing=True, misfire_grace_time=3600, coalesce=True)
    # Retry LLM work that was skipped because the host was down.
    scheduler.add_job(run_llm_retry, "interval", hours=2, id="llm_retry", replace_existing=True)
    scheduler.add_job(run_usgs, "interval", minutes=30, id="usgs", replace_existing=True, coalesce=True)
    scheduler.add_job(run_corps, "interval", hours=1, id="corps", replace_existing=True, coalesce=True)
    scheduler.add_job(run_odf_fire, "interval", hours=6, id="odf_fire", replace_existing=True, coalesce=True)
    scheduler.add_job(run_nifc, "interval", hours=1, id="nifc", replace_existing=True, coalesce=True)
    scheduler.add_job(run_nwps, "interval", minutes=60, id="nwps", replace_existing=True, coalesce=True)
    scheduler.add_job(run_nws, "interval", hours=1, id="nws", replace_existing=True, coalesce=True)
    scheduler.add_job(run_explain, "cron", hour="6,12,17", minute=40, id="explain", replace_existing=True, coalesce=True)
    scheduler.add_job(run_briefing, "cron", day_of_week="thu", hour=16, minute=30, id="briefing", replace_existing=True, misfire_grace_time=6 * 3600, coalesce=True)
    scheduler.add_job(run_oha, "cron", hour=5, minute=45, id="oha", replace_existing=True, coalesce=True)
    scheduler.add_job(backup, "cron", hour=3, minute=30, id="backup", replace_existing=True)
    scheduler.add_job(catch_up, "date", run_date=datetime.now(scheduler.timezone) + timedelta(seconds=5), id="catch_up", replace_existing=True)
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
            if last is None and source in OPTIONAL:
                out[source] = {"last_success": None, "stale": False, "last_error": None, "idle": True}
                continue
            stale = last_ok is None or (last is not None and last.parse_ok == 0)
            if last_ok and not stale:
                from datetime import datetime
                age = datetime.fromisoformat(now_iso()) - datetime.fromisoformat(last_ok)
                stale = age > cadence * 2
            out[source] = {"last_success": last_ok, "stale": stale,
                           "last_error": last.error if last is not None and last.parse_ok == 0 else None}
    return out
