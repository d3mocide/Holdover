"""Synthetic chart observations for the disposable river browser fixture, never production data.

Usage: .venv/bin/python tests/e2e/seed-river-history.py /tmp/holdover-.../data/e2e.db
Run after setup.sh gear. Existing rows are never overwritten.
"""
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timedelta, timezone

path = Path(sys.argv[1]).resolve()
temp = Path(tempfile.gettempdir()).resolve()
if not path.is_file() or not path.is_relative_to(temp) or not path.relative_to(temp).parts[0].startswith("holdover-"):
    raise SystemExit("Refusing: expected an existing disposable /tmp/holdover-... database")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["DATABASE_URL"] = f"sqlite:///{path}"
os.environ["RUN_SCHEDULER"] = "false"

from sqlalchemy import select
from app.config import Settings
Settings.model_config["env_file"] = None
from app.db import session_factory
from app.models import GaugeReading, Waterbody, WaterbodyGauge

with session_factory()() as session:
    river = session.scalar(select(Waterbody).where(Waterbody.name == "Tualatin River"))
    gauge_id = session.scalar(select(WaterbodyGauge.gauge_id).where(WaterbodyGauge.waterbody_id == river.id))
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    for i in range(220):
        timestamp = (now - timedelta(minutes=15 * i)).isoformat()
        for parameter, value in (("discharge_cfs", 100 + i), ("water_temp_c", 10 + i / 100)):
            if session.get(GaugeReading, (gauge_id, parameter, timestamp)) is None:
                session.add(GaugeReading(gauge_id=gauge_id, parameter=parameter, value=value, observed_at=timestamp))
    session.commit()
print("Synthetic Tualatin history added to the disposable fixture only")
