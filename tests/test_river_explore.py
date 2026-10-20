from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.conditions import latest_gauge
from app.models import Gauge, GaugeReading, Waterbody
from app.planner import rank
from app.seed import seed_waterbodies


def test_rivers_are_public_map_features_without_stocking(session):
    from app.main import app
    seed_waterbodies(session)
    c = TestClient(app)
    rivers = c.get('/api/map?layers=rivers&zone=willamette').json()['features']
    river = next(f for f in rivers if f['properties']['name'] == 'Clackamas River')
    assert river['properties']['layer'] == 'river'
    assert session.get(Waterbody, river['properties']['id']).kind == 'river'
    assert c.get(f"/api/waterbodies/{river['properties']['id']}").json()['stocking'] == []
    assert not any(f['properties']['name'] == 'Clackamas River' for f in c.get('/api/map?layers=rivers&zone=central').json()['features'])
    unpinned = session.scalar(select(Waterbody).where(Waterbody.name == 'East Lake'))
    waters = c.get('/api/waterbodies').json()
    assert next(w for w in waters if w['id'] == unpinned.id)['zone'] == 'central'
    assert next(w for w in waters if w['id'] == unpinned.id)['lat'] is None


def test_each_sensor_has_its_own_freshness(session):
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == '14150000'))
    now = datetime.now(timezone.utc)
    session.add_all([
        GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=100, observed_at=(now-timedelta(days=1)).isoformat()),
        GaugeReading(gauge_id=g.id, parameter='water_temp_c', value=10, observed_at=now.isoformat()),
    ])
    session.commit()
    d = latest_gauge(session, g)
    assert d['stale'] and d['values']['discharge_cfs']['stale']
    assert not d['values']['water_temp_f']['stale']
    assert d['values']['water_temp_f']['value'] == 50
    assert d['as_of'] == d['values']['discharge_cfs']['observed_at']
    assert d['trend'] is None


def test_gauge_history_is_bounded_public_and_uses_observation_times(session):
    from app.main import app
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == '14150000'))
    now = datetime.now(timezone.utc)
    for hours in [1, 26, 200]:
        for param, value in [('discharge_cfs', 100), ('water_temp_c', 10)]:
            session.add(GaugeReading(gauge_id=g.id, parameter=param, value=value,
                                    observed_at=(now-timedelta(hours=hours)).isoformat(), provisional=1))
    session.commit()
    c = TestClient(app)
    full = c.get(f'/api/gauges/{g.id}/history').json()
    assert len(full['series']['discharge_cfs']['points']) == 2
    assert full['series']['water_temp_c']['points'][0]['value'] == 50
    day = c.get(f'/api/gauges/{g.id}/history?hours=24').json()
    assert len(day['series']['discharge_cfs']['points']) == 1
    assert day['series']['discharge_cfs']['points'][0]['provisional']
    assert c.get(f'/api/gauges/{g.id}/history?hours=999999').status_code == 422
    assert c.get('/api/gauges/999999/history').status_code == 404


def test_stale_flow_does_not_count_as_ranking_evidence(session):
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == '14183000'))
    now = datetime.now(timezone.utc)
    for i in range(220):
        session.add(GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=100,
                                observed_at=(now-timedelta(hours=8, minutes=15*i)).isoformat()))
    session.commit()
    def flow():
        spot = next(s for s in rank(session, now.date(), 'steelhead') if s.wb.name == 'Santiam River, North Fork')
        return next(f for f in spot.factors if f.name == 'flow')
    assert flow().value is None
    session.add(GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=100, observed_at=now.isoformat()))
    session.commit()
    assert flow().value is not None


def test_public_rankings_expose_only_source_timed_comparison_inputs(session):
    from app.main import app
    seed_waterbodies(session)
    g = session.scalar(select(Gauge).where(Gauge.site_no == '14183000'))
    now = datetime.now(timezone.utc)
    stamp = (now - timedelta(minutes=10)).isoformat()
    session.add_all([
        GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=123, observed_at=stamp),
        GaugeReading(gauge_id=g.id, parameter='discharge_cfs', value=999, observed_at=(now + timedelta(hours=1)).isoformat()),
    ])
    session.commit()
    c = TestClient(app)
    spot = next(s for s in c.get('/api/spots?fishery=steelhead').json()['spots']
                if s['waterbody']['name'] == 'Santiam River, North Fork')
    context = spot['journal_context']
    assert set(context) == {'gauges', 'weather', 'weather_as_of', 'date'}
    assert context['gauges'] == [{'site_no': g.site_no, 'values': {
        'discharge_cfs': {'value': 123, 'observed_at': stamp}}, 'provisional': True}]
    assert spot['score'] == next(s.score for s in rank(session, now.date(), 'steelhead')
                                  if s.wb.name == 'Santiam River, North Fork')
    reading = session.scalar(select(GaugeReading).where(GaugeReading.observed_at == stamp))
    reading.observed_at = (now - timedelta(hours=8)).isoformat()
    session.commit()
    spot = next(s for s in c.get('/api/spots?fishery=steelhead').json()['spots']
                if s['waterbody']['name'] == 'Santiam River, North Fork')
    assert spot['journal_context']['gauges'] == []
