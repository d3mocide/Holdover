import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.llm.client import LLMClient, LLMUnavailable
from app.llm.extract import extract_report, match_waterbody
from app.llm.jobs import process_pending
from app.llm.grounding import ungrounded_terms
from app.models import Generation, Report, ReportItem, Waterbody
from app.seed import seed_waterbodies
from app.sources.odfw_report import ParseError, ingest, parse, report_text
from conftest import FIX

URL = "https://example.test/recreation-report"
AUTH = {}
HTML = (FIX / "odfw_report" / "index.html").read_bytes()


def llm_with(handler) -> LLMClient:
    return LLMClient("http://llm.test/v1", "m", transport=httpx.MockTransport(handler))


def reply(obj):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(obj)}}]})


def willamette(session):
    seed_waterbodies(session)
    ingest(session, URL, 200, HTML)
    return session.scalar(select(Report).where(Report.zone == "willamette"))


def test_parse_real_report():
    p = parse(HTML)
    assert p.issued_on == "2026-10-16"
    assert set(p.zones) == {"nw", "willamette", "central", "ne", "se"}
    assert len(p.zones["willamette"]) == 2 and "North Santiam" in p.zone_text("willamette")


def test_layout_change_is_parse_error():
    with pytest.raises(ParseError):
        parse(b"<html><body>nothing</body></html>")


def test_ingest_one_report_per_zone_and_hash_skip(session):
    seed_waterbodies(session)
    assert len(ingest(session, URL, 200, HTML)) == 5
    assert ingest(session, URL, 200, HTML) == []  # identical body: parse skipped
    assert session.scalar(select(func.count()).select_from(Report)) == 5


def test_waterbody_matching_is_exact_not_loose(session):
    seed_waterbodies(session)
    assert match_waterbody(session, "North Santiam") is not None
    assert match_waterbody(session, "Dexter Reservoir") is not None
    assert match_waterbody(session, "Willamette River") is None  # not the Coast Fork
    assert match_waterbody(session, "Imaginary Lake") is None


def test_hallucinated_sentence_is_rejected(session):
    r = willamette(session)
    text = report_text(session, r)
    real = text.split(". ")[0] + "."
    llm = llm_with(lambda req: reply({"items": [
        {"waterbody_raw": "North Santiam", "species": ["coho"], "rating": "good", "note": "n", "source_sentence": real},
        {"waterbody_raw": "Fake Lake", "species": ["trout"], "rating": "excellent", "note": "n",
         "source_sentence": "Fake Lake is stuffed with trout."},
    ]}))
    assert extract_report(session, r, llm) == {"kept": 1, "rejected": 1}
    items = {i.waterbody_raw: i for i in session.scalars(select(ReportItem))}
    assert items["North Santiam"].status == "review" and items["North Santiam"].waterbody_id
    assert items["Fake Lake"].status == "rejected" and items["Fake Lake"].waterbody_id is None
    # idempotent
    assert extract_report(session, r, llm) == {"skipped": True}
    assert session.scalar(select(func.count()).select_from(ReportItem)) == 2


def test_invalid_model_output_is_rejected_whole(session):
    r = willamette(session)
    for bad in [{"items": [{"waterbody_raw": "x"}]}, {"items": [{"waterbody_raw": "", "source_sentence": "y"}]}]:  # missing or empty required fields
        with pytest.raises(ValueError):
            extract_report(session, r, llm_with(lambda req, b=bad: reply(b)))
    bad_json = llm_with(lambda req: httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]}))
    with pytest.raises(ValueError):
        extract_report(session, r, bad_json)
    assert session.scalar(select(func.count()).select_from(ReportItem)) == 0


