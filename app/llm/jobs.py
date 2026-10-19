import logging

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.llm.client import LLMClient, LLMUnavailable
from app.llm.extract import extract_report, extracted, rematch_items
from app.models import Report

log = logging.getLogger("holdover.llm")


def process_pending(session: Session, llm: LLMClient | None = None) -> dict:
    """Extract items from every report that hasn't been done yet, Willamette first. If the LLM
    host is down nothing is lost: reports stay pending and the next run retries."""
    llm = llm or LLMClient.for_extraction()
    out = {"extracted": 0, "pending": 0, "llm": "ok", "errors": 0}
    if not llm.configured:
        out["llm"] = "not_configured"
    reports = session.scalars(select(Report).order_by(
        case((Report.zone == "willamette", 0), else_=1), Report.issued_on.desc(), Report.id.desc())).all()
    for r in reports:
        if out["llm"] != "ok":
            out["pending"] += not extracted(session, r.id)
            continue
        try:
            if not extracted(session, r.id):
                extract_report(session, r, llm)
                out["extracted"] += 1
        except LLMUnavailable as exc:
            log.warning("LLM unavailable: %s", exc)
            out["llm"] = "unreachable"
            out["pending"] += 1
        except ValueError as exc:
            log.warning("LLM output rejected for report %s: %s", r.id, exc)
            out["errors"] += 1
            out["pending"] += 1
    out["rematched"] = rematch_items(session)
    return out
