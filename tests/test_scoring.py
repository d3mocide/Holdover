from datetime import date

import pytest

from app import scoring as s

DAY = date(2026, 10, 17)  # Saturday; week of Oct 12


def test_stocking_recency_and_size():
    this = s.stocking_factor([("2026-10-12", 1000)], DAY, 1000, 0.3)
    last = s.stocking_factor([("2026-10-05", 1000)], DAY, 1000, 0.3)
    old = s.stocking_factor([("2026-09-14", 1000)], DAY, 1000, 0.3)
    small = s.stocking_factor([("2026-10-12", 100)], DAY, 1000, 0.3)
    assert this.value == 1.0 and last.value == 0.75 and old.value == pytest.approx(0.25)
    assert small.value < this.value
    assert this.value > last.value > old.value


def test_stocking_edge_cases():
    assert s.stocking_factor([], DAY, 1000, 0.3).value is None  # no stocking
    assert s.stocking_factor([("2026-10-19", 900)], DAY, 1000, 0.3).value is None  # only future weeks
    assert s.stocking_factor([("2026-10-12", 0)], DAY, 1000, 0.3).value is None
    assert s.stocking_factor([("2026-10-12", 500)], DAY, 0, 0.3).value is not None  # zone range unknown


def test_report_factor_decay_and_missing():
    assert s.report_factor("excellent", "2026-10-16", DAY, 0.25).value == 1.0
    assert s.report_factor("excellent", "2026-10-05", DAY, 0.25).value == 0.7
    assert s.report_factor("good", "2026-09-01", DAY, 0.25).value is None
    assert s.report_factor("unknown", "2026-10-16", DAY, 0.25).value is None
    assert s.report_factor(None, None, DAY, 0.25).value is None


def test_flow_factor():
    hist = [1000.0 + i for i in range(48)]
    near = s.flow_factor(1024, hist, 0.2, 168)
    blown = s.flow_factor(3000, hist, 0.2, 168)
    assert near.value > 0.95 and blown.value == 0.0
    assert s.flow_factor(None, hist, 0.2, 168).value is None  # no gauge
    assert s.flow_factor(1000, hist[:5], 0.2, 168).value is None  # too few points
    assert s.flow_factor(1000, hist, 0.2, 6).value is None  # dense but only 6 hours: no baseline
    assert s.flow_factor(5, [0.0] * 40, 0.2, 168).value is None


def test_forecast_factor():
    nice = s.forecast_factor(65, 5, 4, 0.15)
    bad = s.forecast_factor(30, 90, 25, 0.15)
    assert nice.value > 0.9 > 0.3 > bad.value
    assert s.forecast_factor(None, None, None, 0.15).value is None  # missing forecast
    assert s.forecast_factor(65, None, None, 0.15).value == 1.0  # partial data still scores


def test_distance_factor():
    assert s.distance_factor(0, 0.1).value == 1.0
    assert s.distance_factor(240, 0.1).value == 0.0
    assert s.distance_factor(None, 0.1).value is None
    assert s.haversine_km(44.05, -123.06, 44.05, -123.06) == 0
    assert 100 < s.haversine_km(44.05, -123.06, 45.5, -122.67) < 180


def test_combine_is_explainable():
    fs = [s.Factor("a", 1.0, 0.3, ""), s.Factor("b", 0.5, 0.2, ""), s.Factor("c", None, 0.5, "")]
    score, coverage = s.combine(fs)
    assert score == 65.0 and coverage == 0.5  # c has no data: neutral 0.5 -> (0.3 + 0.1 + 0.25) / 1.0
    assert [f.contribution for f in fs] == [30.0, 10.0, 25.0]
    assert sum(f.contribution for f in fs) == pytest.approx(score)  # breakdown adds up to the score


def test_not_applicable_is_dropped_and_weights_renormalised():
    fs = [s.Factor("a", 1.0, 0.3, ""), s.Factor("home", None, 0.7, "", applicable=False)]
    assert s.combine(fs) == (100.0, 1.0)
    assert fs[1].contribution == 0.0


def test_little_evidence_stays_near_neutral():
    one_input = [s.Factor("fc", 1.0, 0.15, "")] + [s.Factor(n, None, w, "") for n, w in
                                                      (("stock", .3), ("rep", .25), ("flow", .2), ("dist", .1))]
    score, coverage = s.combine(one_input)
    assert coverage == 0.15 and 50 < score < 60  # one perfect factor can't make a confident 79


def test_combine_nothing_applicable():
    assert s.combine([s.Factor("a", None, 0.3, "", applicable=False)]) == (0.0, 0.0)
    assert s.combine([]) == (0.0, 0.0)
    assert s.combine([s.Factor("a", None, 0.3, "")]) == (50.0, 0.0)  # applicable, no data: neutral
