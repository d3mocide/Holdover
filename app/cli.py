"""python -m app.cli <command>: migrate | seed | ingest-fixtures DIR | stocking | ingest-report FILE | llm | reports | usgs [--backfill] | nws | oha | explain
  accounts: create-user NAME [--admin] [--password-stdin] | reset-password NAME [--password-stdin] | list-users"""
import glob
import sys

from alembic import command
from alembic.config import Config

from app.db import session_factory


def migrate() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def _password(args: list[str]) -> str:
    import getpass
    if "--password-stdin" in args:
        return sys.stdin.readline().rstrip("\n")
    a, b = getpass.getpass("Password: "), getpass.getpass("Repeat: ")
    if a != b:
        raise SystemExit("passwords differ")
    return a


def _accounts(cmd: str, args: list[str]) -> int:
    from datetime import datetime, timezone

    from sqlalchemy import func, select, update

    from app.models import Catch, Favorite, Pin, Trip, User, Waterbody
    from app.security import hash_password, validate_password, validate_username

    with session_factory()() as s:
        if cmd == "list-users":
            for u in s.scalars(select(User).order_by(User.id)):
                print(u.id, u.username, "admin" if u.is_admin else "", "disabled" if u.disabled else "")
            return 0
        names = [a for a in args if not a.startswith("--")]
        if not names:
            print(__doc__)
            return 2
        try:
            name = validate_username(names[0])
        except ValueError as e:
            raise SystemExit(str(e))
        user = s.scalar(select(User).where(User.username == name))
        if cmd == "reset-password":
            if user is None:
                raise SystemExit(f"no such user: {name}")
            try:
                user.password_hash = hash_password(validate_password(_password(args)))
            except ValueError as e:
                raise SystemExit(str(e))
            s.commit()
            print("password reset for", name)
            return 0
        if user is not None:
            raise SystemExit(f"{name} already exists (use reset-password)")
        first = s.scalar(select(func.count()).select_from(User)) == 0
        try:
            pw = validate_password(_password(args))
        except ValueError as e:
            raise SystemExit(str(e))
        user = User(username=name, password_hash=hash_password(pw), is_admin=int("--admin" in args or first),
                    created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        s.add(user)
        s.flush()
        print(f"created {name}" + (" (admin)" if user.is_admin else ""))
        if first:
            # Everything that existed before accounts belongs to the first person on the server.
            for m in (Trip, Catch, Pin):
                n = s.execute(update(m).where(m.owner_id.is_(None)).values(owner_id=user.id)).rowcount
                if n:
                    print(f"  adopted {n} existing {m.__tablename__} rows")
            starred = list(s.scalars(select(Waterbody.id).where(Waterbody.starred == 1)))
            for wb_id in starred:
                s.add(Favorite(user_id=user.id, waterbody_id=wb_id))
            if starred:
                print(f"  carried over {len(starred)} starred waterbodies as favorites")
        s.commit()
    return 0


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
    elif cmd in ("create-user", "reset-password", "list-users"):
        return _accounts(cmd, argv[1:])
    elif cmd == "stocking":
        from app.scheduler import run_stocking
        print(run_stocking())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
