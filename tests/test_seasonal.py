import copy
import json
from datetime import date, datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select

from app import seasonal
from app.http import now_iso
from app.models import FlowBaseline, Gauge, GaugeReading, RawFetch, Waterbody, WaterbodyGauge
from app.sources import usgs_daily as daily
from app.sources.usgs import ParseError
from conftest import FIX


def values(start=2016, end=2025):
    out = {}
    day = date(start, 1, 1)
    while day.year <= end:
        out[day.isoformat()] = (day.year - start + 1) * 10
        day += timedelta(days=1)
    return out


def gauge(session):
    g = Gauge(site_no='14207500', agency='USGS', name='Synthetic seasonal test gauge', lat=45, lon=-123)
    session.add(g); session.commit()
    return g


def test_saved_live_daily_fixture_and_approval_unit_quality_guards():
    body = (FIX / 'usgs_daily/daily.json').read_bytes()
    rows = daily.parse(body, '14207500', 2016, 2025)
    assert len(rows) == 3 and rows['2025-10-03'] == 379
    payload = json.loads(body)
    original = payload['features'][0]
    for patch in [{'approval_status': 'Provisional'}, {'value': 'NaN'}, {'value': '-999999'}, {'value': 'ice'},
                  {'qualifier': ['ice']}, {'time': 'wrong'}, {'statistic_id': '00001'}, {'monitoring_location_id': 'USGS-other'}]:
        f = copy.deepcopy(original); f['properties'].update(patch)
        assert daily.parse(json.dumps({'type': 'FeatureCollection', 'features': [f]}), '14207500', 2016, 2025) == {}
    f = copy.deepcopy(original); f['properties']['unit_of_measure'] = 'm3/s'
    with pytest.raises(ParseError): daily.parse(json.dumps({'type': 'FeatureCollection', 'features': [f]}), '14207500', 2016, 2025)
    with pytest.raises(ParseError): daily.parse(b'{"type":"FeatureCollection","features":[null]}', '14207500', 2016, 2025)


def test_baseline_percentiles_samples_leap_day_and_circular_year_window():
    result = seasonal.build_baseline(values(), 2016, 2025)
    normal = result['points']['10-20']
    assert normal == {'samples': 150, 'expected': 150, 'years': list(range(2016, 2026)), 'p25': 30, 'median': 55, 'p75': 80}
    assert result['points']['02-29']['samples'] == result['points']['02-29']['expected'] == 143
    assert result['points']['01-01']['samples'] == result['points']['12-31']['samples'] == 150
    assert result['approved_days'] == 3653 and len(result['points']) == 366
    sparse = seasonal.build_baseline(values(2022, 2025), 2016, 2025)['points']['10-20']
    assert sparse['samples'] == 60 and sparse['median'] is None
    zeros = {k: 0 for k in values()}
    assert seasonal.build_baseline(zeros, 2016, 2025)['points']['10-20']['median'] == 0


def test_raw_precedes_parsing_and_failed_or_empty_refresh_keeps_last_good(session, monkeypatch):
    g = gauge(session); body = (FIX / 'usgs_daily/daily.json').read_bytes(); original = daily.parse
    def checked(body, *args):
        raw = session.scalar(select(RawFetch).order_by(RawFetch.id.desc()))
        assert raw.body == body and raw.parse_ok is None
        return original(body, *args)
    monkeypatch.setattr(daily, 'parse', checked)
    assert daily.refresh(session, g, lambda u: (200, body), date(2026, 10, 20))['ok']
    cache = session.get(FlowBaseline, g.id); good = cache.payload_json; stamp = cache.fetched_at
    for status, bad in [(503, b'busy'), (200, b'{}'), (200, b'{"type":"FeatureCollection","features":[]}')]:
        assert not daily.refresh(session, g, lambda u: (status, bad), date(2026, 10, 20))['ok']
        assert cache.payload_json == good and cache.fetched_at == stamp and cache.error
        assert session.scalar(select(RawFetch).order_by(RawFetch.id.desc())).parse_ok == 0
    assert seasonal.for_gauge(session, g, date(2026, 10, 20))['stale']


