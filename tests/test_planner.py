import json
from datetime import date

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.llm.client import LLMClient
from app.llm.explain import generate_explanations, guard
from app.models import Generation, Report, ReportItem, Waterbody
from app.packlist import pack_list
from app.planner import FISHERIES, rank, template_text, wind_mph
from app.seed import seed_waterbodies
from app.sources import nws, odfw_report, usgs
from app.sources.odfw_stocking import ingest_page
from conftest import FIX, usgs_fetch

TODAY = date(2026, 10, 17)


def load(session, with_weather=False):
    seed_waterbodies(session)
    ingest_page(session, "u", 200, (FIX / "odfw_stocking" / "wv_p0.html").read_bytes())
    ingest_page(session, "u2", 200, (FIX / "odfw_stocking" / "wv_p1.html").read_bytes())
    usgs.run_job(session, usgs_fetch())
    odfw_report.ingest(session, odfw_report.URL, 200, (FIX / "odfw_report" / "index.html").read_bytes())
    if with_weather:
        wb = session.scalar(select(Waterbody).where(Waterbody.name == "Alton Baker Canal"))
        nws.refresh(session, wb, lambda u: (200, (FIX / "nws" / ("points.json" if "/points/" in u else "hourly.json" if u.endswith("hourly") else "forecast.json")).read_bytes()))


def accept(session, name, rating, species, sentence="s"):
    r = session.scalar(select(Report).where(Report.zone == "willamette"))
    wb = session.scalar(select(Waterbody).where(Waterbody.name == name))
    session.add(ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw=name, species=species, rating=rating,
                           note="n", source_sentence=sentence, status="accepted"))
    session.commit()


def test_trout_ranking_has_breakdown_that_adds_up(session):
    load(session)
    spots = rank(session, TODAY, "trout")
    assert spots and all(s.wb.lat is not None for s in spots)
    for sp in spots:
        assert sum(f.contribution for f in sp.factors) == pytest.approx(sp.score, abs=0.3)
        assert 0 <= sp.score <= 100 and 0 <= sp.coverage <= 1
    assert [s.score for s in spots] == sorted((s.score for s in spots), reverse=True)
    top = spots[0]
    assert top.factors[0].name == "stocking" and top.factors[0].value is not None


def test_this_week_beats_old_stocking(session):
    load(session)
    scores = {s.wb.name: s for s in rank(session, TODAY, "trout")}
    this_week = next(s for s in scores.values() if s.factors[0].detail.endswith("(this week)"))
    older = next(s for s in scores.values() if "wk before" in s.factors[0].detail and s.factors[0].value < 0.4)
    assert this_week.score > older.score


def test_missing_data_is_neutral_and_unconfigured_is_dropped(session):
    load(session)
    sp = rank(session, TODAY, "trout")[0]
    names = {f.name: f for f in sp.factors}
    assert names["forecast"].value is None and names["forecast"].contribution > 0  # no data: neutral, not zero
    assert names["distance"].applicable is False and names["distance"].contribution == 0  # no HOME_LAT: dropped
    assert sp.coverage < 1.0  # and the UI can say so


def test_forecast_and_report_move_the_score(session):
    load(session, with_weather=True)
    accept(session, "Alton Baker Canal", "excellent", "rainbow trout")
    sp = next(s for s in rank(session, TODAY, "trout") if s.wb.name == "Alton Baker Canal")
    f = {x.name: x for x in sp.factors}
    assert f["report"].value == 1.0 and f["forecast"].value is not None


def test_fisheries_from_hints_and_reports(session):
    load(session)
    steel = {s.wb.name for s in rank(session, TODAY, "steelhead")}
    assert "Santiam River, North Fork" in steel
    warm = {s.wb.name for s in rank(session, TODAY, "warmwater")}
    assert "Henry Hagg Lake" in warm and "Santiam River, North Fork" not in warm
    accept(session, "Detroit Reservoir", "good", "smallmouth bass")
    assert "Detroit Reservoir" in {s.wb.name for s in rank(session, TODAY, "warmwater")}


def test_flow_factor_uses_gauge_history(session):
    load(session)
    sp = next(s for s in rank(session, TODAY, "steelhead") if s.wb.name == "Santiam River, North Fork")
    flow = next(f for f in sp.factors if f.name == "flow")
    assert flow.value is None  # fixture has only 6 h of readings: not enough history, so excluded, not guessed


