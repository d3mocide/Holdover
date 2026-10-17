import os
from pathlib import Path

import pytest

os.environ.setdefault("RUN_SCHEDULER", "false")
os.environ.setdefault("HOLDOVER_TOKEN", "testtoken")

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def session(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config

    url = f"sqlite:///{tmp_path/'t.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    from app import db
    from app.config import get_settings

    get_settings.cache_clear()
    db._engine = db._Session = None
    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with db.session_factory()() as s:
        yield s
    db._engine = db._Session = None
    get_settings.cache_clear()


@pytest.fixture
def stocking_html():
    return (FIX / "odfw_stocking" / "wv_p0.html").read_bytes()