def test_llm_down_leaves_everything_pending_then_recovers(session):
    willamette(session)

    def down(req):
        raise httpx.ConnectError("refused")

    out = process_pending(session, llm_with(down))
    assert out["llm"] == "unreachable" and out["pending"] >= 1 and out["extracted"] == 0
    assert session.scalar(select(func.count()).select_from(Generation)) == 0

    def ok(req):
        return reply({"items": []})

    out = process_pending(session, llm_with(ok))
    assert out["llm"] == "ok" and out["extracted"] == 5 and out["pending"] == 0


def test_unconfigured_llm_is_not_an_error(session):
    willamette(session)
    out = process_pending(session, LLMClient("", ""))
    assert out["llm"] == "not_configured"
    with pytest.raises(LLMUnavailable):
        LLMClient("", "").chat_json("s", "u", __import__("app.llm.schemas", fromlist=["x"]).TextResult)


def test_grounding_guard():
    src = "- North Santiam (coho; rating good): Coho moving in. [Coho salmon are moving into the lower North Santiam.]"
    assert ungrounded_terms("Coho are moving into the North Santiam.", src) == []
    assert "40" in ungrounded_terms("About 40 coho were caught.", src)
    assert "Detroit" in ungrounded_terms("Fishing is also good at Detroit.", src)


def test_api_serves_verbatim_bullets_without_llm(session):
    from app.main import app
    r = willamette(session)
    c = TestClient(app)
    body = c.get("/api/reports?zone=willamette").json()["report"]
    assert "digest" not in body and body["items"] == []
    assert body["bullets"][0].startswith("Coho salmon are moving into the lower parts of the North Santiam")
    assert body["source_url"] == "https://myodfw.com/recreation-report" and body["issued_on"] == "2026-10-16"


def test_review_queue_accept_reject_and_map_effect(session):
    from app.main import app
    r = willamette(session)
    session.add_all([
        ReportItem(report_id=r.id, waterbody_raw="North Santiam", waterbody_id=None, rating="good", species="coho",
                   note="n", source_sentence="s1", status="review"),
        ReportItem(report_id=r.id, waterbody_raw="Junk", rating="unknown", note="n", source_sentence="s2", status="review"),
    ])
    session.commit()
    from conftest import anonymous_client, signed_in_client
    assert anonymous_client().get("/api/admin/review/items").status_code == 401
    c = signed_in_client("boss", admin=True)
    q = c.get("/api/admin/review/items", headers=AUTH).json()
    assert len(q) == 2
    wb = match_waterbody(session, "North Santiam")
    assert c.post(f"/api/admin/review/items/{q[0]['id']}/accept", json={"waterbody_id": wb}, headers=AUTH).status_code == 200
    assert c.post(f"/api/admin/review/items/{q[1]['id']}/reject", headers=AUTH).status_code == 200
    sheet = c.get(f"/api/waterbodies/{wb}").json()
    assert [i["source_sentence"] for i in sheet["report_items"]] == ["s1"]
    assert c.get("/api/reports?zone=willamette").json()["report"]["items"][0]["rating"] == "good"


def test_a_bare_list_from_a_server_that_ignores_the_schema_is_wrapped_and_still_validated():
    item = {"waterbody_raw": "Detroit Lake", "species": ["rainbow trout"], "rating": "good", "note": "", "source_sentence": "Fishing was good."}
    out = llm_with(lambda r: reply([item])).chat_json("s", "u", __import__("app.llm.schemas", fromlist=["x"]).ExtractionResult)
    assert out.items[0].waterbody_raw == "Detroit Lake"
    bad = dict(item, source_sentence="")  # an invalid item is still rejected after wrapping
    with pytest.raises(ValueError):
        llm_with(lambda r: reply([bad])).chat_json("s", "u", __import__("app.llm.schemas", fromlist=["x"]).ExtractionResult)


def test_a_single_species_string_is_accepted_as_a_list():
    from app.llm.schemas import ExtractedItem
    base = {"waterbody_raw": "Detroit Lake", "rating": "good", "source_sentence": "Fishing was good."}
    assert ExtractedItem(**base, species="coho").species == ["coho"]
    assert ExtractedItem(**base, species=["coho", "steelhead"]).species == ["coho", "steelhead"]
    with pytest.raises(ValueError):
        ExtractedItem(**base, species=5)


