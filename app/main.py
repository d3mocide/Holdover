import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import scheduler
from app.api import accounts, admin, conditions, fire, journal, planner, reports, stocking
from app.config import get_settings

def configure_logging() -> None:
    """Our own loggers (scheduler, jobs) at INFO with a timestamp, and the access log without the noise of static files."""
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("holdover").setLevel(logging.INFO)

    class Quiet(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return not any(f'"GET {p}' in record.getMessage() for p in ("/assets/", "/fonts/", "/tiles/", "/healthz", "/icon", "/manifest", "/sw.js", "/workbox"))

    logging.getLogger("uvicorn.access").addFilter(Quiet())


configure_logging()
log = logging.getLogger("holdover")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    if s.run_scheduler:
        scheduler.start()
    yield
    if scheduler.scheduler.running:
        scheduler.scheduler.shutdown(wait=False)


app = FastAPI(title="Holdover", lifespan=lifespan)
app.include_router(stocking.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(conditions.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(fire.router, prefix="/api")
app.include_router(planner.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")


_llm_cache: tuple[float, dict] = (0.0, {})


def _llm_status() -> dict:
    """Reachability is cached for 60 s so /healthz stays cheap."""
    global _llm_cache
    import time
    from app.llm.client import LLMClient
    if time.monotonic() - _llm_cache[0] > 60:
        c = LLMClient()
        _llm_cache = (time.monotonic(), {"configured": c.configured, "reachable": c.reachable()})
    return _llm_cache[1]


@app.get("/healthz")
def healthz():
    sources = scheduler.source_status()
    s = get_settings()
    return {
        "ok": True,
        "scheduler_running": scheduler.scheduler.running,
        "sources": sources,
        "stale": [k for k, v in sources.items() if v["stale"]],
        "llm": _llm_status(),
    }


# StaticFiles answers HTTP Range requests, which PMTiles needs.
tiles_dir = os.path.join(get_settings().data_dir, "tiles")
if os.path.isdir(tiles_dir):
    app.mount("/tiles", StaticFiles(directory=tiles_dir), name="tiles")

web = Path(get_settings().web_dir).resolve()
if (web / "index.html").exists():

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def spa(path: str):
        f = (web / path).resolve()
        if path and f.is_file() and web in f.parents:
            return FileResponse(f)
        # Asset-like prefixes must 404, not fall through to the SPA shell (a missing glyph range is not HTML).
        if path.startswith(("api/", "tiles/", "fonts/")):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(web / "index.html")
