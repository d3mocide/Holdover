"""Writing the briefing paragraphs: grounded text is kept with its facts; ungrounded text is retried once, then dropped; no LLM, no problem."""
import json
from datetime import date

import httpx
from conftest import FIX
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.briefing import build, monday
from app.llm.briefing import generate, stored
from app.llm.client import LLMClient
from app.models import Generation
from app.seed import seed_waterbodies
from app.sources.odfw_report import ingest as ingest_report
from app.sources.odfw_stocking import ingest_page

TODAY = date.today()


def loaded(session, stocking_html):
    seed_waterbodies(session)
    ingest_page(session, "https://example.test/stocking?page=0", 200, stocking_html)
    ingest_report(session, "https://example.test/recreation-report", 200, (FIX / "odfw_report" / "index.html").read_bytes())


def llm_with(handler):
    return LLMClient("http://llm.test/v1", "slow-and-strong", transport=httpx.MockTransport(handler))


def reply(text):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"text": text})}}]})


def sections(session):
    return {s.key: s for s in build(session, TODAY)}


def test_grounded_paragraphs_are_stored_with_the_facts_they_came_from(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    # the fixture schedule is for October 2026: pin the briefing to that week
    import app.llm.briefing as lb
    monkeypatch.setattr(lb, "build", lambda s, t=None, z="willamette": __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14)))
    out = generate(session, llm_with(lambda r: reply("Alton Baker Canal gets 750 legals this week.")), date(2026, 10, 14))
    assert out["llm"] == "ok" and out["written"] >= 1
    kept = stored(session, monday(date(2026, 10, 14)))
    assert "stocking" in kept and kept["stocking"]["model"] == "slow-and-strong" and kept["stocking"]["facts"][0].startswith("This week")
    assert "report" not in kept and "alerts" not in kept  # ODFW's words and alerts are never narrated


def test_an_ungrounded_paragraph_gets_one_retry_then_the_better_text_is_kept(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    import app.llm.briefing as lb
    monkeypatch.setattr(lb, "build", lambda s, t=None, z="willamette": [x for x in __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14)) if x.key == "stocking"])
    calls = []

    def handler(req):
        body = json.loads(req.content)
        calls.append(body["messages"][-1]["content"])
        return reply("About 9,999 fish go into Detroit Lake." if len(calls) == 1 else "Alton Baker Canal gets 750 legals this week.")

    out = generate(session, llm_with(handler), date(2026, 10, 14))
    assert len(calls) == 2 and "not in the facts" in calls[1] and out["written"] == 1 and out["rejected"] == 0
    assert "9,999" not in stored(session, monday(date(2026, 10, 14)))["stocking"]["text"]


def test_text_that_never_grounds_is_dropped_and_nothing_is_stored(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    import app.llm.briefing as lb
    monkeypatch.setattr(lb, "build", lambda s, t=None, z="willamette": [x for x in __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14)) if x.key == "stocking"])
    out = generate(session, llm_with(lambda r: reply("Expect 42 coho at Detroit Lake.")), date(2026, 10, 14))
    assert out["written"] == 0 and out["rejected"] == 1
    assert session.scalar(select(func.count()).select_from(Generation).where(Generation.kind == "briefing")) == 0


def test_regenerating_replaces_the_paragraph(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    import app.llm.briefing as lb
    monkeypatch.setattr(lb, "build", lambda s, t=None, z="willamette": [x for x in __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14)) if x.key == "stocking"])
    generate(session, llm_with(lambda r: reply("Alton Baker Canal gets 750 legals.")), date(2026, 10, 14))
    generate(session, llm_with(lambda r: reply("Canby Pond gets 300 legals.")), date(2026, 10, 14))
    assert session.scalar(select(func.count()).select_from(Generation).where(Generation.kind == "briefing")) == 1
    assert stored(session, monday(date(2026, 10, 14)))["stocking"]["text"].startswith("Canby Pond")


def test_no_llm_or_a_down_llm_is_not_an_error(session, stocking_html):
    loaded(session, stocking_html)
    assert generate(session, LLMClient("", ""), date(2026, 10, 14)) == {"written": 0, "rejected": 0, "llm": "not_configured"}

    def down(req):
        raise httpx.ConnectError("refused")

    out = generate(session, llm_with(down), date(2026, 10, 14))
    assert out["llm"] == "unreachable" and out["written"] == 0


def test_the_api_serves_facts_alone_and_then_the_paragraph_with_its_facts(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    import app.api.briefing as ab
    import app.llm.briefing as lb
    pinned = lambda s, t=None, z="willamette": __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14))
    monkeypatch.setattr(lb, "build", pinned)
    monkeypatch.setattr(ab, "build", pinned)

    class D(date):
        @classmethod
        def today(cls):
            return date(2026, 10, 14)

    monkeypatch.setattr(ab, "date", D)
    from app.main import app
    c = TestClient(app)
    before = c.get("/api/briefing").json()
    assert before["week_of"] == "2026-10-12"
    stock = next(s for s in before["sections"] if s["key"] == "stocking")
    assert stock["text"] is None and not stock["narrated"] and stock["facts"]
    generate(session, llm_with(lambda r: reply("Alton Baker Canal gets 750 legals this week.")), date(2026, 10, 14))
    after = c.get("/api/briefing").json()
    stock = next(s for s in after["sections"] if s["key"] == "stocking")
    assert stock["narrated"] and stock["text"].startswith("Alton Baker Canal") and stock["model"] == "slow-and-strong" and stock["as_of"]
    report = next(s for s in after["sections"] if s["key"] == "report")
    assert not report["narrated"] and report["text"] is None and report["facts"][0].startswith("Coho salmon")
    assert "does not state regulations" in after["note"]


def test_a_sections_editorial_hint_reaches_the_model_but_is_not_a_fact(session, stocking_html, monkeypatch):
    loaded(session, stocking_html)
    import app.llm.briefing as lb
    monkeypatch.setattr(lb, "build", lambda s, t=None, z="willamette": [x for x in __import__("app.briefing", fromlist=["x"]).build(s, date(2026, 10, 14)) if x.key == "stocking"])
    seen = []

    def handler(req):
        seen.append(json.loads(req.content)["messages"][-1]["content"])
        return reply("Alton Baker Canal gets 750 legals this week.")

    generate(session, llm_with(handler), date(2026, 10, 14))
    assert "Say which week is the biggest" in seen[0] and seen[0].index("Say which week") < seen[0].index("Facts:")
    assert "Say which week" not in " ".join(stored(session, monday(date(2026, 10, 14)))["stocking"]["facts"])