def test_status_line_says_what_is_wrong():
    def server(models):
        return llm_with(lambda r: httpx.Response(200, json={"data": [{"id": m} for m in models]}) if r.url.path.endswith("/models") else httpx.Response(404))
    ok = server(["gemma4-e4b"])
    ok.model = "gemma4-e4b"
    assert "is available" in ok.status_line()
    wrong = server(["gemma4-e4b", "other"])
    wrong.model = "openai/gemma4-e4b"
    line = wrong.status_line()
    assert "does not list model 'openai/gemma4-e4b'" in line and "gemma4-e4b, other" in line and "no provider prefix" in line
    assert "not configured" in LLMClient("", "").status_line()
    down = LLMClient("http://llm.test/v1", "m", transport=httpx.MockTransport(lambda r: httpx.Response(500)))
    assert "did not answer GET /models" in down.status_line()


def test_answer_in_a_reasoning_field_is_read_when_content_is_empty():
    from app.llm.schemas import TextResult
    for field in ("reasoning", "reasoning_content"):
        body = {"choices": [{"message": {"role": "assistant", "content": "", field: json.dumps({"text": "Coho are moving up the North Santiam."})}}]}
        out = llm_with(lambda r, b=body: httpx.Response(200, json=b)).chat_json("s", "u", TextResult)
        assert out.text.startswith("Coho are moving")
    plain = {"choices": [{"message": {"content": json.dumps({"text": "From content."}), "reasoning": "thinking..."}}]}
    assert llm_with(lambda r: httpx.Response(200, json=plain)).chat_json("s", "u", TextResult).text == "From content."  # content wins


def test_an_unknown_rating_word_becomes_unknown_instead_of_rejecting_the_report():
    from app.llm.schemas import ExtractedItem
    base = {"waterbody_raw": "Detroit Lake", "source_sentence": "Fishing was great."}
    assert ExtractedItem(**base, rating="great").rating == "unknown"
    assert ExtractedItem(**base, rating="Good ").rating == "good"
    assert ExtractedItem(**base).rating == "unknown"


