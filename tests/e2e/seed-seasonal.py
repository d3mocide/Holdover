"""Explicitly synthetic seasonal baselines; refuses personal databases. Run on a disposable river fixture."""
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import json

path = Path(sys.argv[1]).resolve()
if not path.is_file() or not path.is_relative_to('/tmp') or not path.relative_to('/tmp').parts[0].startswith('holdover-'):
    raise SystemExit('Refusing: expected a disposable /tmp/holdover-... database')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ['DATABASE_URL'] = f'sqlite:///{path}'
os.environ['RUN_SCHEDULER'] = 'false'
from app.config import Settings
Settings.model_config['env_file'] = None
from app.db import session_factory
from app.http import now_iso
from app.models import Gauge, FlowBaseline
from app.seasonal import build_baseline
from sqlalchemy import select

end = date.today().year - 1
day = date(end - 9, 1, 1)
values = {}
while day.year <= end:
    values[day.isoformat()] = 50 + (day.year - end + 9) * 10 + day.month
    day += timedelta(days=1)
payload = json.dumps(build_baseline(values, end - 9, end))
with session_factory()() as session:
    for gauge in session.scalars(select(Gauge)):
        if session.get(FlowBaseline, gauge.id) is None:
            session.add(FlowBaseline(gauge_id=gauge.id, payload_json=payload, fetched_at=now_iso(), attempted_at=now_iso()))
    session.commit()
print('Synthetic seasonal baselines added only to disposable fixture')