def test_empty_date_far_future_has_no_trout_spots(session):
    load(session)
    assert rank(session, date(2031, 1, 1), "trout") == []


def test_api_spots(session):
    from app.main import app
    load(session)
    c = TestClient(app)
    r = c.get("/api/spots?date=2026-10-17&fishery=trout").json()
    assert r["spots"][0]["rank"] == 1 and r["spots"][0]["explanation"]["source"] == "template"
    assert set(r["spots"][0]["factors"][0]) == {"name", "value", "weight", "points", "detail", "applicable"}
    assert "\n" in r["spots"][0]["explanation"]["text"] and "regulation" in r["note"]
    assert c.get("/api/spots?fishery=sharks").status_code == 422
    assert c.get("/api/spots?fishery=steelhead").status_code == 200


def llm_with(handler):
    return LLMClient("http://llm.test/v1", "m", transport=httpx.MockTransport(handler))


def reply(text):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"text": text})}}]})


def test_guard_rejects_new_numbers_places_species():
    src = "Stocked: 750 fish, week of Oct 12 (this week).\nlight: 07:28-18:21"
    assert guard("Stocked with 750 fish this week.", src) == []
    assert "5000" in guard("About 5000 fish went in.", src)
    assert "Detroit" in guard("Try Detroit instead.", src)
    assert "steelhead" in guard("Steelhead may also be around.", src)
    assert "bass" in guard("Bass are active", src)


def test_explanations_cached_when_grounded_and_template_otherwise(session):
    from app.main import app
    load(session)
    top = rank(session, TODAY, "trout")[0]

    def good(req):
        facts = json.loads(req.content)["messages"][1]["content"]
        line = next(l for l in facts.splitlines() if l.startswith(("stocking:", "daylight:")))
        return reply(f"Fish went in recently. {line.split(': ', 1)[1]}")  # only restates a provided fact

    out = generate_explanations(session, llm_with(good), TODAY, "trout", limit=3)
    assert out["generated"] == 3 and out["rejected"] == 0
    r = TestClient(app).get("/api/spots?date=2026-10-17&fishery=trout").json()["spots"]
    assert r[0]["explanation"]["source"] == "llm" and r[0]["explanation"]["as_of"]

    def bad(req):
        return reply("There are 9999 giant steelhead here and Detroit is better.")

    session.query(Generation).delete()
    session.commit()
    out = generate_explanations(session, llm_with(bad), TODAY, "trout", limit=3)
    assert out["rejected"] == 3 and out["generated"] == 0
    r = TestClient(app).get("/api/spots?date=2026-10-17&fishery=trout").json()["spots"]
    assert r[0]["explanation"]["source"] == "template"  # LLM text never reaches the user


def test_llm_down_falls_back_cleanly(session):
    load(session)

    def down(req):
        raise httpx.ConnectError("refused")

    assert generate_explanations(session, llm_with(down), TODAY, "trout")["llm"] == "unreachable"
    assert generate_explanations(session, LLMClient("", ""), TODAY, "trout")["llm"] == "not_configured"


def test_wind_parse():
    assert wind_mph("5 mph") == 5 and wind_mph("0 to 7 mph") == 7 and wind_mph(None) is None


def test_pack_list_rules():
    rainy = pack_list(date(2026, 11, 2), "steelhead", 44, 70, 18, "river")
    ids = {i["id"] for i in rainy["items"]}
    assert {"rain", "waders", "pfd", "wind", "layers", "thermos", "rod-drift", "license"} <= ids
    hot = pack_list(date(2026, 7, 20), "warmwater", 90, 0, 5, "lake")
    hids = {i["id"] for i in hot["items"]}
    assert {"sun", "bug", "pol"} <= hids and "rain" not in hids and "waders" not in hids
    none = pack_list(date(2026, 10, 17), "trout", None, None, None, "pond")
    assert "No forecast is cached" in none["intro"] and "rain" in {i["id"] for i in none["items"]}
    assert not any("limit" in i["label"].lower() for i in rainy["items"])  # gear, not rules


def test_day_bundle_has_pack_list(session, monkeypatch):
    from app.main import app
    import app.api.conditions as api_cond
    load(session)
    monkeypatch.setattr(api_cond, "quick_fetch", lambda u: (None, b""))
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Alton Baker Canal"))
    d = TestClient(app).get(f"/api/day/{wb.id}?fishery=trout").json()
    assert d["pack"]["items"] and d["pack"]["intro_source"] == "template"