def test_partial_pagination_and_external_next_links_never_publish_a_partial_baseline(session):
    g = gauge(session); payload = json.loads((FIX / 'usgs_daily/daily.json').read_bytes())
    payload['links'] = [{'rel': 'next', 'href': 'https://outside.invalid/daily'}]
    called = []
    assert not daily.refresh(session, g, lambda u: (called.append(u) or 200, json.dumps(payload).encode()), date(2026, 10, 20))['ok']
    assert len(called) == 1 and session.get(FlowBaseline, g.id).payload_json is None
    payload['links'] = [{'rel': 'next', 'href': daily.url_for(g.site_no, 2016, 2025) + '&offset=10000'}]
    def partial(url):
        return (503, b'busy') if 'offset' in url else (200, json.dumps(payload).encode())
    assert not daily.refresh(session, g, partial, date(2026, 10, 20))['ok']
    assert session.get(FlowBaseline, g.id).payload_json is None
    payload['links'] = []; payload['numberMatched'] = 4000
    assert not daily.refresh(session, g, lambda u: (200, json.dumps(payload).encode()), date(2026, 10, 20))['ok']
    assert session.get(FlowBaseline, g.id).payload_json is None


def test_background_job_is_key_gated_bounded_and_does_not_refetch_recently(session, monkeypatch):
    from app.scheduler import source_status
    assert 'USGS_API_KEY' in daily.run_job(session)['skipped']
    assert source_status()['usgs_daily']['disabled'] and not source_status()['usgs_daily']['stale']
    assert session.scalar(select(RawFetch)) is None
    g = gauge(session)
    w = Waterbody(name='Synthetic river', kind='river', zone='willamette', lat=45, lon=-123)
    session.add(w); session.flush(); session.add(WaterbodyGauge(waterbody_id=w.id, gauge_id=g.id)); session.commit()
    called = []
    def fetch(url):
        called.append(url)
        return 200, b'{"type":"FeatureCollection","features":[]}'
    assert daily.run_job(session, fetch)['ok'] and len(called) == 1
    assert 'skipped' in daily.run_job(session, fetch) and len(called) == 1


def test_current_instantaneous_vs_daily_baseline_and_no_comparison_when_stale(session):
    g = gauge(session); now = datetime.now(timezone.utc)
    payload = seasonal.build_baseline(values(now.year - 10, now.year - 1), now.year - 10, now.year - 1)
    cache = FlowBaseline(gauge_id=g.id, payload_json=json.dumps(payload), fetched_at=now_iso(), attempted_at=now_iso())
    session.add(cache)
    session.add(GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=200, observed_at=(now-timedelta(minutes=10)).isoformat()))
    session.add(GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=999, observed_at=(now+timedelta(days=1)).isoformat()))
    session.commit()
    result = seasonal.for_gauge(session, g, now.date()+timedelta(days=3))
    assert result['current']['value'] == 200 and result['current']['position'] == 'above the middle 50%'
    assert len(result['series']) == 61 and result['date'] != result['current']['date']
    cache.error = 'upstream failed'; session.commit()
    result = seasonal.for_gauge(session, g, now.date())
    assert result['stale'] and result['current']['position'] is None
    cache.error = None
    reading = session.scalar(select(GaugeReading).where(GaugeReading.value == 200))
    reading.observed_at = (now-timedelta(hours=4)).isoformat(); session.commit()
    assert seasonal.for_gauge(session, g, now.date())['current']['stale']
    assert seasonal.for_gauge(session, g, now.date())['current']['position'] is None


def test_public_api_disabled_state_invalid_gauges_and_date_edges(session):
    from app.main import app
    g = gauge(session); client = TestClient(app)
    assert client.get(f'/api/gauges/{g.id}/seasonal').json()['status'] == 'disabled'
    assert client.get('/api/gauges/999999/seasonal').status_code == 404
    assert client.get(f'/api/gauges/{g.id}/seasonal?date=bad').status_code == 422
    session.add(FlowBaseline(gauge_id=g.id, payload_json=json.dumps(seasonal.build_baseline(values(), 2016, 2025)), fetched_at=now_iso(), attempted_at=now_iso()))
    session.commit()
    assert client.get(f'/api/gauges/{g.id}/seasonal?date=0001-01-01').status_code == 200
    assert client.get(f'/api/gauges/{g.id}/seasonal?date=9999-12-31').status_code == 200


