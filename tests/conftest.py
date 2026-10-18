import os
from pathlib import Path

import pytest

os.environ.setdefault("RUN_SCHEDULER", "false")

# Tests must never pick up a developer's local .env (HOME_LAT, USER_AGENT, ...).
from app.config import Settings  # noqa: E402

Settings.model_config["env_file"] = None

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


@pytest.fixture(autouse=True)
def _reset_login_throttle():
    from app import security
    security.by_user.hits.clear()
    security.by_ip.hits.clear()


PASSWORD = "correct-horse-battery"


def signed_in_client(username="angler", admin=False):
    """A TestClient signed in as a real (created-on-demand) account, sending the CSRF header like the web app does."""
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from app import db
    from app.main import app
    from app.models import User
    from app.security import hash_password

    with db.session_factory()() as s:
        if s.scalar(select(User).where(User.username == username)) is None:
            s.add(User(username=username, password_hash=hash_password(PASSWORD), is_admin=int(admin),
                       created_at="2026-10-17T00:00:00+00:00"))
            s.commit()
    c = TestClient(app)
    c.headers["X-Holdover"] = "1"
    r = c.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return c


def anonymous_client():
    from fastapi.testclient import TestClient

    from app.main import app
    c = TestClient(app)
    c.headers["X-Holdover"] = "1"
    return c