def test_the_request_timeout_comes_from_settings_unless_given(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_TIMEOUT", "900")
    get_settings.cache_clear()
    try:
        assert LLMClient("http://x/v1", "m")._http.timeout.read == 900
        assert LLMClient("http://x/v1", "m", timeout=5)._http.timeout.read == 5
    finally:
        get_settings.cache_clear()


def test_all_reports_serves_every_zone_verbatim_with_no_llm(session):
    from app.main import app
    willamette(session)
    d = TestClient(app).get("/api/reports/all").json()
    assert d["issued_on"] == "2026-10-16" and d["available"] == ["2026-10-16"]
    keys = [z["zone"] for z in d["zones"]]
    assert keys[0] == "willamette" and set(keys) == {"willamette", "nw", "central", "ne", "se"}
    assert all(z["bullets"] and z["label"] for z in d["zones"])
    assert d["zones"][0]["bullets"][0].startswith("Coho salmon are moving into the lower parts of the North Santiam")
    assert d["source_url"] == "https://myodfw.com/recreation-report" and d["fetched_at"]


def test_all_reports_unknown_date_and_empty_database_are_empty_not_errors(session):
    from app.main import app
    c = TestClient(app)
    assert c.get("/api/reports/all").json() == {"issued_on": None, "available": [], "source_url": "https://myodfw.com/recreation-report", "fetched_at": None, "zones": []}
    willamette(session)
    d = c.get("/api/reports/all", params={"issued_on": "2020-01-01"}).json()
    assert d["zones"] == [] and d["available"] == ["2026-10-16"]


def test_extraction_can_use_its_own_model_and_a_longer_timeout(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_BASE_URL", "http://x/v1")
    monkeypatch.setenv("LLM_MODEL", "fast")
    monkeypatch.setenv("LLM_TIMEOUT", "60")
    monkeypatch.setenv("LLM_EXTRACT_MODEL", "slow-and-strong")
    monkeypatch.setenv("LLM_EXTRACT_TIMEOUT", "1500")
    get_settings.cache_clear()
    try:
        usual, extract = LLMClient(), LLMClient.for_extraction()
        assert (usual.model, usual._http.timeout.read) == ("fast", 60)
        assert (extract.model, extract._http.timeout.read) == ("slow-and-strong", 1500)
        monkeypatch.delenv("LLM_EXTRACT_MODEL")
        get_settings.cache_clear()
        assert LLMClient.for_extraction().model == "fast"  # unset: same model as everything else
    finally:
        get_settings.cache_clear()


def test_the_map_shows_unreviewed_ai_ratings_flagged_and_accepted_ones_win_a_tie(session):
    from app.main import app
    r = willamette(session)
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Dexter Reservoir"))
    other = session.scalar(select(Waterbody).where(Waterbody.name == "Detroit Reservoir"))
    session.add_all([
        ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="Dexter", species="trout", rating="good", note="n", source_sentence="s1", status="review"),
        ReportItem(report_id=r.id, waterbody_id=other.id, waterbody_raw="Detroit", species="kokanee", rating="fair", note="n", source_sentence="s2", status="review"),
        ReportItem(report_id=r.id, waterbody_id=other.id, waterbody_raw="Detroit", species="kokanee", rating="excellent", note="n", source_sentence="s3", status="accepted"),
        ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="x", species="y", rating="excellent", note="n", source_sentence="s4", status="rejected"),
    ])
    session.commit()
    feats = {f["properties"]["name"]: f["properties"] for f in TestClient(app).get("/api/map?layers=stocking,reports").json()["features"] if f["properties"]["layer"] == "report"}
    assert feats["Dexter Reservoir"]["rating"] == "good" and feats["Dexter Reservoir"]["reviewed"] is False  # rejected never shows
    assert feats["Detroit Reservoir"]["rating"] == "excellent" and feats["Detroit Reservoir"]["reviewed"] is True  # accepted beats review


def test_unknown_ratings_are_not_drawn_and_unreviewed_items_never_move_a_score(session):
    from datetime import date

    from app.main import app
    from app.planner import _report_inputs
    r = willamette(session)
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Dexter Reservoir"))
    session.add(ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="Dexter", species="trout", rating="unknown", note="n", source_sentence="s", status="review"))
    session.add(ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="Dexter", species="trout", rating="excellent", note="n", source_sentence="s", status="review"))
    session.commit()
    names = {f["properties"]["name"] for f in TestClient(app).get("/api/map?layers=stocking,reports").json()["features"] if f["properties"]["layer"] == "report"}
    assert names == {"Dexter Reservoir"}  # drawn once, from the excellent one; the unknown one draws nothing
    assert _report_inputs(session, wb.id)[0] is None  # nothing accepted: the ranking ignores the model's reading
    body = TestClient(app).get(f"/api/waterbodies/{wb.id}").json()
    assert [i["reviewed"] for i in body["report_items"]] == [False, False]


def test_an_unreviewed_reading_from_another_zones_report_never_reaches_the_map_or_the_sheet(session):
    from app.main import app
    willamette(session)
    central = session.scalar(select(Report).where(Report.zone == "central"))
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Fall Creek Reservoir"))  # a Willamette-zone water
    session.add(ReportItem(report_id=central.id, waterbody_id=wb.id, waterbody_raw="Fall River", species="trout", rating="excellent",
                           note="n", source_sentence="s", status="review"))
    session.commit()
    c = TestClient(app)
    drawn = {f["properties"]["name"] for f in c.get("/api/map?layers=stocking,reports").json()["features"] if f["properties"]["layer"] == "report"}
    assert "Fall Creek Reservoir" not in drawn and c.get(f"/api/waterbodies/{wb.id}").json()["report_items"] == []
    session.query(ReportItem).update({ReportItem.status: "accepted"})  # a person decided it: now it shows
    session.commit()
    assert "Fall Creek Reservoir" in {f["properties"]["name"] for f in c.get("/api/map?layers=stocking,reports").json()["features"] if f["properties"]["layer"] == "report"}


