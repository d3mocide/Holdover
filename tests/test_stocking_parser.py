from datetime import date

import pytest

from app.freshness import freshness
from app.normalize import normalize_alias
from app.sources.odfw_stocking import ParseError, parse, parse_week_start


def test_parse_fixture(stocking_html):
    rows = parse(stocking_html)
    assert len(rows) == 50
    r = rows[0]
    assert r.week_of == "2026-09-14" and r.waterbody_raw == "ESTACADA LK" and r.total == 1334
    assert all(date.fromisoformat(x.week_of).weekday() == 0 for x in rows)  # Mondays
    assert all(x.total == x.legals + x.trophy + x.brood + x.fingerling for x in rows)


@pytest.mark.parametrize("text", [
    "Oct. 12, 2026 - Oct. 16, 2026", "Sep. 14, 2026-Sep. 18, 2026", "May. 17, 2027-May. 22, 2027",
])
def test_week_text_variants(text):
    assert parse_week_start(text).year in (2026, 2027)


def test_layout_change_is_an_error_not_empty():
    with pytest.raises(ParseError):
        parse(b"<html><body><p>redesigned</p></body></html>")


def test_unexpected_columns():
    html = "<table class='views-table'><tr><th>Foo</th></tr></table>"
    with pytest.raises(ParseError):
        parse(html)


def test_normalize():
    assert normalize_alias("SANTIAM R, N FK-2") == "SANTIAM RIVER NORTH FORK"
    assert normalize_alias("DEXTER RES") == "DEXTER RESERVOIR"
    assert normalize_alias("MCKENZIE R-1 (below Leaburg Dam)") != normalize_alias("MCKENZIE R-2 (above Leaburg Dam)")


def test_freshness_buckets():
    today = date(2026, 10, 17)  # Saturday; week starts Mon 10-12
    assert freshness("2026-10-12", today) == "this_week"
    assert freshness("2026-10-05", today) == "recent"
    assert freshness("2026-09-28", today) == "recent"
    assert freshness("2026-09-21", today) == "older"
    assert freshness("2026-10-19", today) == "upcoming"