def test_key_is_header_only_and_never_in_raw_url(monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'usgs_api_key', 'synthetic-test-key')
    def get(url, **kwargs):
        assert kwargs['headers']['X-Api-Key'] == 'synthetic-test-key'
        assert kwargs['follow_redirects'] is False  # never forward the key to a redirect target
        assert 'synthetic-test-key' not in url
        return httpx.Response(200, content=b'{}')
    monkeypatch.setattr(httpx, 'get', get)
    assert daily.fetch_daily(daily.url_for('14207500', 2016, 2025)) == (200, b'{}')


def test_additive_migration_downgrade_preserves_existing_tables(session):
    from alembic import command
    from alembic.config import Config
    from app.db import get_engine
    config = Config('alembic.ini'); config.set_main_option('sqlalchemy.url', session.bind.url.render_as_string(hide_password=False))
    session.close()
    command.downgrade(config, '0009')
    assert 'flow_baseline' not in inspect(get_engine()).get_table_names()
    assert 'trip' in inspect(get_engine()).get_table_names()
    command.upgrade(config, 'head')
    assert 'flow_baseline' in inspect(get_engine()).get_table_names()


def test_upgrade_from_060_preserves_personal_rows_and_manual_pin(session):
    from alembic import command
    from alembic.config import Config
    from app.models import Catch, Favorite, GearItem, GearSetup, Pin, Trip, User, UserSession
    from app.seed import seed_waterbodies

    config = Config('alembic.ini')
    config.set_main_option('sqlalchemy.url', session.bind.url.render_as_string(hide_password=False))
    session.close()
    command.downgrade(config, '0008')  # production 0.6.0 schema
    seed_waterbodies(session)
    water = session.scalar(select(Waterbody).where(Waterbody.name == 'Henry Hagg Lake'))
    water.lat, water.lon = 45.0, -123.0  # explicitly synthetic owner-edited pin
    stamp = now_iso()
    owner = User(username='upgrade-test', password_hash='synthetic-hash', created_at=stamp)
    session.add(owner); session.flush()
    session.add(GearItem(uuid='upgrade-lure', owner_id=owner.id, kind='lure', name='Synthetic lure', updated_at=stamp))
    session.add(GearSetup(uuid='upgrade-setup', owner_id=owner.id, name='Synthetic setup', item_uuids_json='["upgrade-lure"]', updated_at=stamp))
    session.add(Trip(uuid='upgrade-trip', owner_id=owner.id, waterbody_id=water.id, notes='Keep this journal', setup_uuid='upgrade-setup', updated_at=stamp))
    session.flush()
    session.add_all([
        Catch(uuid='upgrade-catch', owner_id=owner.id, trip_uuid='upgrade-trip', count=1, photo_path='synthetic-photo.jpg', updated_at=stamp),
        Pin(uuid='upgrade-pin', owner_id=owner.id, label='Synthetic private pin', lat=45, lon=-123, updated_at=stamp),
        Favorite(user_id=owner.id, waterbody_id=water.id),
        UserSession(token_hash='synthetic-session', user_id=owner.id, created_at=stamp, last_used_at=stamp, expires_at='2099-01-01T00:00:00+00:00'),
    ])
    session.commit()
    tables = [User, UserSession, Trip, Catch, Pin, GearItem, GearSetup, Favorite, Waterbody]
    def snapshot():
        return {model.__tablename__: [dict(row) for row in session.execute(select(model.__table__)).mappings()] for model in tables}
    before = snapshot()
    session.close()
    command.upgrade(config, 'head')
    seed_waterbodies(session)  # the same migrate + seed sequence used by the image
    assert snapshot() == before
    assert 'flow_baseline' in inspect(session.bind).get_table_names()
    assert session.scalar(select(FlowBaseline)) is None  # no invented historical data