def test_report_items_match_only_inside_their_own_zone_and_late_matches_are_picked_up(session):
    from app.llm.extract import rematch_items
    seed_waterbodies(session)
    ingest(session, URL, 200, HTML)
    # "Fall River" is a Central-zone water; "Fall Creek ..." is Willamette's. Across all zones the key is ambiguous, inside a zone it is not.
    assert match_waterbody(session, "Fall River") is None
    central = match_waterbody(session, "Fall River", "central")
    assert central is not None and session.get(Waterbody, central).name == "Fall River"
    assert match_waterbody(session, "Fall River", "central") != match_waterbody(session, "Fall River", "willamette")  # each zone resolves on its own
    rep = session.scalar(select(Report).where(Report.zone == "central"))
    session.add(ReportItem(report_id=rep.id, waterbody_id=None, waterbody_raw="Fall River", species="trout", rating="excellent", note="n", source_sentence="s", status="review"))
    session.add(ReportItem(report_id=rep.id, waterbody_id=None, waterbody_raw="Fall River", species="trout", rating="good", note="n", source_sentence="s2", status="rejected"))
    session.commit()
    assert rematch_items(session) == 1
    items = session.scalars(select(ReportItem).order_by(ReportItem.id)).all()
    assert items[0].waterbody_id == central and items[1].waterbody_id is None  # the rejected one is left alone


def test_rematching_corrects_an_old_cross_zone_match_but_never_touches_accepted_items(session):
    from app.llm.extract import rematch_items
    seed_waterbodies(session)
    ingest(session, URL, 200, HTML)
    nw = session.scalar(select(Report).where(Report.zone == "central"))  # a Central item that was once matched to a Willamette water
    willamette_wb = session.scalar(select(Waterbody).where(Waterbody.name == "Fall Creek Reservoir"))
    mistaken = ReportItem(report_id=nw.id, waterbody_id=willamette_wb.id, waterbody_raw="Fall River", species="trout", rating="excellent", note="n", source_sentence="s", status="review")
    decided = ReportItem(report_id=nw.id, waterbody_id=willamette_wb.id, waterbody_raw="Fall River", species="trout", rating="good", note="n", source_sentence="s2", status="accepted")
    session.add_all([mistaken, decided])
    session.commit()
    assert rematch_items(session) == 1
    assert session.get(Waterbody, mistaken.waterbody_id).name == "Fall River" and decided.waterbody_id == willamette_wb.id
    assert rematch_items(session) == 0  # nothing left to change


def test_re_extracting_replaces_unreviewed_items_but_keeps_what_a_person_decided(session):
    r = willamette(session)
    wb = session.scalar(select(Waterbody).where(Waterbody.name == "Dexter Reservoir"))
    session.add_all([
        ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="old", species="x", rating="good", note="n", source_sentence="Coho salmon are moving into the lower parts of the North Santiam.", status="review"),
        ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="kept", species="x", rating="good", note="n", source_sentence="a", status="accepted"),
        ReportItem(report_id=r.id, waterbody_id=wb.id, waterbody_raw="dismissed", species="x", rating="slow", note="n", source_sentence="b", status="rejected"),
    ])
    session.commit()
    extract_report(session, r, llm_with(lambda req: reply({"items": []})))
    assert sorted(i.waterbody_raw for i in session.scalars(select(ReportItem))) == ["dismissed", "kept"]  # the unreviewed "old" one is gone
