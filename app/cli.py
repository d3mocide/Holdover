"""python -m app.cli <command>: migrate | seed | ingest-fixtures DIR | stocking | ingest-report FILE | llm | reports | usgs [--backfill] | nws | oha | explain"""
import glob
import sys

from alembic import command
from alembic.config import Config

from app.db import session_factory


def migrate() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "migrate":
        migrate()
    elif cmd == "seed":
        from app.seed import seed_waterbodies
        with session_factory()() as s:
            print("added", seed_waterbodies(s))
    elif cmd == "ingest-fixtures":
        from app.sources.odfw_stocking import SOURCE, ingest_page
        for f in sorted(glob.glob(argv[1] + "/*.html")):
            with session_factory()() as s:
                print(f, ingest_page(s, "file://" + f, 200, open(f, "rb").read()))
    elif cmd == "ingest-report":  # replay a saved report page: ingest-report FILE
        from app.sources.odfw_report import URL, ingest
        with session_factory()() as s:
            print([(r.zone, r.issued_on) for r in ingest(s, URL, 200, open(argv[1], "rb").read())])
    elif cmd == "llm":
        from app.llm.jobs import process_pending
        with session_factory()() as s:
            print(process_pending(s))
    elif cmd == "reports":
        from app.scheduler import run_reports
        print(run_reports())
    elif cmd == "usgs" and "--backfill" in argv:
        from app.sources import usgs
        with session_factory()() as s:
            print(usgs.run_job(s, period="P7D"))
    elif cmd in ("usgs", "nws", "oha", "explain"):
        from app import scheduler
        print(getattr(scheduler, f"run_{cmd}")())
    elif cmd == "stocking":
        from app.scheduler import run_stocking
        print(run_stocking())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
