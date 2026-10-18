"""The nightly backup is only worth having if the file it writes is a complete, valid database, and old ones rotate."""
import os
import sqlite3
from datetime import date

import pytest

from sqlalchemy import select

from app.config import get_settings
from app.models import User, Waterbody
from app.scheduler import backup
from app.seed import seed_waterbodies


def _use_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    get_settings.cache_clear()
    return tmp_path / "data" / "backup"


sqlite_only = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL", "sqlite").startswith("sqlite"), reason="the nightly backup copies a SQLite file; use pg_dump on Postgres")


@sqlite_only
def test_backup_is_a_complete_valid_copy(session, tmp_path, monkeypatch):
    out = _use_data_dir(tmp_path, monkeypatch)
    seed_waterbodies(session)
    session.add(User(username="will", password_hash="x", created_at="2026-10-18T00:00:00+00:00"))
    session.commit()
    backup()
    files = list(out.glob("holdover-*.db"))
    assert [f.name for f in files] == [f"holdover-{date.today():%Y%m%d}.db"]
    c = sqlite3.connect(files[0])
    assert c.execute("pragma integrity_check").fetchone()[0] == "ok"
    assert c.execute("select count(*) from waterbody").fetchone()[0] == len(list(session.scalars(select(Waterbody))))
    assert c.execute("select count(*) from user").fetchone()[0] == 1
    assert c.execute("select version_num from alembic_version").fetchone()[0]  # migrations travel with the data
    backup()  # running twice the same day replaces the file instead of failing
    assert len(list(out.glob("holdover-*.db"))) == 1


@sqlite_only
def test_only_the_last_seven_backups_are_kept(session, tmp_path, monkeypatch):
    out = _use_data_dir(tmp_path, monkeypatch)
    out.mkdir(parents=True)
    for d in range(1, 10):
        (out / f"holdover-2025010{d}.db").write_text("old")
    backup()
    names = sorted(f.name for f in out.glob("holdover-*.db"))
    assert len(names) == 7 and names[-1] == f"holdover-{date.today():%Y%m%d}.db"
    assert "holdover-20250101.db" not in names and "holdover-20250102.db" not in names and "holdover-20250103.db" not in names


def test_backup_does_nothing_on_a_non_sqlite_database(tmp_path, monkeypatch):
    out = _use_data_dir(tmp_path, monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://nobody@localhost/none")
    get_settings.cache_clear()
    backup()  # must not try to connect; use pg_dump for Postgres
    assert not out.exists()
    get_settings.cache_clear()
